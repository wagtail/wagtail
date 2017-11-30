from collections import OrderedDict

from rest_framework.fields import Field, ReadOnlyField

from wagtail.api.v2.serializers import PageSerializer
from wagtail.api.v2.utils import get_full_url
from wagtail.core.models import Page


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


class PageDescendantsField(Field):
    """
    Serializes the "descendants" field.

    Example:
    "descendants": {
        "count": 10,
        "listing_url": "/api/v1/pages/?descendant_of=2"
    }
    """
    def get_attribute(self, instance):
        return instance

    def to_representation(self, page):
        return OrderedDict([
            ('count', page.get_descendants().count()),
            ('listing_url', get_model_listing_url(self.context, Page) + '?descendant_of=' + str(page.id)),
        ])


class AdminPageSerializer(PageSerializer):
    status = PageStatusField(read_only=True)
    children = PageChildrenField(read_only=True)
    descendants = PageDescendantsField(read_only=True)
    admin_display_title = ReadOnlyField(source='get_admin_display_title')
