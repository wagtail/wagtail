from __future__ import absolute_import, unicode_literals

from collections import OrderedDict

from modelcluster.models import get_all_child_relations
from rest_framework import relations, serializers
from rest_framework.fields import Field
from taggit.managers import _TaggableManager

from wagtail.wagtailcore import fields as wagtailcore_fields

from .utils import get_full_url, pages_for_site


def get_object_detail_url(context, model, pk):
    url_path = context['router'].get_object_detail_urlpath(model, pk)

    if url_path:
        return get_full_url(context['request'], url_path)


class MetaField(Field):
    """
    Serializes the "meta" section of each object.

    This section is used for storing non-field data such as model name, urls, etc.

    Example:

    "meta": {
        "type": "wagtailimages.Image",
        "detail_url": "http://api.example.com/v1/images/1/"
    }
    """
    def get_attribute(self, instance):
        return instance

    def to_representation(self, obj):
        return OrderedDict([
            ('type', type(obj)._meta.app_label + '.' + type(obj).__name__),
            ('detail_url', get_object_detail_url(self.context, type(obj), obj.pk)),
        ])


class PageMetaField(MetaField):
    """
    A subclass of MetaField for Page objects.

    Changes the "type" field to use the name of the specific model of the page.

    Example:

    "meta": {
        "type": "blog.BlogPage",
        "detail_url": "http://api.example.com/v1/pages/1/"
    }
    """
    def to_representation(self, page):
        return OrderedDict([
            ('type', page.specific_class._meta.app_label + '.' + page.specific_class.__name__),
            ('detail_url', get_object_detail_url(self.context, type(page), page.pk)),
        ])


class DocumentMetaField(MetaField):
    """
    A subclass of MetaField for Document objects.

    Adds a "download_url" field.

    "meta": {
        "type": "wagtaildocs.Document",
        "detail_url": "http://api.example.com/v1/documents/1/",
        "download_url": "http://api.example.com/documents/1/my_document.pdf"
    }
    """
    def to_representation(self, document):
        data = OrderedDict([
            ('type', "wagtaildocs.Document"),
            ('detail_url', get_object_detail_url(self.context, type(document), document.pk)),
        ])

        # Add download url
        if self.context.get('show_details', False):
            data['download_url'] = get_full_url(self.context['request'], document.url)

        return data


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
    meta_field_serializer_class = MetaField

    def to_representation(self, value):
        meta_serializer = self.meta_field_serializer_class()
        meta_serializer.bind('meta', self)

        return OrderedDict([
            ('id', value.pk),
            ('meta', meta_serializer.to_representation(value)),
        ])


class PageParentField(RelatedField):
    """
    Serializes the "parent" field on Page objects.

    Pages don't have a "parent" field so some extra logic is needed to find the
    parent page. That logic is implemented in this class.

    The representation is the same as the RelatedField class.
    """
    meta_field_serializer_class = PageMetaField

    def get_attribute(self, instance):
        parent = instance.get_parent()

        site_pages = pages_for_site(self.context['request'].site)
        if site_pages.filter(id=parent.id).exists():
            return parent


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
            "title": "First carousel item",
            "image": {
                "id": 1,
                "meta": {
                    "type": "wagtailimages.Image",
                    "detail_url": "http://api.example.com/v1/images/1/"
                }
            }
        },
        "carousel_items": [
        {
            "title": "Second carousel item (no image)",
            "image": null
        }
    ]
    """
    def __init__(self, *args, **kwargs):
        self.child_fields = kwargs.pop('child_fields')
        super(ChildRelationField, self).__init__(*args, **kwargs)

    def to_representation(self, value):
        serializer_class = get_serializer_class(value.model, self.child_fields)
        serializer = serializer_class(context=self.context)

        return [
            serializer.to_representation(child_object)
            for child_object in value.all()
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
        return value.stream_block.get_prep_value(value)


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
        return list(value.all().order_by('name').values_list('name', flat=True))


class BaseSerializer(serializers.ModelSerializer):
    # Add StreamField to serializer_field_mapping
    serializer_field_mapping = serializers.ModelSerializer.serializer_field_mapping.copy()
    serializer_field_mapping.update({
        wagtailcore_fields.StreamField: StreamField,
    })
    serializer_related_field = RelatedField

    meta = MetaField()

    def build_property_field(self, field_name, model_class):
        # TaggableManager is not a Django field so it gets treated as a property
        field = getattr(model_class, field_name)
        if isinstance(field, _TaggableManager):
            return TagsField, {}

        return super(BaseSerializer, self).build_property_field(field_name, model_class)


class PageSerializer(BaseSerializer):
    meta = PageMetaField()
    parent = PageParentField(read_only=True)

    def build_relational_field(self, field_name, relation_info):
        # Find all relation fields that point to child class and make them use
        # the ChildRelationField class.
        if relation_info.to_many:
            model = getattr(self.Meta, 'model')
            child_relations = {
                child_relation.field.rel.related_name: child_relation.related_model
                for child_relation in get_all_child_relations(model)
            }

            if field_name in child_relations and hasattr(child_relations[field_name], 'api_fields'):
                return ChildRelationField, {'child_fields': child_relations[field_name].api_fields}

        return super(BaseSerializer, self).build_relational_field(field_name, relation_info)


class ImageSerializer(BaseSerializer):
    pass


class DocumentSerializer(BaseSerializer):
    meta = DocumentMetaField()


def get_serializer_class(model_, fields_, base=BaseSerializer):
    class Meta:
        model = model_
        fields = fields_

    return type(str(model_.__name__ + 'Serializer'), (base, ), {
        'Meta': Meta
    })
