from collections import OrderedDict

from django.urls.exceptions import NoReverseMatch
from modelcluster.models import get_all_child_relations
from rest_framework import relations, serializers
from rest_framework.fields import Field, SkipField
from taggit.managers import _TaggableManager

from wagtail import fields as wagtailcore_fields

from .utils import get_object_detail_url


class TypeField(Field):
    """
    Serializes the "type" field of each object.

    Example:
    "type": "wagtailimages.Image"
    """

    def get_attribute(self, instance):
        return instance

    def to_representation(self, obj):
        name = type(obj)._meta.app_label + "." + type(obj).__name__
        self.context["view"].seen_types[name] = type(obj)
        return name


class DetailUrlField(Field):
    """
    Serializes the "detail_url" field of each object.

    Example:
    "detail_url": "http://api.example.com/v1/images/1/"
    """

    def get_attribute(self, instance):
        url = get_object_detail_url(
            self.context["router"], self.context["request"], type(instance), instance.pk
        )

        if url:
            return url
        else:
            # Hide the detail_url field if the object doesn't have an endpoint
            raise SkipField

    def to_representation(self, url):
        return url


class PageHtmlUrlField(Field):
    """
    Serializes the "html_url" field for pages.

    Example:
    "html_url": "http://www.example.com/blog/blog-post/"
    """

    def get_attribute(self, instance):
        return instance

    def to_representation(self, page):
        try:
            return page.full_url
        except NoReverseMatch:
            return None


class PageTypeField(Field):
    """
    Serializes the "type" field for pages.

    This takes into account the fact that we sometimes may not have the "specific"
    page object by calling "page.specific_class" instead of looking at the object's
    type.

    Example:
    "type": "blog.BlogPage"
    """

    def get_attribute(self, instance):
        return instance

    def to_representation(self, page):
        if page.specific_class is None:
            return None
        name = page.specific_class._meta.app_label + "." + page.specific_class.__name__
        self.context["view"].seen_types[name] = page.specific_class
        return name


class PageLocaleField(Field):
    """
    Serializes the "locale" field for pages.
    """

    def get_attribute(self, instance):
        return instance

    def to_representation(self, page):
        return page.locale.language_code


class RelatedField(relations.RelatedField):
    """
    Serializes related objects (eg, foreign keys).

    Example:

    "feed_image": {
        "id": 1,
        "meta": {
            "type": "wagtailimages.Image",
            "detail_url": "http://api.example.com/v1/images/1/"
        }
    }
    """

    def __init__(self, *args, **kwargs):
        self.serializer_class = kwargs.pop("serializer_class")
        super().__init__(*args, **kwargs)

    def to_representation(self, value):
        serializer = self.serializer_class(context=self.context)
        return serializer.to_representation(value)


class PageParentField(relations.RelatedField):
    """
    Serializes the "parent" field on Page objects.

    Pages don't have a "parent" field so some extra logic is needed to find the
    parent page. That logic is implemented in this class.

    The representation is the same as the RelatedField class.
    """

    def get_attribute(self, instance):
        parent = instance.get_parent()

        if self.context["base_queryset"].filter(id=parent.id).exists():
            return parent

    def to_representation(self, value):
        serializer_class = get_serializer_class(
            value.__class__,
            ["id", "type", "detail_url", "html_url", "title"],
            meta_fields=["type", "detail_url", "html_url"],
            base=PageSerializer,
        )
        serializer = serializer_class(context=self.context)
        return serializer.to_representation(value)


class PageAliasOfField(relations.RelatedField):
    """
    Serializes the "alias_of" field on Page objects.
    """

    def get_attribute(self, instance):
        return instance.alias_of

    def to_representation(self, value):
        serializer_class = get_serializer_class(
            value.__class__,
            ["id", "type", "detail_url", "html_url", "title"],
            meta_fields=["type", "detail_url", "html_url"],
            base=PageSerializer,
        )
        serializer = serializer_class(context=self.context)
        return serializer.to_representation(value)


class ChildRelationField(Field):
    """
    Serializes child relations.

    Child relations are any model that is related to a Page using a ParentalKey.
    They are used for repeated fields on a page such as carousel items or related
    links.

    Child objects are part of the pages content so we nest them. The relation is
    represented as a list of objects.

    Example:

    "carousel_items": [
        {
            "id": 1,
            "meta": {
                "type": "demo.MyCarouselItem"
            },
            "title": "First carousel item",
            "image": {
                "id": 1,
                "meta": {
                    "type": "wagtailimages.Image",
                    "detail_url": "http://api.example.com/v1/images/1/"
                }
            }
        },
        {
            "id": 2,
            "meta": {
                "type": "demo.MyCarouselItem"
            },
            "title": "Second carousel item (no image)",
            "image": null
        }
    ]
    """

    def __init__(self, *args, **kwargs):
        self.serializer_class = kwargs.pop("serializer_class")
        super().__init__(*args, **kwargs)

    def to_representation(self, value):
        serializer = self.serializer_class(context=self.context)

        return [
            serializer.to_representation(child_object) for child_object in value.all()
        ]


class StreamField(Field):
    """
    Serializes StreamField values.

    Stream fields are stored in JSON format in the database. We reuse that in
    the API.

    Example:

    "body": [
        {
            "type": "heading",
            "value": {
                "text": "Hello world!",
                "size": "h1"
            }
        },
        {
            "type": "paragraph",
            "value": "Some content"
        }
        {
            "type": "image",
            "value": 1
        }
    ]

    Where "heading" is a struct block containing "text" and "size" fields, and
    "paragraph" is a simple text block.

    Note that foreign keys are represented slightly differently in stream fields
    to other parts of the API. In stream fields, a foreign key is represented
    by an integer (the ID of the related object) but elsewhere in the API,
    foreign objects are nested objects with id and meta as attributes.
    """

    def to_representation(self, value):
        return value.stream_block.get_api_representation(value, self.context)


class TagsField(Field):
    """
    Serializes django-taggit TaggableManager fields.

    These fields are a common way to link tags to objects in Wagtail. The API
    serializes these as a list of strings taken from the name attribute of each
    tag.

    Example:

    "tags": ["bird", "wagtail"]
    """

    def to_representation(self, value):
        return list(value.all().order_by("name").values_list("name", flat=True))


class BaseSerializer(serializers.ModelSerializer):
    # Add StreamField to serializer_field_mapping
    serializer_field_mapping = (
        serializers.ModelSerializer.serializer_field_mapping.copy()
    )
    serializer_field_mapping.update(
        {
            wagtailcore_fields.StreamField: StreamField,
        }
    )
    serializer_related_field = RelatedField

    # Meta fields
    type = TypeField(read_only=True)
    detail_url = DetailUrlField(read_only=True)

    def to_representation(self, instance):
        data = OrderedDict()
        fields = [field for field in self.fields.values() if not field.write_only]

        # Split meta fields from core fields
        meta_fields = [
            field for field in fields if field.field_name in self.meta_fields
        ]
        fields = [field for field in fields if field.field_name not in self.meta_fields]

        # Make sure id is always first. This will be filled in later
        if "id" in [field.field_name for field in fields]:
            data["id"] = None

        # Serialise meta fields
        meta = OrderedDict()
        for field in meta_fields:
            try:
                attribute = field.get_attribute(instance)
            except SkipField:
                continue

            if attribute is None:
                # We skip `to_representation` for `None` values so that
                # fields do not have to explicitly deal with that case.
                meta[field.field_name] = None
            else:
                meta[field.field_name] = field.to_representation(attribute)

        if meta:
            data["meta"] = meta

        # Serialise core fields
        for field in fields:
            try:
                if field.field_name == "admin_display_title":
                    instance = instance.specific_deferred

                attribute = field.get_attribute(instance)
            except SkipField:
                continue

            if attribute is None:
                # We skip `to_representation` for `None` values so that
                # fields do not have to explicitly deal with that case.
                data[field.field_name] = None
            else:
                data[field.field_name] = field.to_representation(attribute)

        return data

    def build_property_field(self, field_name, model_class):
        # TaggableManager is not a Django field so it gets treated as a property
        field = getattr(model_class, field_name)
        if isinstance(field, _TaggableManager):
            return TagsField, {}

        return super().build_property_field(field_name, model_class)

    def build_relational_field(self, field_name, relation_info):
        field_class, field_kwargs = super().build_relational_field(
            field_name, relation_info
        )
        field_kwargs["serializer_class"] = self.child_serializer_classes[field_name]
        return field_class, field_kwargs


class PageSerializer(BaseSerializer):
    type = PageTypeField(read_only=True)
    locale = PageLocaleField(read_only=True)
    html_url = PageHtmlUrlField(read_only=True)
    parent = PageParentField(read_only=True)
    alias_of = PageAliasOfField(read_only=True)

    def build_relational_field(self, field_name, relation_info):
        # Find all relation fields that point to child class and make them use
        # the ChildRelationField class.
        if relation_info.to_many:
            model = getattr(self.Meta, "model")
            child_relations = {
                child_relation.field.remote_field.related_name: child_relation.related_model
                for child_relation in get_all_child_relations(model)
            }

            if (
                field_name in child_relations
                and field_name in self.child_serializer_classes
            ):
                return ChildRelationField, {
                    "serializer_class": self.child_serializer_classes[field_name]
                }

        return super().build_relational_field(field_name, relation_info)


def get_serializer_class(
    model,
    field_names,
    meta_fields,
    field_serializer_overrides=None,
    child_serializer_classes=None,
    base=BaseSerializer,
):
    model_ = model

    class Meta:
        model = model_
        fields = list(field_names)

    attrs = {
        "Meta": Meta,
        "meta_fields": list(meta_fields),
        "child_serializer_classes": child_serializer_classes or {},
    }

    if field_serializer_overrides:
        attrs.update(field_serializer_overrides)

    return type(str(model_.__name__ + "Serializer"), (base,), attrs)
