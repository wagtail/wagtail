from __future__ import absolute_import

from collections import OrderedDict

from modelcluster.models import get_all_child_relations

from taggit.managers import _TaggableManager

from rest_framework import serializers
from rest_framework.fields import Field
from rest_framework.relations import RelatedField

from wagtail.utils.compat import get_related_model
from wagtail.wagtailcore import fields as wagtailcore_fields

from .utils import ObjectDetailURL, URLPath, pages_for_site


class ChildRelationField(Field):
    def __init__(self, *args, **kwargs):
        self.child_fields = kwargs.pop('child_fields')
        super(ChildRelationField, self).__init__(*args, **kwargs)

    def to_representation(self, value):
        serializer_class = get_serializer_class(value.model, self.child_fields)
        serializer = serializer_class()

        return [
            serializer.serialize_fields(child_object)
            for child_object in value.all()
        ]


class RelatedObjectField(RelatedField):
    def to_representation(self, value):
        model = type(value)

        return OrderedDict([
            ('id', value.pk),
            ('meta', OrderedDict([
                 ('type', model._meta.app_label + '.' + model.__name__),
                 ('detail_url', ObjectDetailURL(model, value.pk)),
            ])),
        ])


class StreamField(Field):
    def to_representation(self, value):
        return value.stream_block.get_prep_value(value)


class TagsField(Field):
    def to_representation(self, value):
        return list(value.all().values_list('name', flat=True))


class BaseSerializer(serializers.ModelSerializer):
    # Add StreamField to serializer_field_mapping
    serializer_field_mapping = serializers.ModelSerializer.serializer_field_mapping.copy()
    serializer_field_mapping.update({
        wagtailcore_fields.StreamField: StreamField,
    })
    serializer_related_field = RelatedObjectField

    def build_property_field(self, field_name, model_class):
        # TaggableManager is not a Django field so it gets treated as a property
        field = getattr(model_class, field_name)
        if isinstance(field, _TaggableManager):
            return TagsField, {}

        return super(BaseSerializer, self).build_property_field(field_name, model_class)

    def serialize_meta(self, obj):
        """
        This returns a JSON-serialisable dict to use for the "meta"
        section of a particlular object.
        """
        data = OrderedDict()

        # Add type
        data['type'] = type(obj)._meta.app_label + '.' + type(obj).__name__
        data['detail_url'] = ObjectDetailURL(type(obj), obj.pk)

        return data

    def serialize_fields(self, obj):
        # Call rest frameworks built in to_representation method
        return super(BaseSerializer, self).to_representation(obj)

    def to_representation(self, obj):
        """
        This converts an object into JSON-serialisable dict so it can
        be used in the API.
        """
        data = [
            ('id', obj.id),
        ]

        # Serialize meta
        metadata = self.serialize_meta(obj)
        if metadata:
            data.append(('meta', metadata))

        # Serialize fields
        data.extend(self.serialize_fields(obj).items())

        return OrderedDict(data)


class PageSerializer(BaseSerializer):
    def serialize_meta(self, page):
        data = super(PageSerializer, self).serialize_meta(page)

        # Add type
        data['type'] = page.specific_class._meta.app_label + '.' + page.specific_class.__name__

        return data

    def serialize_fields(self, page):
        data = list(super(PageSerializer, self).serialize_fields(page).items())

        # Add parent field to the beginning
        if self.context.get('show_details', False):
            parent = page.get_parent()

            site_pages = pages_for_site(self.context['request'].site)
            if site_pages.filter(id=parent.id).exists():
                parent_class = parent.specific_class

                data.insert(0,
                    ('parent', OrderedDict([
                        ('id', parent.id),
                        ('meta', OrderedDict([
                             ('type', parent_class._meta.app_label + '.' + parent_class.__name__),
                             ('detail_url', ObjectDetailURL(parent_class, parent.id)),
                        ])),
                    ]))
                )

        return OrderedDict(data)

    def build_relational_field(self, field_name, relation_info):
        if relation_info.to_many:
            # Find child relations
            model = getattr(self.Meta, 'model')
            child_relations = {
                child_relation.field.rel.related_name: get_related_model(child_relation)
                for child_relation in get_all_child_relations(model)
            }

            # Check child relations
            if field_name in child_relations and hasattr(child_relations[field_name], 'api_fields'):
                return ChildRelationField, {'child_fields': child_relations[field_name].api_fields}

        return super(BaseSerializer, self).build_relational_field(field_name, relation_info)


class DocumentSerializer(BaseSerializer):
    def serialize_meta(self, document):
        data = super(DocumentSerializer, self).serialize_meta(document)

        # Download URL
        if self.context.get('show_details', False):
            data['download_url'] = URLPath(document.url)

        return data


def get_serializer_class(model_, fields_, base=BaseSerializer):
    class Meta:
        model = model_
        fields = fields_

    return type(model_.__name__ + 'Serializer', (base, ), {
        'Meta': Meta
    })
