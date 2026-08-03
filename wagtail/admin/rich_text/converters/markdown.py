"""
Markdown conversion rules for links, with two modes for public rendering and internal with references preserved.
"""

from draftjs_exporter.markdown.helpers import inline


def link_markdown(props):
    """Render a link as a public Markdown inline reference.

    When the referenced page has been deleted (``url`` is ``None``), renders
    a visible ``[broken link: …]`` marker instead of a link to ``#``, which
    would look functional but go nowhere useful.
    """
    url = props.get("url")
    if url:
        return inline(["[", props["children"], "](", url, ")"])
    return inline(["[broken link: ", props["children"], "]"])


def link_markdown_internal(props):
    """Render a link as an internal Markdown reference.

    Page links (entity data includes ``id``) use ``wagtail://page?id=<id>`` so
    the reference can be resolved back to the page. Other links (external,
    anchor, email) have no internal identifier and use the URL directly.
    """
    page_id = props.get("id")
    if page_id is not None:
        url = f"wagtail://page?id={page_id}"
    else:
        url = props.get("url") or "#"
    return inline(["[", props["children"], "](", url, ")"])


MarkdownLinkConversionRule = {
    "entity_decorators": {"LINK": link_markdown},
}

MarkdownInternalLinkConversionRule = {
    "entity_decorators": {"LINK": link_markdown_internal},
}
