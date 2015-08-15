from __future__ import absolute_import

from collections import OrderedDict

from modelcluster.models import get_all_child_relations

from taggit.managers import _TaggableManager

from rest_framework import serializers
from rest_framework.fields import Field
from rest_framework import relations

from wagtail.utils.compat import get_related_model
from wagtail.wagtailcore import fields as wagtailcore_fields

from .utils import ObjectDetailURL, URLPath, pages_for_site


class MetaField(Field):
    def get_attribute(self, instance):
        return instance

    def to_representation(self, obj):
        return OrderedDict([
            ('type', type(obj)._meta.app_label + '.' + type(obj).__name__),
            ('detail_url', ObjectDetailURL(type(obj), obj.pk)),
        ])


class PageMetaField(MetaField):
    def to_representation(self, page):
        data = super(PageMetaField, self).to_representation(page)

        # Change type to the specific page class instead
        data['type'] = page.specific_class._meta.app_label + '.' + page.specific_class.__name__

        return data


class DocumentMetaField(MetaField):
    def to_representation(self, document):
        data = super(DocumentMetaField, self).to_representation(document)

        # Add download url
        if self.context.get('show_details', False):
            data['download_url'] = URLPath(document.url)

        return data


class RelatedField(relations.RelatedField):
    meta_field_serializer_class = MetaField

    def to_representation(self, value):
        return OrderedDict([
            ('id', value.pk),
            ('meta', self.meta_field_serializer_class().to_representation(value)),
        ])


class PageParentField(RelatedField):
    meta_field_serializer_class = PageMetaField

    def get_attribute(self, instance):
        parent = instance.get_parent()

        site_pages = pages_for_site(self.context['request'].site)
        if site_pages.filter(id=parent.id).exists():
            return parent


class ChildRelationField(Field):
    """
    Child objects are part of the pages content so we nest them on the page.
    """
    def __init__(self, *args, **kwargs):
        self.child_fields = kwargs.pop('child_fields')
        super(ChildRelationField, self).__init__(*args, **kwargs)

    def to_representation(self, value):
        serializer_class = get_serializer_class(value.model, self.child_fields)
        serializer = serializer_class()

        return [
            serializer.to_representation(child_object)
            for child_object in value.all()
        ]


class StreamField(Field):
    def to_representation(self, value):
        return value.stream_block.get_prep_value(value)


class TagsField(Field):
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
                child_relation.field.rel.related_name: get_related_model(child_relation)
                for child_relation in get_all_child_relations(model)
            }

            if field_name in child_relations and hasattr(child_relations[field_name], 'api_fields'):
                return ChildRelationField, {'child_fields': child_relations[field_name].api_fields}

        return super(BaseSerializer, self).build_relational_field(field_name, relation_info)


class DocumentSerializer(BaseSerializer):
    meta = DocumentMetaField()


def get_serializer_class(model_, fields_, base=BaseSerializer):
    class Meta:
        model = model_
        fields = fields_

    return type(model_.__name__ + 'Serializer', (base, ), {
        'Meta': Meta
    })
