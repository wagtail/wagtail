from typing import List

from django.utils.html import escape

from wagtail.documents import get_document_model
from wagtail.rich_text import LinkHandler

# Front-end conversion


class DocumentLinkHandler(LinkHandler):
    identifier = "document"

    @staticmethod
    def get_model():
        return get_document_model()

    @classmethod
    def expand_db_attributes(cls, attrs: dict) -> str:
        return cls.expand_db_attributes_many([attrs])[0]

    @classmethod
    def expand_db_attributes_many(cls, attrs_list: List[dict]) -> List[str]:
        return [
            '<a href="%s">' % escape(doc.url) if doc else "<a>"
            for doc in cls.get_many(attrs_list)
        ]

    @classmethod
    def extract_references(cls, attrs):
        # Yields tuples of (content_type_id, object_id, model_path, content_path)
        yield cls.get_model(), attrs["id"], "", ""
