from draftjs_exporter.dom import DOM

from wagtail.admin.rich_text.converters import editor_html
from wagtail.admin.rich_text.converters.html_to_contentstate import LinkElementHandler
from wagtail.core.rich_text.feature_registry import LinkHandler
from wagtail.documents.models import get_document_model


# Front-end + hallo.js / editor-html conversions

class DocumentLinkHandler(LinkHandler):
    link_type = 'document'

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


EditorHTMLDocumentLinkConversionRule = [
    editor_html.LinkTypeRule(DocumentLinkHandler.link_type,
                             DocumentLinkHandler),
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
            doc = Document.objects.get(id=attrs['id'])
        except Document.DoesNotExist:
            return {}

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
