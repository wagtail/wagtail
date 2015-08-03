from __future__ import absolute_import

from collections import OrderedDict

from django.db import models

from modelcluster.models import get_all_child_relations

from taggit.managers import TaggableManager

from rest_framework.serializers import BaseSerializer
from rest_framework.fields import Field, ReadOnlyField

from wagtail.utils.compat import get_related_model
from wagtail.wagtailcore.models import Page
from wagtail.wagtailcore import fields as wagtailcore_fields

from .utils import ObjectDetailURL, URLPath, BadRequestError, pages_for_site


class ChildRelationField(Field):
    def __init__(self, *args, **kwargs):
        self.child_fields = kwargs.pop('child_fields')
        super(ChildRelationField, self).__init__(*args, **kwargs)

    def to_representation(self, value):
        return [
            dict(get_api_data(child_object, self.child_fields))
            for child_object in value.all()
        ]


class RelatedObjectField(Field):
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


def get_serializer_fields(model, fields):
    # Find any child relations (pages only)
    child_relations = {}
    if issubclass(model, Page):
        child_relations = {
            child_relation.field.rel.related_name: get_related_model(child_relation)
            for child_relation in get_all_child_relations(model)
        }

    # Loop through fields
    for field_name in fields:
        # Check child relations
        if field_name in child_relations and hasattr(child_relations[field_name], 'api_fields'):
            yield field_name, ChildRelationField, {'child_fields': child_relations[field_name].api_fields}
            continue

        # Check django fields
        try:
            field = model._meta.get_field(field_name)

            if field.rel and isinstance(field.rel, models.ManyToOneRel):
                yield field_name, RelatedObjectField, {}
            elif isinstance(field, wagtailcore_fields.StreamField):
                yield field_name, StreamField, {}
            elif isinstance(field, TaggableManager):
                yield field_name, TagsField, {}
            else:
                yield field_name, ReadOnlyField, {}

            continue
        except models.fields.FieldDoesNotExist:
            pass

        # Check attributes
        if hasattr(model, field_name):
            yield field_name, ReadOnlyField, {}
            continue


def get_api_data(obj, fields):
    serializer_fields = get_serializer_fields(type(obj), fields)

    for field_name, field_class, field_kwargs in serializer_fields:
        field = field_class(**field_kwargs)
        field.bind(field_name, None)

        value = field.get_attribute(obj)

        if value is not None:
            yield field.field_name, field.to_representation(value)
        else:
            yield field.field_name, None


class WagtailSerializer(BaseSerializer):
    def to_representation(self, instance):
        request = self.context['request']
        fields = self.context.get('fields', frozenset())
        all_fields = self.context.get('all_fields', False)
        show_details = self.context.get('show_details', False)
        return self.serialize_object(
            request,
            instance,
            fields=fields,
            all_fields=all_fields,
            show_details=show_details
        )

    def serialize_object_metadata(self, request, obj, show_details=False):
        """
        This returns a JSON-serialisable dict to use for the "meta"
        section of a particlular object.
        """
        data = OrderedDict()

        # Add type
        data['type'] = type(obj)._meta.app_label + '.' + type(obj).__name__
        data['detail_url'] = ObjectDetailURL(type(obj), obj.pk)

        return data

    def serialize_object(self, request, obj, fields=frozenset(), extra_data=(), all_fields=False, show_details=False):
        """
        This converts an object into JSON-serialisable dict so it can
        be used in the API.
        """
        data = [
            ('id', obj.id),
        ]

        # Add meta
        metadata = self.serialize_object_metadata(request, obj, show_details=show_details)
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

        data.extend(get_api_data(obj, fields))

        return OrderedDict(data)


class PageSerializer(WagtailSerializer):
    def serialize_object_metadata(self, request, page, show_details=False):
        data = super(PageSerializer, self).serialize_object_metadata(request, page, show_details=show_details)

        # Add type
        data['type'] = page.specific_class._meta.app_label + '.' + page.specific_class.__name__

        return data

    def serialize_object(self, request, page, fields=frozenset(), extra_data=(), all_fields=False, show_details=False):
        # Add parent
        if show_details:
            parent = page.get_parent()

            site_pages = pages_for_site(request.site)
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

        return super(PageSerializer, self).serialize_object(request, page, fields=fields, extra_data=extra_data, all_fields=all_fields, show_details=show_details)


class DocumentSerializer(WagtailSerializer):
    def serialize_object_metadata(self, request, document, show_details=False):
        data = super(DocumentSerializer, self).serialize_object_metadata(request, document, show_details=show_details)

        # Download URL
        if show_details:
            data['download_url'] = URLPath(document.url)

        return data
