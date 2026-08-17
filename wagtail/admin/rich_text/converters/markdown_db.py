"""
ContentState-mediated conversion between Markdown and Wagtail's database-HTML
rich text format, for the API's `db_markdown` / `markdown` rich text formats.

Internal object references travel in Markdown as `wagtail://` URLs in link /
image destinations (see `REFERENCE_SCHEME`), resolved to Draft.js entities by
`scheme_resolver` on input and rendered back by custom entity decorators on
output. Feature enforcement is NOT done here: input callers must pass the
resulting DB HTML through `APIRichText.sanitize_db_html` (which enforces the
field's features and reports removals).
"""

import json
import re
from urllib.parse import quote, urlencode

from draftjs_exporter import (
    BLOCK_TYPES,
    DOM,
    ENTITY_TYPES,
    INLINE_STYLES,
    HTMLExporter,
    MarkdownImporter,
    MarkdownParseError,
    build_markdown_config,
    md_block,
    md_image,
    md_inline,
    md_link_destination,
    md_mark_safe,
    render_children,
    scheme_resolver,
)

from wagtail.admin.rich_text.converters.contentstate import (
    ContentstateConverter,
    br,
)
from wagtail.rich_text import features as feature_registry

REFERENCE_SCHEME = "wagtail"

# Entity types Wagtail's contentstate conversion uses that draftjs_exporter
# has no constant for.
ENTITY_TYPE_DOCUMENT = "DOCUMENT"
ENTITY_TYPE_MEDIA = "EMBED"


def wagtail_ref(kind, **params):
    """Build a `wagtail://kind?k=v` reference URL for Markdown destinations."""
    return f"{REFERENCE_SCHEME}://{kind}?{urlencode(params, quote_via=quote)}"


class MarkdownConverter:
    """Convert between Markdown and Wagtail DB HTML."""

    def __init__(self, features=None):
        self.features = (
            list(features)
            if features is not None
            else feature_registry.get_default_features()
        )

    def to_database_format(self, markdown):
        """Convert Markdown to unsanitised DB HTML.

        Raises ``MarkdownParseError`` for ``wagtail://`` references that are
        missing their required parameters (e.g. ``[x](wagtail://page)``).
        """
        content_state = _importer().import_markdown(markdown)
        _validate_entity_map(content_state)
        return _db_html_exporter().render(content_state)

    def from_database_format(self, html, *, resolved):
        """Convert DB HTML to Markdown.

        ``resolved=False`` preserves internal references as ``wagtail://``
        destinations (the ``db_markdown`` format); ``resolved=True`` emits
        public URLs (the ``markdown`` format, the analogue of
        ``expand_db_html``). Dangling references degrade to plain text in
        resolved mode (editor parity).
        """
        contentstate_json = ContentstateConverter(self.features).from_database_format(
            html
        )
        content_state = json.loads(contentstate_json)
        markdown = _markdown_exporter(resolved).render(content_state)
        # The contentstate conversion pads atomic blocks (images/embeds) at
        # the document edges with empty spacer paragraphs, which render as
        # stray blank lines. Normalise: no leading/trailing blank lines, one
        # trailing blank line while any content remains.
        markdown = markdown.strip("\n")
        return f"{markdown}\n\n" if markdown else ""


def _validate_entity_map(content_state):
    """Normalise imported entity data before rendering to DB HTML.

    Two checks, in this order:

    1. Validate references: a ``LINK`` entity with neither ``id`` nor
       ``url``, or a ``DOCUMENT`` entity with no ``id``, can only come from a
       ``wagtail://`` reference missing its parameter (external links always
       carry ``url`` from the default resolver). Reject with
       ``MarkdownParseError`` — the API layer renders it as 422 — rather than
       crashing the renderer or storing a meaningless reference.
    2. Drop empty-string data values (e.g. ``wagtail://image?format=``):
       an empty parameter means "absent", and must reach the whitelister as
       a missing attribute (removal + report) rather than being stored
       verbatim, where it would break every later output conversion.
    """
    for entity in content_state.get("entityMap", {}).values():
        entity_type = entity.get("type")
        data = entity.get("data") or {}
        if entity_type == ENTITY_TYPES.LINK:
            if "id" not in data and "url" not in data:
                raise MarkdownParseError("wagtail://page reference requires id")
            # LINK tolerates an empty url (`[x]()` → `<a href="">`); dropping
            # it here would make the data-less LINK crash the renderer.
            continue
        if entity_type == ENTITY_TYPE_DOCUMENT and "id" not in data:
            raise MarkdownParseError("wagtail://document reference requires id")
        if data:
            entity["data"] = {key: value for key, value in data.items() if value != ""}


def _importer():
    return MarkdownImporter(
        {
            "parser_config": {
                "link_resolvers": [
                    scheme_resolver(
                        REFERENCE_SCHEME,
                        {
                            "page": ENTITY_TYPES.LINK,
                            "document": ENTITY_TYPE_DOCUMENT,
                        },
                        coerce={"id": int},
                    ),
                ],
                "image_resolvers": [
                    scheme_resolver(
                        REFERENCE_SCHEME,
                        {"image": ENTITY_TYPES.IMAGE, "media": ENTITY_TYPE_MEDIA},
                        coerce={"id": int},
                        label_key="alt",
                        mutability="IMMUTABLE",
                    ),
                ],
                "inline_html_styles": {
                    "sup": INLINE_STYLES.SUPERSCRIPT,
                    "sub": INLINE_STYLES.SUBSCRIPT,
                },
            }
        }
    )


def _keep_children_block(props):
    # Unlike ContentstateConverter's deleting fallback, unknown blocks must
    # survive as text so the whitelister (never this layer) decides their fate.
    return DOM.create_element("p", {}, props["children"])


def _keep_children_style(props):
    return props["children"]


def _keep_children_entity(props):
    return props["children"]


def _db_html_exporter():
    exporter_config = {
        "block_map": {
            BLOCK_TYPES.UNSTYLED: "p",
            BLOCK_TYPES.ATOMIC: render_children,
            # Constructs the Markdown parser can produce that no core feature
            # registers: survive as elements so the whitelister can report them.
            BLOCK_TYPES.HEADER_FIVE: "h5",
            BLOCK_TYPES.HEADER_SIX: "h6",
            BLOCK_TYPES.CODE: "pre",
            BLOCK_TYPES.FALLBACK: _keep_children_block,
        },
        "style_map": {INLINE_STYLES.FALLBACK: _keep_children_style},
        "entity_decorators": {ENTITY_TYPES.FALLBACK: _keep_children_entity},
        "composite_decorators": [{"strategy": re.compile(r"\n"), "component": br}],
        "engine": DOM.STRING,
    }
    for feature in feature_registry.get_converter_features("contentstate"):
        rule = feature_registry.get_converter_rule("contentstate", feature)
        if rule is None:
            continue
        feature_config = rule["to_database_format"]
        exporter_config["block_map"].update(feature_config.get("block_map", {}))
        exporter_config["style_map"].update(feature_config.get("style_map", {}))
        exporter_config["entity_decorators"].update(
            feature_config.get("entity_decorators", {})
        )
    return HTMLExporter(exporter_config)


def _markdown_link(children, destination):
    return md_inline(
        [
            md_mark_safe("["),
            children,
            md_mark_safe("]("),
            md_link_destination(destination),
            md_mark_safe(")"),
        ]
    )


def _page_or_external_ref_link(props):
    id_ = props.get("id")
    if id_ is not None:
        return _markdown_link(props["children"], wagtail_ref("page", id=id_))
    return _markdown_link(props["children"], props.get("url") or "")


def _resolved_link(props):
    url = props.get("url")
    if not url:
        # Dangling references degrade to plain text (editor parity).
        return md_inline([props["children"]])
    return _markdown_link(props["children"], url)


def _document_ref_link(props):
    return _markdown_link(
        props["children"], wagtail_ref("document", id=props.get("id"))
    )


def _resolved_document_link(props):
    url = props.get("url")
    if not url:
        return md_inline([props["children"]])
    return _markdown_link(props["children"], url)


def _image_ref_image(props):
    return md_block(
        [
            md_mark_safe("!["),
            props.get("alt") or "",
            md_mark_safe("]("),
            md_link_destination(
                wagtail_ref(
                    "image", id=props.get("id"), format=props.get("format") or ""
                )
            ),
            md_mark_safe(")"),
        ]
    )


def _resolved_image(props):
    if props.get("src"):
        return md_image(props)
    return _image_ref_image(props)


def _media_ref_embed(props):
    label = props.get("title") or props.get("url") or ""
    return md_block(
        [
            md_mark_safe("!["),
            label,
            md_mark_safe("]("),
            md_link_destination(wagtail_ref("media", url=props.get("url") or "")),
            md_mark_safe(")"),
        ]
    )


def _resolved_media_embed(props):
    label = props.get("title") or props.get("url") or ""
    return md_block(
        [
            md_mark_safe("["),
            label,
            md_mark_safe("]("),
            md_link_destination(props.get("url") or ""),
            md_mark_safe(")"),
        ]
    )


def _markdown_exporter(resolved):
    config = build_markdown_config({"italic": "*", "strikethrough": "~~"})
    if resolved:
        config["entity_decorators"].update(
            {
                ENTITY_TYPES.LINK: _resolved_link,
                ENTITY_TYPE_DOCUMENT: _resolved_document_link,
                ENTITY_TYPES.IMAGE: _resolved_image,
                ENTITY_TYPE_MEDIA: _resolved_media_embed,
            }
        )
    else:
        config["entity_decorators"].update(
            {
                ENTITY_TYPES.LINK: _page_or_external_ref_link,
                ENTITY_TYPE_DOCUMENT: _document_ref_link,
                ENTITY_TYPES.IMAGE: _image_ref_image,
                ENTITY_TYPE_MEDIA: _media_ref_embed,
            }
        )
    return HTMLExporter(config)
