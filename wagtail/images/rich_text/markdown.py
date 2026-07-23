"""
Markdown conversion rules for images (``IMAGE`` Draft.js entity).

The contentstate handler (:mod:`wagtail.images.rich_text.contentstate`)
stores ``id``, ``src`` (the rendition URL captured at save time), ``alt`` and
``format`` on each image entity. The decorators below render the same entity
as Markdown:

- ``MarkdownImageConversionRule`` (public): use the rendition ``src`` URL.
  When the image has been deleted (``src`` is empty), renders a visible
  ``[broken image: …]`` marker instead of a silent ``![alt]()``.
- ``MarkdownInternalImageConversionRule`` (internal): use
  ``wagtail://image?id=<id>&alt=<alt>&format=<format>`` so the reference can
  be resolved back to the image and the DB HTML reconstructed. The ``src``
  attribute is intentionally omitted — it is derived from the image rendition
  at render time, not stored in the database.
"""

from urllib.parse import urlencode

from draftjs_exporter.markdown.helpers import block

__all__ = [
    "MarkdownImageConversionRule",
    "MarkdownInternalImageConversionRule",
    "image_markdown",
    "image_markdown_internal",
]


def image_markdown(props):
    """Render an image as a public Markdown image reference.

    When the referenced image has been deleted (``src`` is empty), renders a
    visible ``[broken image: …]`` marker instead of ``![alt]()``, which silently
    renders nothing in most Markdown renderers.
    """
    alt = props.get("alt") or ""
    src = props.get("src") or ""
    if src:
        return block(["![", alt, "](", src, ")"])
    if alt:
        return block(["[broken image: ", alt, "]"])
    return block(["[broken image]"])


def image_markdown_internal(props):
    """Render an image as an internal Markdown reference.

    Preserves the DB HTML attributes (``id``, ``alt``, ``format``) as query
    parameters so the reference can be resolved back to the image and the
    DB HTML reconstructed. Falls back to the stored ``src`` when the entity
    has no ``id`` (for example, broken references where the image was deleted
    between save and render time).
    """
    alt = props.get("alt") or ""
    image_id = props.get("id")
    if image_id is not None:
        # Preserve all DB HTML attributes that are not derived data.
        query = {"id": image_id}
        if props.get("alt") is not None:
            query["alt"] = props["alt"]
        if props.get("format") is not None:
            query["format"] = props["format"]
        src = f"wagtail://image?{urlencode(query)}"
    else:
        src = props.get("src") or ""
    return block(["![", alt, "](", src, ")"])


MarkdownImageConversionRule = {
    "entity_decorators": {"IMAGE": image_markdown},
}

MarkdownInternalImageConversionRule = {
    "entity_decorators": {"IMAGE": image_markdown_internal},
}
