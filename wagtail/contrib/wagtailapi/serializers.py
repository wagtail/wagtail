from __future__ import absolute_import

from collections import OrderedDict

from modelcluster.models import get_all_child_relations

from taggit.managers import _TaggableManager

from rest_framework import serializers
from rest_framework.fields import Field
from rest_framework.relations import RelatedField

from wagtail.utils.compat import get_related_model
from wagtail.wagtailcore.models import Page
from wagtail.wagtailcore import fields as wagtailcore_fields

from .utils import ObjectDetailURL, URLPath, BadRequestError, pages_for_site


class ChildRelationField(Field):
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

    def build_relational_field(self, field_name, relation_info):
        if relation_info.to_many:
            # Find child relations (pages only)
            model = getattr(self.Meta, 'model')
            child_relations = {}
            if issubclass(model, Page):
                child_relations = {
                    child_relation.field.rel.related_name: get_related_model(child_relation)
                    for child_relation in get_all_child_relations(model)
                }

            # Check child relations
            if field_name in child_relations and hasattr(child_relations[field_name], 'api_fields'):
                return ChildRelationField, {'child_fields': child_relations[field_name].api_fields}

        return super(BaseSerializer, self).build_relational_field(field_name, relation_info)


def get_serializer_class(model_, fields_):
    class Meta:
        model = model_
        fields = fields_

    return type(model_.__name__ + 'Serializer', (BaseSerializer, ), {
        'Meta': Meta
    })


class WagtailSerializer(serializers.BaseSerializer):
    def to_representation(self, instance):
        fields = self.context.get('fields', frozenset())
        all_fields = self.context.get('all_fields', False)
        return self.serialize_object(
            instance,
            fields=fields,
            all_fields=all_fields,
        )

    def serialize_object_metadata(self, obj):
        """
        This returns a JSON-serialisable dict to use for the "meta"
        section of a particlular object.
        """
        data = OrderedDict()

        # Add type
        data['type'] = type(obj)._meta.app_label + '.' + type(obj).__name__
        data['detail_url'] = ObjectDetailURL(type(obj), obj.pk)

        return data

    def serialize_object(self, obj, fields=frozenset(), extra_data=(), all_fields=False):
        """
        This converts an object into JSON-serialisable dict so it can
        be used in the API.
        """
        data = [
            ('id', obj.id),
        ]

        # Add meta
        metadata = self.serialize_object_metadata(obj)
        if metadata:
            data.append(('meta', metadata))

        # Add extra data
        data.extend(extra_data)

        # Add other fields
        api_fields = self.context['view'].get_api_fields(type(obj))
        api_fields = list(OrderedDict.fromkeys(api_fields)) # Removes any duplicates in case the user put "title" in api_fields

        if all_fields:
            fields = api_fields
        else:
            unknown_fields = fields - set(api_fields)

            if unknown_fields:
                raise BadRequestError("unknown fields: %s" % ', '.join(sorted(unknown_fields)))

            # Reorder fields so it matches the order of api_fields
            fields = [field for field in api_fields if field in fields]

        # Serialize the fields
        serializer_class = get_serializer_class(type(obj), fields)
        serializer = serializer_class()
        data.extend(serializer.to_representation(obj).items())

        return OrderedDict(data)


class PageSerializer(WagtailSerializer):
    def serialize_object_metadata(self, page):
        data = super(PageSerializer, self).serialize_object_metadata(page)

        # Add type
        data['type'] = page.specific_class._meta.app_label + '.' + page.specific_class.__name__

        return data

    def serialize_object(self, page, fields=frozenset(), extra_data=(), all_fields=False):
        # Add parent
        if self.context.get('show_details', False):
            parent = page.get_parent()

            site_pages = pages_for_site(self.context['request'].site)
            if site_pages.filter(id=parent.id).exists():
                parent_class = parent.specific_class

                extra_data += (
                    ('parent', OrderedDict([
                        ('id', parent.id),
                        ('meta', OrderedDict([
                             ('type', parent_class._meta.app_label + '.' + parent_class.__name__),
                             ('detail_url', ObjectDetailURL(parent_class, parent.id)),
                        ])),
                    ])),
                )

        return super(PageSerializer, self).serialize_object(page, fields=fields, extra_data=extra_data, all_fields=all_fields)


class DocumentSerializer(WagtailSerializer):
    def serialize_object_metadata(self, document):
        data = super(DocumentSerializer, self).serialize_object_metadata(document)

        # Download URL
        if self.context.get('show_details', False):
            data['download_url'] = URLPath(document.url)

        return data
