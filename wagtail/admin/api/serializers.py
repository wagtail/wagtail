from collections import OrderedDict

from rest_framework.fields import Field, ReadOnlyField

from wagtail.api.v2.serializers import PageSerializer, get_serializer_class
from wagtail.api.v2.utils import get_full_url
from wagtail.models import Page


def get_model_listing_url(context, model):
    url_path = context["router"].get_model_listing_urlpath(model)

    if url_path:
        return get_full_url(context["request"], url_path)


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
        return OrderedDict(
            [
                ("status", page.status_string),
                ("live", page.live),
                ("has_unpublished_changes", page.has_unpublished_changes),
            ]
        )


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
        return OrderedDict(
            [
                ("count", self.context["base_queryset"].child_of(page).count()),
                (
                    "listing_url",
                    get_model_listing_url(self.context, Page)
                    + "?child_of="
                    + str(page.id),
                ),
            ]
        )


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
        return OrderedDict(
            [
                ("count", self.context["base_queryset"].descendant_of(page).count()),
                (
                    "listing_url",
                    get_model_listing_url(self.context, Page)
                    + "?descendant_of="
                    + str(page.id),
                ),
            ]
        )


class PageAncestorsField(Field):
    """
    Serializes the page's ancestry.

    Example:
    "ancestry": [
        {
            "id": 1,
            "meta": {
                "type": "wagtailcore.Page",
                "detail_url": "/api/v1/pages/1/"
            },
            "title": "Root"
        },
        {
            "id": 2,
            "meta": {
                "type": "home.HomePage",
                "detail_url": "/api/v1/pages/2/"
            },
            "title": "Home"
        }
    ]
    """

    def get_attribute(self, instance):
        return instance

    def to_representation(self, page):
        serializer_class = get_serializer_class(
            Page,
            ["id", "type", "detail_url", "html_url", "title", "admin_display_title"],
            meta_fields=["type", "detail_url", "html_url"],
            base=AdminPageSerializer,
        )
        serializer = serializer_class(context=self.context, many=True)
        return serializer.to_representation(page.get_ancestors())


class PageTranslationsField(Field):
    """
    Serializes the page's translations.

    Example:
    "translations": [
        {
            "id": 1,
            "meta": {
                "type": "home.HomePage",
                "detail_url": "/api/v1/pages/1/",
                "locale": "es"
            },
            "title": "Casa"
        },
        {
            "id": 2,
            "meta": {
                "type": "home.HomePage",
                "detail_url": "/api/v1/pages/2/",
                "locale": "fr"
            },
            "title": "Maison"
        }
    ]
    """

    def get_attribute(self, instance):
        return instance

    def to_representation(self, page):
        serializer_class = get_serializer_class(
            Page,
            [
                "id",
                "type",
                "detail_url",
                "html_url",
                "locale",
                "title",
                "admin_display_title",
            ],
            meta_fields=["type", "detail_url", "html_url", "locale"],
            base=AdminPageSerializer,
        )
        serializer = serializer_class(context=self.context, many=True)
        return serializer.to_representation(page.get_translations())


class AdminPageSerializer(PageSerializer):
    status = PageStatusField(read_only=True)
    children = PageChildrenField(read_only=True)
    descendants = PageDescendantsField(read_only=True)
    ancestors = PageAncestorsField(read_only=True)
    translations = PageTranslationsField(read_only=True)
    admin_display_title = ReadOnlyField(source="get_admin_display_title")
