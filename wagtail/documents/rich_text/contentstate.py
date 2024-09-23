"""
Draftail / contentstate conversion
"""
from draftjs_exporter.dom import DOM

from wagtail.admin.rich_text.converters.html_to_contentstate import LinkElementHandler
from wagtail.documents import get_document_model


def document_link_entity(props):
    """
    Helper to construct elements of the form
    <a id="1" linktype="document">document link</a>
    when converting from contentstate data
    """

    return DOM.create_element(
        "a",
        {
            "linktype": "document",
            "id": props.get("id"),
        },
        props["children"],
    )


class DocumentLinkElementHandler(LinkElementHandler):
    """
    Rule for populating the attributes of a document link when converting from database representation
    to contentstate
    """

    def get_attribute_data(self, attrs):
        Document = get_document_model()
        try:
            id = int(attrs["id"])
        except (KeyError, ValueError):
            return {}

        try:
            doc = Document.objects.get(id=id)
        except Document.DoesNotExist:
            return {"id": id}

        return {
            "id": doc.id,
            "url": doc.url,
            "filename": doc.filename,
        }


ContentstateDocumentLinkConversionRule = {
    "from_database_format": {
        'a[linktype="document"]': DocumentLinkElementHandler("DOCUMENT"),
    },
    "to_database_format": {"entity_decorators": {"DOCUMENT": document_link_entity}},
}
