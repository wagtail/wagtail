import uuid
from operator import attrgetter

from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import connections, models, router
from django.db.models import signals
from django.db.models.fields.related import (
    ManyToManyRel,
    OneToOneRel,
    RelatedField,
    lazy_related_operation,
)
from django.db.models.query_utils import PathInfo
from django.utils.functional import cached_property
from django.utils.text import capfirst
from django.utils.translation import gettext_lazy as _

from taggit.forms import TagField
from taggit.models import (
    CommonGenericTaggedItemBase,
    GenericUUIDTaggedItemBase,
    TaggedItem,
)
from taggit.utils import require_instance_manager


class ExtraJoinRestriction:
    """
    An extra restriction used for contenttype restriction in joins.
    """

    contains_aggregate = False
    contains_over_clause = False

    def __init__(self, alias, col, content_types):
        self.alias = alias
        self.col = col
        self.content_types = content_types

    def as_sql(self, compiler, connection):
        qn = compiler.quote_name_unless_alias
        if len(self.content_types) == 1:
            extra_where = f"{qn(self.alias)}.{qn(self.col)} = %s"
        else:
            extra_where = "{}.{} IN ({})".format(
                qn(self.alias), qn(self.col), ",".join(["%s"] * len(self.content_types))
            )
        return extra_where, self.content_types

    def relabel_aliases(self, change_map):
        self.alias = change_map.get(self.alias, self.alias)

    def clone(self):
        return type(self)(self.alias, self.col, self.content_types[:])


class _TaggableManager(models.Manager):
    # TODO investigate whether we can use a RelatedManager instead of all this stuff
    # to take advantage of all the Django goodness
    def __init__(self, through, model, instance, prefetch_cache_name, ordering=None):
        super().__init__()
        self.through = through
        self.model = model
        self.instance = instance
        self.prefetch_cache_name = prefetch_cache_name
        if ordering:
            self.ordering = ordering
        else:
            self.ordering = []

    def is_cached(self, instance):
        return self.prefetch_cache_name in instance._prefetched_objects_cache

    def get_queryset(self, extra_filters=None):
        try:
            return self.instance._prefetched_objects_cache[self.prefetch_cache_name]
        except (AttributeError, KeyError):
            kwargs = extra_filters if extra_filters else {}
            return self.through.tags_for(self.model, self.instance, **kwargs).order_by(
                *self.ordering
            )

    def get_prefetch_queryset(self, instances, queryset=None):
        if queryset is None:
            return self.get_prefetch_querysets(instances)
        else:
            return self.get_prefetch_querysets(instances, [queryset])

    def get_prefetch_querysets(self, instances, querysets=None):
        if querysets is not None:
            # this queryset is meant to be used for filtering down the prefetch
            # this work has not been done yet.
            #
            # Some hint from Django: asserting that len(querysets) == 1 if it's not None
            # and then using that to filter down the qs
            raise ValueError("Custom querysets can't be used for this lookup.")

        instance = instances[0]
        db = self._db or router.db_for_read(type(instance), instance=instance)

        fieldname = (
            "object_id"
            if issubclass(self.through, CommonGenericTaggedItemBase)
            else "content_object"
        )
        fk = self.through._meta.get_field(fieldname)
        query = {
            "%s__%s__in"
            % (self.through.tag_relname(), fk.name): {
                obj._get_pk_val() for obj in instances
            }
        }
        join_table = self.through._meta.db_table
        source_col = fk.column
        connection = connections[db]
        qn = connection.ops.quote_name
        qs = (
            self.get_queryset(query)
            .using(db)
            .extra(
                select={
                    "_prefetch_related_val": "{}.{}".format(
                        qn(join_table), qn(source_col)
                    )
                }
            )
        )

        if issubclass(self.through, GenericUUIDTaggedItemBase):

            def uuid_rel_obj_attr(v):
                value = attrgetter("_prefetch_related_val")(v)
                if value is not None and not isinstance(value, uuid.UUID):
                    input_form = "int" if isinstance(value, int) else "hex"
                    value = uuid.UUID(**{input_form: value})
                return value

            rel_obj_attr = uuid_rel_obj_attr
        else:
            rel_obj_attr = attrgetter("_prefetch_related_val")

        return (
            qs,
            rel_obj_attr,
            lambda obj: obj._get_pk_val(),
            False,
            self.prefetch_cache_name,
            False,
        )

    def _lookup_kwargs(self):
        return self.through.lookup_kwargs(self.instance)

    def _remove_prefetched_objects(self):
        prefetch_cache = getattr(self.instance, "_prefetched_objects_cache", None)
        if prefetch_cache:
            prefetch_cache.pop(self.prefetch_cache_name, None)

    @require_instance_manager
    def add(self, *tags, through_defaults=None, tag_kwargs=None, **kwargs):
        self._remove_prefetched_objects()
        if tag_kwargs is None:
            tag_kwargs = {}
        db = router.db_for_write(self.through, instance=self.instance)

        tag_objs = self._to_tag_model_instances(tags, tag_kwargs)
        new_ids = {t.pk for t in tag_objs}

        # NOTE: can we hardcode 'tag_id' here or should the column name be got
        # dynamically from somewhere?
        vals = (
            self.through._default_manager.using(db)
            .values_list("tag_id", flat=True)
            .filter(**self._lookup_kwargs())
        )

        new_ids = new_ids - set(vals)

        signals.m2m_changed.send(
            sender=self.through,
            action="pre_add",
            instance=self.instance,
            reverse=False,
            model=self.through.tag_model(),
            pk_set=new_ids,
            using=db,
        )

        for tag in tag_objs:
            self.through._default_manager.using(db).get_or_create(
                tag=tag, **self._lookup_kwargs(), defaults=through_defaults
            )

        signals.m2m_changed.send(
            sender=self.through,
            action="post_add",
            instance=self.instance,
            reverse=False,
            model=self.through.tag_model(),
            pk_set=new_ids,
            using=db,
        )

    def _to_tag_model_instances(self, tags, tag_kwargs):
        """
        Takes an iterable containing either strings, tag objects, or a mixture
        of both and returns set of tag objects.
        """
        db = router.db_for_write(self.through, instance=self.instance)

        str_tags = set()
        tag_objs = set()

        for t in tags:
            if isinstance(t, self.through.tag_model()):
                tag_objs.add(t)
            elif isinstance(t, str):
                str_tags.add(t)
            else:
                raise ValueError(
                    "Cannot add {} ({}). Expected {} or str.".format(
                        t, type(t), type(self.through.tag_model())
                    )
                )

        case_insensitive = getattr(settings, "TAGGIT_CASE_INSENSITIVE", False)
        manager = self.through.tag_model()._default_manager.using(db)

        if case_insensitive:
            # Some databases can do case-insensitive comparison with IN, which
            # would be faster, but we can't rely on it or easily detect it.
            existing = []
            tags_to_create = []

            for name in str_tags:
                try:
                    tag = manager.get(name__iexact=name, **tag_kwargs)
                    existing.append(tag)
                except self.through.tag_model().DoesNotExist:
                    tags_to_create.append(name)
        else:
            # If str_tags has 0 elements Django actually optimizes that to not
            # do a query.  Malcolm is very smart.
            existing = manager.filter(name__in=str_tags, **tag_kwargs)

            tags_to_create = str_tags - {t.name for t in existing}

        tag_objs.update(existing)

        for new_tag in tags_to_create:
            if case_insensitive:
                lookup = {"name__iexact": new_tag, **tag_kwargs}
            else:
                lookup = {"name": new_tag, **tag_kwargs}

            tag, create = manager.get_or_create(**lookup, defaults={"name": new_tag})
            tag_objs.add(tag)

        return tag_objs

    @require_instance_manager
    def names(self):
        return self.get_queryset().values_list("name", flat=True)

    @require_instance_manager
    def slugs(self):
        return self.get_queryset().values_list("slug", flat=True)

    @require_instance_manager
    def set(self, tags, *, through_defaults=None, **kwargs):
        """
        Set the object's tags to the given n tags. If the clear kwarg is True
        then all existing tags are removed (using `.clear()`) and the new tags
        added. Otherwise, only those tags that are not present in the args are
        removed and any new tags added.

        Any kwarg apart from 'clear' will be passed when adding tags.

        """
        db = router.db_for_write(self.through, instance=self.instance)

        clear = kwargs.pop("clear", False)
        tag_kwargs = kwargs.pop("tag_kwargs", {})

        if clear:
            self.clear()
            self.add(*tags, **kwargs)
        else:
            # make sure we're working with a collection of a uniform type
            objs = self._to_tag_model_instances(tags, tag_kwargs)

            # get the existing tag strings
            old_tag_strs = set(
                self.through._default_manager.using(db)
                .filter(**self._lookup_kwargs())
                .values_list("tag__name", flat=True)
            )

            new_objs = []
            for obj in objs:
                if obj.name in old_tag_strs:
                    old_tag_strs.remove(obj.name)
                else:
                    new_objs.append(obj)

            self.remove(*old_tag_strs)
            self.add(*new_objs, through_defaults=through_defaults, **kwargs)

    @require_instance_manager
    def remove(self, *tags):
        if not tags:
            return

        self._remove_prefetched_objects()
        db = router.db_for_write(self.through, instance=self.instance)

        qs = (
            self.through._default_manager.using(db)
            .filter(**self._lookup_kwargs())
            .filter(tag__name__in=tags)
        )

        old_ids = set(qs.values_list("tag_id", flat=True))

        signals.m2m_changed.send(
            sender=self.through,
            action="pre_remove",
            instance=self.instance,
            reverse=False,
            model=self.through.tag_model(),
            pk_set=old_ids,
            using=db,
        )
        qs.delete()
        signals.m2m_changed.send(
            sender=self.through,
            action="post_remove",
            instance=self.instance,
            reverse=False,
            model=self.through.tag_model(),
            pk_set=old_ids,
            using=db,
        )

    @require_instance_manager
    def clear(self):
        self._remove_prefetched_objects()
        db = router.db_for_write(self.through, instance=self.instance)

        signals.m2m_changed.send(
            sender=self.through,
            action="pre_clear",
            instance=self.instance,
            reverse=False,
            model=self.through.tag_model(),
            pk_set=None,
            using=db,
        )

        self.through._default_manager.using(db).filter(**self._lookup_kwargs()).delete()

        signals.m2m_changed.send(
            sender=self.through,
            action="post_clear",
            instance=self.instance,
            reverse=False,
            model=self.through.tag_model(),
            pk_set=None,
            using=db,
        )

    def most_common(self, min_count=None, extra_filters=None):
        queryset = (
            self.get_queryset(extra_filters)
            .annotate(num_times=models.Count(self.through.tag_relname()))
            .order_by("-num_times")
        )
        if min_count:
            queryset = queryset.filter(num_times__gte=min_count)

        return queryset

    @require_instance_manager
    def similar_objects(self):
        lookup_kwargs = self._lookup_kwargs()
        lookup_keys = sorted(lookup_kwargs)
        qs = self.through.objects.values(*lookup_kwargs.keys())
        qs = qs.annotate(n=models.Count("pk"))
        qs = qs.exclude(**lookup_kwargs)
        qs = qs.filter(tag__in=self.all())
        qs = qs.order_by("-n")

        # TODO: This all feels like a bit of a hack.
        items = {}
        if len(lookup_keys) == 1:
            # Can we do this without a second query by using a select_related()
            # somehow?
            f = self.through._meta.get_field(lookup_keys[0])
            remote_field = f.remote_field
            rel_model = remote_field.model
            objs = rel_model._default_manager.filter(
                **{
                    "%s__in"
                    % remote_field.field_name: [r["content_object"] for r in qs]
                }
            )
            actual_remote_field_name = f.target_field.get_attname()
            for obj in objs:
                items[(getattr(obj, actual_remote_field_name),)] = obj
        else:
            preload = {}
            for result in qs:
                preload.setdefault(result["content_type"], set())
                preload[result["content_type"]].add(result["object_id"])

            for ct, obj_ids in preload.items():
                ct = ContentType.objects.get_for_id(ct)
                for obj in ct.model_class()._default_manager.filter(pk__in=obj_ids):
                    items[(ct.pk, obj.pk)] = obj

        results = []
        for result in qs:
            obj = items[tuple(result[k] for k in lookup_keys)]
            obj.similar_tags = result["n"]
            results.append(obj)
        return results


class TaggableManager(RelatedField):
    # Field flags
    many_to_many = True
    many_to_one = False
    one_to_many = False
    one_to_one = False

    _related_name_counter = 0

    def __init__(
        self,
        verbose_name=_("Tags"),
        help_text=_("A comma-separated list of tags."),
        through=None,
        blank=False,
        related_name=None,
        to=None,
        ordering=None,
        manager=_TaggableManager,
    ):
        self.through = through or TaggedItem

        rel = ManyToManyRel(self, to, related_name=related_name, through=self.through)

        super().__init__(
            verbose_name=verbose_name,
            help_text=help_text,
            blank=blank,
            null=True,
            serialize=False,
            rel=rel,
        )

        self.ordering = ordering
        self.swappable = False
        self.manager = manager

    def __get__(self, instance, model):
        if instance is not None and instance.pk is None:
            raise ValueError(
                "%s objects need to have a primary key value "
                "before you can access their tags." % model.__name__
            )
        return self.manager(
            through=self.through,
            model=model,
            instance=instance,
            prefetch_cache_name=self.name,
            ordering=self.ordering,
        )

    def deconstruct(self):
        """
        Deconstruct the object, used with migrations.
        """
        name, path, args, kwargs = super().deconstruct()
        # Remove forced kwargs.
        for kwarg in ("serialize", "null"):
            del kwargs[kwarg]
        # Add arguments related to relations.
        # Ref: https://github.com/jazzband/django-taggit/issues/206#issuecomment-37578676
        rel = self.remote_field
        if isinstance(rel.through, str):
            kwargs["through"] = rel.through
        elif not rel.through._meta.auto_created:
            kwargs["through"] = "{}.{}".format(
                rel.through._meta.app_label, rel.through._meta.object_name
            )

        related_model = rel.model
        if isinstance(related_model, str):
            kwargs["to"] = related_model
        else:
            kwargs["to"] = "{}.{}".format(
                related_model._meta.app_label, related_model._meta.object_name
            )

        return name, path, args, kwargs

    def contribute_to_class(self, cls, name):
        self.set_attributes_from_name(name)
        self.model = cls
        self.opts = cls._meta

        cls._meta.add_field(self)
        setattr(cls, name, self)
        if not cls._meta.abstract:
            if isinstance(self.remote_field.model, str):

                def resolve_related_class(cls, model, field):
                    field.remote_field.model = model

                lazy_related_operation(
                    resolve_related_class, cls, self.remote_field.model, field=self
                )
            if isinstance(self.through, str):

                def resolve_related_class(cls, model, field):
                    self.through = model
                    self.remote_field.through = model
                    self.post_through_setup(cls)

                lazy_related_operation(
                    resolve_related_class, cls, self.through, field=self
                )
            else:
                self.post_through_setup(cls)

    def get_internal_type(self):
        return "ManyToManyField"

    def post_through_setup(self, cls):
        self.use_gfk = self.through is None or issubclass(
            self.through, CommonGenericTaggedItemBase
        )

        if not self.remote_field.model:
            self.remote_field.model = self.through._meta.get_field(
                "tag"
            ).remote_field.model

        if self.use_gfk:
            tagged_items = GenericRelation(self.through)
            tagged_items.contribute_to_class(cls, "tagged_items")

        for rel in cls._meta.local_many_to_many:
            if rel == self or not isinstance(rel, TaggableManager):
                continue
            if rel.through == self.through:
                raise ValueError(
                    "You can't have two TaggableManagers with the"
                    " same through model."
                )

    def save_form_data(self, instance, value):
        getattr(instance, self.name).set(value)

    def formfield(self, form_class=TagField, **kwargs):
        defaults = {
            "label": capfirst(self.verbose_name),
            "help_text": self.help_text,
            "required": not self.blank,
        }
        defaults.update(kwargs)
        return form_class(**defaults)

    def value_from_object(self, obj):
        if obj.pk is None:
            return []
        qs = self.through.objects.select_related("tag").filter(
            **self.through.lookup_kwargs(obj)
        )
        return [ti.tag for ti in qs]

    def m2m_reverse_name(self):
        return self.through._meta.get_field("tag").column

    def m2m_reverse_field_name(self):
        return self.through._meta.get_field("tag").name

    def m2m_target_field_name(self):
        return self.model._meta.pk.name

    def m2m_reverse_target_field_name(self):
        return self.remote_field.model._meta.pk.name

    def m2m_column_name(self):
        if self.use_gfk:
            return self.through._meta.private_fields[0].fk_field
        return self.through._meta.get_field("content_object").column

    def m2m_db_table(self):
        return self.through._meta.db_table

    def bulk_related_objects(self, new_objs, using):
        return []

    def _get_mm_case_path_info(self, direct=False, filtered_relation=None):
        pathinfos = []
        linkfield1 = self.through._meta.get_field("content_object")
        linkfield2 = self.through._meta.get_field(self.m2m_reverse_field_name())
        if not filtered_relation:
            # Django >= 4.1 provides cached path_infos and reverse_path_infos properties
            # to use in preference to get_path_info / get_reverse_path_info when not
            # passing a filtered_relation
            if direct:
                join1infos = linkfield1.reverse_path_infos
                join2infos = linkfield2.path_infos
            else:
                join1infos = linkfield2.reverse_path_infos
                join2infos = linkfield1.path_infos
        else:
            if direct:
                join1infos = linkfield1.get_reverse_path_info(
                    filtered_relation=filtered_relation
                )
                join2infos = linkfield2.get_path_info(
                    filtered_relation=filtered_relation
                )
            else:
                join1infos = linkfield2.get_reverse_path_info(
                    filtered_relation=filtered_relation
                )
                join2infos = linkfield1.get_path_info(
                    filtered_relation=filtered_relation
                )
        pathinfos.extend(join1infos)
        pathinfos.extend(join2infos)
        return pathinfos

    def _get_gfk_case_path_info(self, direct=False, filtered_relation=None):
        pathinfos = []
        from_field = self.model._meta.pk
        opts = self.through._meta
        linkfield = self.through._meta.get_field(self.m2m_reverse_field_name())
        if direct:
            join1infos = [
                PathInfo(
                    self.model._meta,
                    opts,
                    [from_field],
                    self.remote_field,
                    True,
                    False,
                    filtered_relation,
                )
            ]
            if not filtered_relation:
                join2infos = linkfield.path_infos
            else:
                join2infos = linkfield.get_path_info(
                    filtered_relation=filtered_relation
                )
        else:
            if not filtered_relation:
                join1infos = linkfield.reverse_path_infos
            else:
                join1infos = linkfield.get_reverse_path_info(
                    filtered_relation=filtered_relation
                )
            join2infos = [
                PathInfo(
                    opts,
                    self.model._meta,
                    [from_field],
                    self,
                    True,
                    False,
                    filtered_relation,
                )
            ]
        pathinfos.extend(join1infos)
        pathinfos.extend(join2infos)
        return pathinfos

    def get_path_info(self, filtered_relation=None):
        if self.use_gfk:
            return self._get_gfk_case_path_info(
                direct=True, filtered_relation=filtered_relation
            )
        else:
            return self._get_mm_case_path_info(
                direct=True, filtered_relation=filtered_relation
            )

    @cached_property
    def path_infos(self):
        return self.get_path_info()

    def get_reverse_path_info(self, filtered_relation=None):
        if self.use_gfk:
            return self._get_gfk_case_path_info(
                direct=False, filtered_relation=filtered_relation
            )
        else:
            return self._get_mm_case_path_info(
                direct=False, filtered_relation=filtered_relation
            )

    @cached_property
    def reverse_path_infos(self):
        return self.get_reverse_path_info()

    def get_joining_columns(self, reverse_join=False):
        # RemovedInDjango60Warning
        # https://github.com/django/django/commit/8b1ff0da4b162e87edebd94e61f2cd153e9e159d
        if reverse_join:
            return ((self.model._meta.pk.column, "object_id"),)
        else:
            return (("object_id", self.model._meta.pk.column),)

    def get_joining_fields(self, reverse_join=False):
        if reverse_join:
            return (
                (
                    self.model._meta.pk,
                    self.remote_field.through._meta.get_field("object_id"),
                ),
            )
        else:
            return (
                (
                    self.remote_field.through._meta.get_field("object_id"),
                    self.model._meta.pk,
                ),
            )

    def get_extra_restriction(self, alias, related_alias):
        extra_col = self.through._meta.get_field("content_type").column
        content_type_ids = [
            ContentType.objects.get_for_model(subclass).pk
            for subclass in _get_subclasses(self.model)
        ]
        return ExtraJoinRestriction(related_alias, extra_col, content_type_ids)

    def get_reverse_joining_columns(self):
        # RemovedInDjango60Warning
        # https://github.com/django/django/commit/8b1ff0da4b162e87edebd94e61f2cd153e9e159d
        return self.get_joining_columns(reverse_join=True)

    def get_reverse_joining_fields(self):
        return self.get_joining_fields(reverse_join=True)

    @property
    def related_fields(self):
        return [(self.through._meta.get_field("object_id"), self.model._meta.pk)]

    @property
    def foreign_related_fields(self):
        return [self.related_fields[0][1]]


def _get_subclasses(model):
    subclasses = [model]
    for field in model._meta.get_fields():
        if isinstance(field, OneToOneRel) and getattr(
            field.field.remote_field, "parent_link", None
        ):
            subclasses.extend(_get_subclasses(field.related_model))
    return subclasses
