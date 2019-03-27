from django.utils.html import escape

from wagtail.admin.rich_text.converters import editor_html
from wagtail.documents.models import get_document_model


# hallo.js / editor-html conversion

class DocumentLinkHandler:
    @staticmethod
    def get_db_attributes(tag):
        return {'id': tag['data-id']}

    @staticmethod
    def expand_db_attributes(attrs):
        Document = get_document_model()
        try:
            doc = Document.objects.get(id=attrs['id'])
            return '<a data-linktype="document" data-id="%d" href="%s">' % (doc.id, escape(doc.url))
        except Document.DoesNotExist:
            # Preserve the ID attribute for troubleshooting purposes, even though it
            # points to a missing document
            return '<a data-linktype="document" data-id="%s">' % attrs['id']
        except KeyError:
            return '<a data-linktype="document">'


EditorHTMLDocumentLinkConversionRule = [
    editor_html.LinkTypeRule('document', DocumentLinkHandler),
]
