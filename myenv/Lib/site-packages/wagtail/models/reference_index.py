import uuid

from django.contrib.contenttypes.fields import GenericForeignKey, GenericRel
from django.contrib.contenttypes.models import ContentType
from django.db import connection, models
from django.utils.functional import cached_property
from django.utils.text import capfirst
from django.utils.translation import gettext_lazy as _
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel, get_all_child_relations
from taggit.models import ItemBase

from wagtail.blocks import StreamBlock
from wagtail.fields import StreamField


class ReferenceGroups:
    """
    Groups records in a ReferenceIndex queryset by their source object.

    Args:
        qs: (QuerySet[ReferenceIndex]) A QuerySet on the ReferenceIndex model

    Yields:
        A tuple (source_object, references) for each source object that appears
        in the queryset. source_object is the model instance of the source object
        and references is a list of references that occur in the QuerySet from
        that source object.
    """

    def __init__(self, qs):
        self.qs = qs.order_by("base_content_type", "object_id")

    def __iter__(self):
        reference_fk = None
        references = []
        for reference in self.qs:
            if reference_fk != (reference.base_content_type_id, reference.object_id):
                if reference_fk is not None:
                    content_type = ContentType.objects.get_for_id(reference_fk[0])
                    object = content_type.get_object_for_this_type(pk=reference_fk[1])
                    yield object, references
                    references = []

                reference_fk = (reference.base_content_type_id, reference.object_id)

            references.append(reference)

        if references:
            content_type = ContentType.objects.get_for_id(reference_fk[0])
            object = content_type.get_object_for_this_type(pk=reference_fk[1])
            yield object, references

    def __len__(self):
        return self._count

    @cached_property
    def _count(self):
        return self.qs.values("base_content_type", "object_id").distinct().count()

    @cached_property
    def is_protected(self):
        return any(reference.on_delete == models.PROTECT for reference in self.qs)

    def count(self):
        """
        Returns the number of rows that will be returned by iterating this
        ReferenceGroups.

        Just calls len(self) internally, this method only exists to allow
        instances of this class to be used in a Paginator.
        """
        return len(self)

    def __getitem__(self, key):
        return list(self)[key]


class ReferenceIndexQuerySet(models.QuerySet):
    def group_by_source_object(self):
        """
        Returns a ReferenceGroups object for this queryset that will yield
        references grouped by their source instance.
        """
        return ReferenceGroups(self)


class ReferenceIndex(models.Model):
    """
    Records references between objects for quick retrieval of object usage.

    References are extracted from Foreign Keys, Chooser Blocks in StreamFields, and links in Rich Text Fields.
    This index allows us to efficiently find all of the references to a particular object from all of these sources.
    """

    # The object where the reference was extracted from

    # content_type represents the content type of the model that contains
    # the field where the reference came from. If the model sub-classes another
    # concrete model (such as Page), that concrete model will be set in
    # base_content_type, otherwise it would be the same as content_type
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, related_name="+"
    )
    base_content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, related_name="+"
    )
    object_id = models.CharField(
        max_length=255,
        verbose_name=_("object id"),
    )

    # The object that has been referenced
    # to_content_type is always the base content type of the referenced object
    to_content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, related_name="+"
    )
    to_object_id = models.CharField(
        max_length=255,
        verbose_name=_("object id"),
    )

    # The model_path is the path to the field on content_type where the reference was extracted from.
    # the content_path is the path to a specific block on the instance where the reference is extracted from.

    # These are dotted path, always starting with a field or child relation name. If
    # the reference was extracted from an inline panel or streamfield, other components
    # of the path can be used to locate where the reference was extracted.
    #
    # For example, say we have a StreamField called 'body' which has a struct block type
    # called 'my_struct_block' that has a field called 'my_field'. If we extracted a
    # reference from that field, the model_path would be set to the following:
    #
    # 'body.my_struct_block.my_field'
    #
    # The content path would follow the same format, but anything repeatable would be replaced by an ID.
    # For example:
    #
    # 'body.bdc70d8b-e7a2-4c2a-bf43-2a3e3fcbbe86.my_field'
    #
    # We can use the model_path with the 'content_type' to find the original definition of
    # the field block and display information to the user about where the reference was
    # extracted from.
    #
    # We can use the content_path to link the user directly to the block/field that contains
    # the reference.
    model_path = models.TextField()
    content_path = models.TextField()

    # We need a separate hash field for content_path in order to use it in a unique key because
    # MySQL has a limit to the size of fields that are included in unique keys
    content_path_hash = models.UUIDField()

    objects = ReferenceIndexQuerySet.as_manager()

    wagtail_reference_index_ignore = True

    # The set of models that should have signals attached to watch for outbound references.
    # This includes those registered with `register_model`, as well as their child models
    # linked by a ParentalKey.
    tracked_models = set()

    # The set of models that can appear as the 'from' object in the reference index.
    # This only includes those registered with `register_model`, and NOT child models linked
    # by ParentalKey (object references on those are recorded under the parent).
    indexed_models = set()

    class Meta:
        unique_together = [
            (
                "base_content_type",
                "object_id",
                "to_content_type",
                "to_object_id",
                "content_path_hash",
            )
        ]

    @classmethod
    def _get_base_content_type(cls, model_or_object):
        """
        Returns the ContentType record that represents the base model of the
        given model or object.

        For a model that uses multi-table-inheritance, this returns the model
        that contains the primary key. For example, for any page object, this
        will return the content type of the Page model.
        """
        parents = model_or_object._meta.get_parent_list()
        if parents:
            return ContentType.objects.get_for_model(
                parents[-1], for_concrete_model=False
            )
        else:
            return ContentType.objects.get_for_model(
                model_or_object, for_concrete_model=False
            )

    @classmethod
    def model_is_indexable(cls, model, allow_child_models=False):
        """
        Returns True if the given model may have outbound references that we would be interested in recording in the index.


        Args:
            model (type): a Django model class
            allow_child_models (boolean): Child models are not indexable on their own. If you are looking at
                                          a child model from the perspective of indexing it through its parent,
                                          set this to True to disable checking for this. Default False.
        """
        if getattr(model, "wagtail_reference_index_ignore", False):
            return False

        # Don't check any models that have a parental key, references from these will be collected from the parent
        if not allow_child_models and any(
            isinstance(field, ParentalKey) for field in model._meta.get_fields()
        ):
            return False

        for field in model._meta.get_fields():
            if field.is_relation and field.many_to_one:
                if getattr(field, "wagtail_reference_index_ignore", False):
                    continue

                if getattr(
                    field.related_model, "wagtail_reference_index_ignore", False
                ):
                    continue

                if isinstance(field, (ParentalKey, GenericRel)):
                    continue

                return True

            if hasattr(field, "extract_references"):
                return True

        if issubclass(model, ClusterableModel):
            for child_relation in get_all_child_relations(model):
                if cls.model_is_indexable(
                    child_relation.related_model,
                    allow_child_models=True,
                ):
                    return True

        return False

    @classmethod
    def register_model(cls, model):
        """
        Registers the model for indexing.
        """
        if model in cls.indexed_models:
            return

        if cls.model_is_indexable(model):
            cls.indexed_models.add(model)
            cls._register_as_tracked_model(model)

    @classmethod
    def _register_as_tracked_model(cls, model):
        """
        Add the model and all of its ParentalKey-linked children to the set of
        models to be tracked by signal handlers.
        """
        if model in cls.tracked_models:
            return

        from wagtail.signal_handlers import (
            connect_reference_index_signal_handlers_for_model,
        )

        cls.tracked_models.add(model)
        connect_reference_index_signal_handlers_for_model(model)

        for child_relation in get_all_child_relations(model):
            if cls.model_is_indexable(
                child_relation.related_model,
                allow_child_models=True,
            ):
                cls._register_as_tracked_model(child_relation.related_model)

    @classmethod
    def is_indexed(cls, model):
        return model in cls.indexed_models

    @classmethod
    def _extract_references_from_object(cls, object):
        """
        Generator that scans the given object and yields any references it finds.

        Args:
            object (Model): an instance of a Django model to scan for references

        Yields:
            A tuple (content_type_id, object_id, model_path, content_path) for each
            reference found.

            content_type_id (int): The ID of the ContentType record representing
                                   the model of the referenced object

            object_id (str): The primary key of the referenced object, converted
                             to a string

            model_path (str): The path to the field on the model of the source
                              object where the reference was found

            content_path (str): The path to the piece of content on the source
                                object instance where the reference was found
        """
        # Extract references from fields
        for field in object._meta.get_fields():
            if field.is_relation and field.many_to_one:
                if getattr(field, "wagtail_reference_index_ignore", False):
                    continue

                if getattr(
                    field.related_model, "wagtail_reference_index_ignore", False
                ):
                    continue

                if isinstance(field, (ParentalKey, GenericRel)):
                    continue

                if isinstance(field, GenericForeignKey):
                    ct_field = object._meta.get_field(field.ct_field)
                    fk_field = object._meta.get_field(field.fk_field)
                    ct_value = ct_field.value_from_object(object)
                    fk_value = fk_field.value_from_object(object)

                    if ct_value is not None and fk_value is not None:
                        # The content type ID referenced by the GenericForeignKey might be a subclassed
                        # model, but the reference index requires us to index it under the base model's
                        # content type, as that's what will be used for lookups. So, we need to convert
                        # the content type back to a model class so that _get_base_content_type can
                        # select the appropriate superclass if necessary, before converting back to a
                        # content type.
                        model = ContentType.objects.get_for_id(ct_value).model_class()
                        yield (
                            cls._get_base_content_type(model).id,
                            str(fk_value),
                            field.name,
                            field.name,
                        )

                    continue

                if isinstance(field, GenericRel):
                    continue

                value = field.value_from_object(object)
                if value is not None:
                    yield (
                        cls._get_base_content_type(field.related_model).id,
                        str(value),
                        field.name,
                        field.name,
                    )

            if hasattr(field, "extract_references"):
                value = field.value_from_object(object)
                if value is not None:
                    yield from (
                        (
                            cls._get_base_content_type(to_model).id,
                            to_object_id,
                            f"{field.name}.{model_path}",
                            f"{field.name}.{content_path}",
                        )
                        for to_model, to_object_id, model_path, content_path in field.extract_references(
                            value
                        )
                    )

        # Extract references from child relations
        if isinstance(object, ClusterableModel):
            for child_relation in get_all_child_relations(object):
                relation_name = child_relation.get_accessor_name()
                child_objects = getattr(object, relation_name).all()

                for child_object in child_objects:
                    yield from (
                        (
                            to_content_type_id,
                            to_object_id,
                            f"{relation_name}.item.{model_path}",
                            f"{relation_name}.{str(child_object.id)}.{content_path}",
                        )
                        for to_content_type_id, to_object_id, model_path, content_path in cls._extract_references_from_object(
                            child_object
                        )
                    )

    @classmethod
    def _get_content_path_hash(cls, content_path):
        """
        Returns a UUID for the given content path. Used to enforce uniqueness.

        Note: MySQL has a limit on the length of fields that are used in unique keys so
              we need a separate hash field to allow us to support long content paths.

        Args:
            content_path (str): The content path to get a hash for

        Returns:
            A UUID instance containing the hash of the given content path
        """
        return uuid.uuid5(
            uuid.UUID("bdc70d8b-e7a2-4c2a-bf43-2a3e3fcbbe86"), content_path
        )

    @classmethod
    def create_or_update_for_object(cls, object):
        """
        Creates or updates ReferenceIndex records for the given object.

        This method will extract any outbound references from the given object
        and insert/update them in the database.

        Note: This method must be called within a `django.db.transaction.atomic()` block.

        Args:
            object (Model): The model instance to create/update ReferenceIndex records for
        """
        # For the purpose of this method, a "reference record" is a tuple of
        # (to_content_type_id, to_object_id, model_path, content_path) - the properties that
        # uniquely define a reference

        # Extract new references and construct a set of reference records
        references = set(cls._extract_references_from_object(object))

        # Find content types for this model and all of its ancestor classes,
        # ordered from most to least specific
        content_types = [
            ContentType.objects.get_for_model(model_or_object, for_concrete_model=False)
            for model_or_object in ([object] + object._meta.get_parent_list())
        ]
        content_type = content_types[0]
        base_content_type = content_types[-1]
        known_content_type_ids = [ct.id for ct in content_types]

        # Find existing references in the database so we know what to add/delete.
        # Construct a dict mapping reference records to the (content_type_id, id) pair that the
        # existing database entry is found under
        existing_references = {
            (to_content_type_id, to_object_id, model_path, content_path): (
                content_type_id,
                id,
            )
            for id, content_type_id, to_content_type_id, to_object_id, model_path, content_path in cls.objects.filter(
                base_content_type=base_content_type, object_id=object.pk
            ).values_list(
                "id",
                "content_type_id",
                "to_content_type",
                "to_object_id",
                "model_path",
                "content_path",
            )
        }

        # Construct the set of reference records that have been found on the object but are not
        # already present in the database
        new_references = references - set(existing_references.keys())

        bulk_create_kwargs = {}
        if connection.features.supports_ignore_conflicts:
            bulk_create_kwargs["ignore_conflicts"] = True

        # Create database records for those reference records
        cls.objects.bulk_create(
            [
                cls(
                    content_type=content_type,
                    base_content_type=base_content_type,
                    object_id=object.pk,
                    to_content_type_id=to_content_type_id,
                    to_object_id=to_object_id,
                    model_path=model_path,
                    content_path=content_path,
                    content_path_hash=cls._get_content_path_hash(content_path),
                )
                for to_content_type_id, to_object_id, model_path, content_path in new_references
            ],
            **bulk_create_kwargs,
        )

        # Delete removed references
        deleted_reference_ids = []
        # Look at the reference record and the supporting content_type / id for each existing
        # reference in the database
        for reference_data, (content_type_id, id) in existing_references.items():
            if reference_data in references:
                # Do not delete this reference, as it is still present in the new set
                continue

            if content_type_id not in known_content_type_ids:
                # The content type for the existing record does not match the current model or any
                # superclass. We can infer that the existing record is for a more specific subclass
                # than the one we're currently indexing - e.g. we are indexing <Page id=123> while
                # the existing reference was recorded against <BlogPage id=123>. In this case, do
                # not treat the missing reference as a deletion - it likely still exists, but on a
                # relation which can only be seen on the more specific model.
                continue

            # If we reach here, this is a legitimate deletion - add it to the list of IDs to delete
            deleted_reference_ids.append(id)

        # Perform the deletion
        cls.objects.filter(id__in=deleted_reference_ids).delete()

    @classmethod
    def remove_for_object(cls, object):
        """
        Deletes all outbound references for the given object.

        Use this before deleting the object itself.

        Args:
            object (Model): The model instance to delete ReferenceIndex records for
        """
        base_content_type = cls._get_base_content_type(object)
        cls.objects.filter(
            base_content_type=base_content_type, object_id=object.pk
        ).delete()

    @classmethod
    def get_references_for_object(cls, object):
        """
        Returns all outbound references for the given object.

        Args:
            object (Model): The model instance to fetch ReferenceIndex records for

        Returns:
            A QuerySet of ReferenceIndex records
        """
        return cls.objects.filter(
            base_content_type_id=cls._get_base_content_type(object),
            object_id=object.pk,
        )

    @classmethod
    def get_references_to(cls, object):
        """
        Returns all inbound references for the given object.

        Args:
            object (Model): The model instance to fetch ReferenceIndex records for

        Returns:
            A QuerySet of ReferenceIndex records
        """
        return cls.objects.filter(
            to_content_type_id=cls._get_base_content_type(object),
            to_object_id=object.pk,
        )

    @classmethod
    def get_grouped_references_to(cls, object):
        """
        Returns all inbound references for the given object, grouped by the object
        they are found on.

        Args:
            object (Model): The model instance to fetch ReferenceIndex records for

        Returns:
            A ReferenceGroups object
        """
        return cls.get_references_to(object).group_by_source_object()

    @property
    def _content_type(self):
        # Accessing a ContentType from a ForeignKey does not make use of the
        # ContentType manager's cache, so we use this property to make use of
        # the cache.
        return ContentType.objects.get_for_id(self.content_type_id)

    @cached_property
    def model_name(self):
        """
        The model name of the object from which the reference was extracted.
        For most cases, this is also where the reference exists on the database
        (i.e. ``related_field_model_name``). However, for ClusterableModels, the
        reference is extracted from the parent model.

        Example:
        A relationship between a BlogPage, BlogPageGalleryImage, and Image
        is extracted from the BlogPage model, but the reference is stored on
        on the BlogPageGalleryImage model.
        """
        return self._content_type.name

    @cached_property
    def related_field_model_name(self):
        """
        The model name where the reference exists on the database.
        """
        return self.related_field.model._meta.verbose_name

    @cached_property
    def on_delete(self):
        try:
            return self.reverse_related_field.on_delete
        except AttributeError:
            # It might be a custom field/relation that doesn't have an on_delete attribute,
            # or other reference collected from extract_references(), e.g. StreamField.
            return models.SET_NULL

    @cached_property
    def source_field(self):
        """
        The field from which the reference was extracted.
        This may be a related field (e.g. ForeignKey), a reverse related field
        (e.g. ManyToOneRel), a StreamField, or any other field that defines
        extract_references().
        """
        model_path_components = self.model_path.split(".")
        field_name = model_path_components[0]
        field = self._content_type.model_class()._meta.get_field(field_name)
        return field

    @cached_property
    def related_field(self):
        # The field stored on the reference index can be a related field or a
        # reverse related field, depending on whether the reference was extracted
        # directly from a ForeignKey or through a parent ClusterableModel. This
        # property normalises to the related field.
        if isinstance(self.source_field, models.ForeignObjectRel):
            return self.source_field.remote_field
        return self.source_field

    @cached_property
    def reverse_related_field(self):
        # This property normalises to the reverse related field, which is where
        # the on_delete attribute is stored.
        return self.related_field.remote_field

    def describe_source_field(self):
        """
        Returns a string describing the field that this reference was extracted from.

        For StreamField, this returns the label of the block that contains the reference.
        For other fields, this returns the verbose name of the field.
        """
        field = self.source_field
        model_path_components = self.model_path.split(".")

        # ManyToOneRel (reverse accessor for ParentalKey) does not have a verbose name. So get the name of the child field instead
        if isinstance(field, models.ManyToOneRel):
            child_field = field.related_model._meta.get_field(model_path_components[2])
            return capfirst(child_field.verbose_name)
        elif isinstance(field, StreamField):
            label = f"{capfirst(field.verbose_name)}"
            block = field.stream_block
            block_idx = 1
            while isinstance(block, StreamBlock):
                block = block.child_blocks[model_path_components[block_idx]]
                block_label = capfirst(block.label)
                label += f" → {block_label}"
                block_idx += 1
            return label
        else:
            try:
                field_name = field.verbose_name
            except AttributeError:
                # generate verbose name from field name in the same way that Django does:
                # https://github.com/django/django/blob/7b94847e384b1a8c05a7d4c8778958c0290bdf9a/django/db/models/fields/__init__.py#L858
                field_name = field.name.replace("_", " ")
            return capfirst(field_name)

    def describe_on_delete(self):
        """
        Returns a string describing the action that will be taken when the referenced object is deleted.
        """
        if self.on_delete == models.CASCADE:
            return _("the %(model_name)s will also be deleted") % {
                "model_name": self.related_field_model_name,
            }
        if self.on_delete == models.PROTECT:
            return _("prevents deletion")
        if self.on_delete == models.SET_DEFAULT:
            return _("will be set to the default %(model_name)s") % {
                "model_name": self.related_field_model_name,
            }
        if self.on_delete == models.DO_NOTHING:
            return _("will do nothing")

        # It's technically possible to know whether RESTRICT will prevent the
        # deletion or not, but the only way to reliably do so is to use Django's
        # internal Collector class, which is not publicly documented.
        # It also uses its own logic to find the references in real-time, which
        # may be slower than our ReferenceIndex. For now, we'll just say that
        # RESTRICT *may* prevent deletion, but we do not add any safe guards
        # around the possible exception.
        if self.on_delete == models.RESTRICT:
            return _("may prevent deletion")

        # SET is a function that returns the actual callable used for on_delete,
        # so we need to check for it by inspecting the deconstruct() result.
        if (
            hasattr(self.on_delete, "deconstruct")
            and self.on_delete.deconstruct()[0] == "django.db.models.SET"
        ):
            return _("will be set to a %(model_name)s specified by the system") % {
                "model_name": self.related_field_model_name,
            }

        # It's either models.SET_NULL or a custom value, but we cannot be sure what
        # will happen with the latter, so assume that the reference will be unset.
        return _("will unset the reference")


# Ignore relations formed by any django-taggit 'through' model, as this causes any tag attached to
# a tagged object to appear as a reference to that object. Ideally we would follow the reference to
# the Tag model so that we can use the references index to find uses of a tag, but doing that
# correctly will require support for ManyToMany relations with through models:
# https://github.com/wagtail/wagtail/issues/9629
ItemBase.wagtail_reference_index_ignore = True
