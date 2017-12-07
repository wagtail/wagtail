from django.utils.html import escape

from wagtail.documents.models import get_document_model


class DocumentLinkHandler:
    @staticmethod
    def get_db_attributes(tag):
        return {'id': tag['data-id']}

    @staticmethod
    def expand_db_attributes_for_editor(attrs):
        Document = get_document_model()
        try:
            doc = Document.objects.get(id=attrs['id'])
            return '<a data-linktype="document" data-id="%d" href="%s">' % (doc.id, escape(doc.url))
        except Document.DoesNotExist:
            return "<a>"


def document_linktype_handler(attrs):
    Document = get_document_model()
    try:
        doc = Document.objects.get(id=attrs['id'])
        return '<a href="%s">' % escape(doc.url)
    except Document.DoesNotExist:
        return "<a>"
