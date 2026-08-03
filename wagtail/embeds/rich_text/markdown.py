"""
Markdown conversion rules for media embeds (``EMBED`` Draft.js entity).

Two rendering modes are supported:

- ``MarkdownMediaEmbedConversionRule`` (public): render the embed's frontend
  HTML inline within the Markdown. CommonMark permits raw HTML blocks, so
  the same HTML produced by :func:`wagtail.embeds.format.embed_to_frontend_html`
  is preserved as-is — no extra wrapping markup. When the embed cannot be
  resolved, renders a visible ``[broken embed: …]`` marker.

- ``MarkdownInternalMediaEmbedConversionRule`` (internal): render an image-like
  reference ``![](wagtail://media?url=<url-encoded-source>)`` so the embed can
  be resolved back to its source URL. The source URL is percent-encoded to keep
  the CommonMark link destination well-formed for any input.
"""

from urllib.parse import quote

from draftjs_exporter.dom import DOM
from draftjs_exporter.markdown.helpers import block

from wagtail.embeds import format as embed_format
from wagtail.embeds.exceptions import EmbedException

__all__ = [
    "MarkdownMediaEmbedConversionRule",
    "MarkdownInternalMediaEmbedConversionRule",
    "media_embed_markdown",
    "media_embed_markdown_internal",
]


def media_embed_markdown(props):
    """Render a media embed as its frontend HTML, inline in the Markdown.

    When the embed cannot be resolved (``EmbedException`` or missing URL),
    renders a visible ``[broken embed: …]`` marker instead of silently
    producing empty output.
    """
    url = props.get("url")
    if not url:
        return block(["[broken embed]"])
    try:
        html = embed_format.embed_to_frontend_html(url)
    except EmbedException:
        return block(["[broken embed: ", url, "]"])
    # ``DOM.parse_html`` returns an "escaped_html" element rendered verbatim
    # by the Markdown engine — raw HTML inside Markdown is valid CommonMark.
    return block([DOM.parse_html(html)])


def media_embed_markdown_internal(props):
    """Render a media embed as an internal Markdown image reference.

    The embed source URL is percent-encoded so any character (including
    parentheses) can survive a Markdown link destination round-trip.
    """
    url = props.get("url") or ""
    encoded = quote(url, safe="")
    return block(["![](wagtail://media?url=", encoded, ")"])


MarkdownMediaEmbedConversionRule = {
    "entity_decorators": {"EMBED": media_embed_markdown},
}

MarkdownInternalMediaEmbedConversionRule = {
    "entity_decorators": {"EMBED": media_embed_markdown_internal},
}
