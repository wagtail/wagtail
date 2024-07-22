from django.db.models import Model
from django.utils.html import escape

from wagtail.models import Page
from wagtail.rich_text import LinkHandler


class PageLinkHandler(LinkHandler):
    identifier = "page"

    @staticmethod
    def get_model():
        return Page

    @classmethod
    def get_many(cls, attrs_list: list[dict]) -> list[Model]:
        # Override LinkHandler.get_many to reduce database queries through the
        # use of PageQuerySet.specific() instead of QuerySet.in_bulk().
        instance_ids = [attrs.get("id") for attrs in attrs_list]
        qs = Page.objects.filter(id__in=instance_ids).defer_streamfields().specific()
        pages_by_str_id = {str(page.id): page for page in qs}
        return [pages_by_str_id.get(str(id_)) for id_ in instance_ids]

    @classmethod
    def expand_db_attributes(cls, attrs: dict) -> str:
        return cls.expand_db_attributes_many([attrs])[0]

    @classmethod
    def expand_db_attributes_many(cls, attrs_list: list[dict]) -> list[str]:
        return [
            '<a href="%s">' % escape(page.localized.url) if page else "<a>"
            for page in cls.get_many(attrs_list)
        ]

    @classmethod
    def extract_references(self, attrs):
        # Yields tuples of (content_type_id, object_id, model_path, content_path)
        yield Page, attrs["id"], "", ""
