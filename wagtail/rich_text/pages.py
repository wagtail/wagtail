from django.utils.html import escape

from wagtail.models import Page
from wagtail.rich_text import LinkHandler


class PageLinkHandler(LinkHandler):
    identifier = "page"

    @staticmethod
    def get_model():
        return Page

    def expand_db_attributes(cls, attrs):
        return cls.expand_db_attributes_many([attrs])[0]

    def expand_db_attributes_many(cls, attrs_list):
        return [
            '<a href="%s">' % escape(page.localized.specific.url) if page else "<a>"
            for page in cls.get_many(attrs_list)
        ]

    @classmethod
    def extract_references(self, attrs):
        # Yields tuples of (content_type_id, object_id, model_path, content_path)
        yield Page, attrs["id"], "", ""
