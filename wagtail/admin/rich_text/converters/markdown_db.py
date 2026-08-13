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

import re
from urllib.parse import quote, urlencode

from draftjs_exporter import (
    BLOCK_TYPES,
    DOM,
    ENTITY_TYPES,
    INLINE_STYLES,
    MarkdownImporter,
    scheme_resolver,
)
from draftjs_exporter import HTML as HTMLExporter
from draftjs_exporter.defaults import render_children

from wagtail.admin.rich_text.converters.contentstate import br
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
        """Convert Markdown to unsanitised DB HTML."""
        content_state = _importer().import_markdown(markdown)
        return _db_html_exporter().render(content_state)

    # from_database_format arrives with the API output formats.


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
