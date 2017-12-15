from wagtail.core.rich_text import LinkHandler
from wagtail.documents.models import get_document_model


class DocumentLinkHandler(LinkHandler):
    name = 'document'

    @staticmethod
    def get_model():
        return get_document_model()

    @staticmethod
    def get_db_attributes(tag):
        return {'id': tag['data-id']}

    @classmethod
    def get_html_attributes(cls, instance, for_editor):
        attrs = super().get_html_attributes(instance, for_editor)
        attrs['href'] = instance.url
        return attrs
