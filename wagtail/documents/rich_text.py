from django.utils.html import escape
from draftjs_exporter.dom import DOM

from wagtail.admin.rich_text.converters import editor_html
from wagtail.admin.rich_text.converters.html_to_contentstate import LinkElementHandler
from wagtail.documents.models import get_document_model


# Front-end conversion

def document_linktype_handler(attrs):
    Document = get_document_model()
    try:
        doc = Document.objects.get(id=attrs['id'])
        return '<a href="%s">' % escape(doc.url)
    except (Document.DoesNotExist, KeyError):
        return "<a>"


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


# draft.js / contentstate conversion

def document_link_entity(props):
    """
    Helper to construct elements of the form
    <a id="1" linktype="document">document link</a>
    when converting from contentstate data
    """

    return DOM.create_element('a', {
        'linktype': 'document',
        'id': props.get('id'),
    }, props['children'])


class DocumentLinkElementHandler(LinkElementHandler):
    """
    Rule for populating the attributes of a document link when converting from database representation
    to contentstate
    """
    def get_attribute_data(self, attrs):
        Document = get_document_model()
        try:
            id = int(attrs['id'])
        except (KeyError, ValueError):
            return {}

        try:
            doc = Document.objects.get(id=id)
        except Document.DoesNotExist:
            return {'id': id}

        return {
            'id': doc.id,
            'url': doc.url,
            'filename': doc.filename,
        }


ContentstateDocumentLinkConversionRule = {
    'from_database_format': {
        'a[linktype="document"]': DocumentLinkElementHandler('DOCUMENT'),
    },
    'to_database_format': {
        'entity_decorators': {'DOCUMENT': document_link_entity}
    }
}
