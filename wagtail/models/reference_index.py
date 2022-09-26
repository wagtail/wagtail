import uuid

from django.contrib.contenttypes.fields import GenericForeignKey, GenericRel
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.text import capfirst
from django.utils.translation import gettext_lazy as _
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel, get_all_child_relations

from wagtail.fields import RichTextField, StreamField


class ReferenceGroups:
    def __init__(self, qs):
        self.qs = qs

    def __iter__(self):
        object = None
        references = []
        for reference in self.qs.order_by("base_content_type", "object_id"):
            if object != (reference.base_content_type, reference.object_id):
                if object is not None:
                    yield object[0].get_object_for_this_type(pk=object[1]), references
                    references = []

                object = (reference.base_content_type, reference.object_id)

            references.append(reference)

        if references:
            yield object[0].get_object_for_this_type(pk=object[1]), references

    def __len__(self):
        return (
            self.qs.order_by("base_content_type", "object_id")
            .values("base_content_type", "object_id")
            .distinct()
            .count()
        )

    def count(self):
        return len(self)

    def __getitem__(self, key):
        return list(self)[key]


class ReferenceIndexQuerySet(models.QuerySet):
    def group_by_source_object(self):
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

    # These are dotted path, always starting with a field orchild relation name. If
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
        """
        if getattr(model, "wagtail_reference_index_ignore", False):
            return False

        # Don't check any models that have a parental key, references from these will be collected from the parent
        if not allow_child_models and any(
            [isinstance(field, ParentalKey) for field in model._meta.get_fields()]
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

            if isinstance(field, (StreamField, RichTextField)):
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
    def _extract_references_from_object(cls, object):
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

                    yield ct_field.value_from_object(object), str(
                        fk_field.value_from_object(object)
                    ), field.name, field.name
                    continue

                if isinstance(field, GenericRel):
                    continue

                value = field.value_from_object(object)
                if value is not None:
                    yield cls._get_base_content_type(field.related_model).id, str(
                        value
                    ), field.name, field.name

            if isinstance(field, (StreamField, RichTextField)):
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
        return uuid.uuid5(
            uuid.UUID("bdc70d8b-e7a2-4c2a-bf43-2a3e3fcbbe86"), content_path
        )

    @classmethod
    def create_or_update_for_object(cls, object):
        # Extract new references
        references = set(cls._extract_references_from_object(object))

        # Find existing references in the database so we know what to add/delete
        content_type = ContentType.objects.get_for_model(object)
        base_content_type = cls._get_base_content_type(object)
        existing_references = {
            (to_content_type_id, to_object_id, model_path, content_path): id
            for id, to_content_type_id, to_object_id, model_path, content_path in cls.objects.filter(
                base_content_type=base_content_type, object_id=object.pk
            ).values_list(
                "id", "to_content_type", "to_object_id", "model_path", "content_path"
            )
        }

        # Add new references
        new_references = references - set(existing_references.keys())
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
            ]
        )

        # Delete removed references
        deleted_references = set(existing_references.keys()) - references
        cls.objects.filter(
            id__in=[existing_references[reference] for reference in deleted_references]
        ).delete()

    @classmethod
    def remove_for_object(cls, object):
        base_content_type = cls._get_base_content_type(object)
        cls.objects.filter(
            base_content_type=base_content_type, object_id=object.pk
        ).delete()

    @classmethod
    def get_references_for_object(cls, object):
        return cls.objects.filter(
            base_content_type_id=cls._get_base_content_type(object),
            object_id=object.pk,
        )

    @classmethod
    def get_references_to(cls, object):
        return cls.objects.filter(
            to_content_type_id=cls._get_base_content_type(object),
            to_object_id=object.pk,
        )

    def describe_source_field(self):
        model_path_components = self.model_path.split(".")
        field_name = model_path_components[0]
        field = self.content_type.model_class()._meta.get_field(field_name)

        # ManyToOneRel (reverse accessor for ParentalKey) does not have a verbose name. So get the name of the child field instead
        if isinstance(field, models.ManyToOneRel):
            child_field = field.related_model._meta.get_field(model_path_components[2])
            return capfirst(child_field.verbose_name)
        else:
            return capfirst(field.verbose_name)
