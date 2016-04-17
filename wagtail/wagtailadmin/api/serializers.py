from __future__ import absolute_import, unicode_literals

from collections import OrderedDict

from rest_framework.fields import Field

from wagtail.api.v2.serializers import ImageSerializer, PageSerializer
from wagtail.api.v2.utils import get_full_url
from wagtail.wagtailcore.models import Page
from wagtail.wagtailimages.models import SourceImageIOError


def get_model_listing_url(context, model):
    url_path = context['router'].get_model_listing_urlpath(model)

    if url_path:
        return get_full_url(context['request'], url_path)


class PageStatusField(Field):
    """
    Serializes the "status" field.

    Example:
    "status": {
        "status": "live",
        "live": true,
        "has_unpublished_changes": false
    },
    """
    def get_attribute(self, instance):
        return instance

    def to_representation(self, page):
        return OrderedDict([
            ('status', page.status_string),
            ('live', page.live),
            ('has_unpublished_changes', page.has_unpublished_changes),
        ])


class PageChildrenField(Field):
    """
    Serializes the "children" field.

    Example:
    "children": {
        "count": 1,
        "listing_url": "/api/v1/pages/?child_of=2"
    }
    """
    def get_attribute(self, instance):
        return instance

    def to_representation(self, page):
        return OrderedDict([
            ('count', page.numchild),
            ('listing_url', get_model_listing_url(self.context, Page) + '?child_of=' + str(page.id)),
        ])


class AdminPageSerializer(PageSerializer):
    status = PageStatusField(read_only=True)
    children = PageChildrenField(read_only=True)

    meta_fields = PageSerializer.meta_fields + [
        'status',
        'children',
    ]


class ImageRenditionField(Field):
    """
    A field that generates a rendition with the specified filter spec, and serialises
    details of that rendition.

    Example:
    "thumbnail": {
        "url": "/media/images/myimage.max-165x165.jpg",
        "width": 165,
        "height": 100
    }

    If there is an error with the source image. The dict will only contain a single
    key, "error", indicating this error:

    "thumbnail": {
        "error": "SourceImageIOError"
    }
    """
    def __init__(self, filter_spec, *args, **kwargs):
        self.filter_spec = filter_spec
        super(ImageRenditionField, self).__init__(*args, **kwargs)

    def get_attribute(self, instance):
        return instance

    def to_representation(self, image):
        try:
            thumbnail = image.get_rendition(self.filter_spec)

            return OrderedDict([
                ('url', thumbnail.url),
                ('width', thumbnail.width),
                ('height', thumbnail.height),
            ])
        except SourceImageIOError:
            return OrderedDict([
                ('error', 'SourceImageIOError'),
            ])


class AdminImageSerializer(ImageSerializer):
    thumbnail = ImageRenditionField('max-165x165', read_only=True)
