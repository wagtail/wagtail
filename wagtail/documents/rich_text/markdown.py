"""
Markdown conversion rules for documents, with two modes for public rendering and internal with references preserved.
"""

from draftjs_exporter.markdown.helpers import inline


def document_link_markdown(props):
    """Render a document link as a public Markdown reference.

    When the referenced document has been deleted (``url`` is missing),
    renders a visible ``[broken document link: …]`` marker instead of a link
    to ``#``, which would look functional but go nowhere useful.
    """
    url = props.get("url")
    if url:
        return inline(["[", props["children"], "](", url, ")"])
    return inline(["[broken document link: ", props["children"], "]"])


def document_link_markdown_internal(props):
    """Render a document link as an internal Markdown reference.

    Falls back to the stored ``url`` when the entity has no ``id`` (for
    broken references where the document was deleted between save and
    render time).
    """
    document_id = props.get("id")
    if document_id is not None:
        url = f"wagtail://document?id={document_id}"
    else:
        url = props.get("url") or "#"
    return inline(["[", props["children"], "](", url, ")"])


MarkdownDocumentLinkConversionRule = {
    "entity_decorators": {"DOCUMENT": document_link_markdown},
}

MarkdownInternalDocumentLinkConversionRule = {
    "entity_decorators": {"DOCUMENT": document_link_markdown_internal},
}
