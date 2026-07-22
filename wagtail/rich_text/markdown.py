"""
Convert Wagtail database rich text HTML to Markdown.

The conversion uses the existing HTML-to-Draft.js ContentState pipeline
(``wagtail.admin.rich_text.converters.html_to_contentstate``) and the
``draftjs_exporter`` Markdown engine (``DOM.MARKDOWN``).

Two output modes are supported:

- ``internal=False`` (public Markdown): entity references are resolved to
  public URLs, equivalent to ``expand_db_html`` followed by Markdown
  rendering. Suitable for rendering for site visitors or feeding to
  Markdown-aware tools that should follow real links.

- ``internal=True`` (internal Markdown): entity references are preserved
  using a ``wagtail://`` URL scheme so they can be resolved back to CMS
  objects. Suitable for AI-assisted content workflows and round-trips
  back to DB HTML (input support is tracked separately in #14308).

Reference syntax for ``internal=True``:

==============  ===============================================
Entity          Internal Markdown form
==============  ===============================================
Page link       ``[Label](wagtail://page?id=<id>)``
Document link   ``[Label](wagtail://document?id=<id>)``
Image embed     ``![alt](wagtail://image?id=<id>&alt=<alt>&format=<format>)``
Media embed     ``![](wagtail://media?url=<url-encoded-source>)``
==============  ===============================================

Query-parameter syntax is used so all DB HTML attributes can be preserved:
internal Markdown carries exactly the attributes needed to reconstruct the
DB HTML tag. Derived data (such as rendition ``src`` URLs or page ``url``
captured at contentstate build time) is intentionally omitted — it can be
recomputed from the stored identifiers at render time.

Custom link and embed types can carry arbitrary attributes, e.g.
``wagtail://user?username=wagtail``.

External, anchor and email links are rendered the same way in both modes.
"""

from __future__ import annotations

import json

from draftjs_exporter import HTML, MARKDOWN_CONFIG
from draftjs_exporter.html import ExporterConfig

from wagtail.admin.rich_text.converters.html_to_contentstate import (
    HtmlToContentStateHandler,
)
from wagtail.rich_text import features as feature_registry

__all__ = ["MarkdownConverter", "expand_db_html_to_markdown"]


CONVERTER_RULE_PUBLIC = "markdown"
CONVERTER_RULE_INTERNAL = "markdown_internal"


class MarkdownConverter:
    """Convert Wagtail database rich text HTML to Markdown.

    The converter is transport-agnostic (no HTTP imports) and reusable for
    API v2 / v3 responses, template filters, copy-paste importers, llms.txt
    generation, and the :rfc:`115` write-API markdown input round-trip
    (input direction tracked separately in #14308).

    Construction is moderately expensive (it builds a Draft.js exporter from
    the configured feature set), so callers reusing the same converter for
    many values should construct it once rather than per call.
    """

    #: Converter rule name used by :class:`MarkdownConverter` for the active
    #: mode. Subclasses overriding the public/internal split can change this.
    converter_rule_name: str = CONVERTER_RULE_PUBLIC

    def __init__(self, features: list[str] | None = None, *, internal: bool = False):
        self.features = (
            features
            if features is not None
            else feature_registry.get_default_features()
        )
        self.internal = internal
        if internal:
            self.converter_rule_name = CONVERTER_RULE_INTERNAL

        self._html_to_contentstate_handler = HtmlToContentStateHandler(self.features)
        self._exporter = HTML(self._build_exporter_config())

    def _build_exporter_config(self) -> ExporterConfig:
        block_map = dict(MARKDOWN_CONFIG["block_map"])
        style_map = dict(MARKDOWN_CONFIG["style_map"])
        entity_decorators = dict(MARKDOWN_CONFIG["entity_decorators"])
        for feature in self.features:
            rule = feature_registry.get_converter_rule(
                self.converter_rule_name, feature
            )
            if rule is None:
                continue
            block_map.update(rule.get("block_map", {}))
            style_map.update(rule.get("style_map", {}))
            entity_decorators.update(rule.get("entity_decorators", {}))
        return {
            "block_map": block_map,
            "style_map": style_map,
            "entity_decorators": entity_decorators,
            "engine": MARKDOWN_CONFIG["engine"],
        }

    def from_database_format(self, html: str | None) -> str:
        """Convert Wagtail DB rich text HTML to a Markdown string.

        Returns an empty string for ``None`` or empty input, mirroring the
        behaviour of the ``|richtext`` template filter for missing values.
        """
        if not html:
            return ""

        handler = self._html_to_contentstate_handler
        handler.reset()
        handler.feed(html)
        handler.close()
        # ``ContentState.as_dict()`` returns the entityMap with integer keys,
        # but the Draft.js exporter expects string keys (matching the JSON
        # representation). Round-trip through JSON to normalise key types
        # and ensure feature parity with the editor's contentstate input.
        content_state = json.loads(handler.contentstate.as_json())
        return self._exporter.render(content_state)


def expand_db_html_to_markdown(
    html: str | None,
    *,
    internal: bool = False,
    features: list[str] | None = None,
) -> str:
    """Convert Wagtail database HTML to Markdown.

    Convenience wrapper mirroring :func:`wagtail.rich_text.expand_db_html`.

    Parameters:
        html: Database-format rich text HTML. ``None`` is treated as empty.
        internal: When ``True``, preserve entity references using the
            ``wagtail://`` URL scheme (see :class:`MarkdownConverter`).
            When ``False`` (the default), resolve references to public URLs.
        features: Rich text features to load conversion rules for. Defaults
            to the project's default feature set. This controls which
            contentstate rules are loaded so that custom ``linktype`` /
            ``embedtype`` handlers render correctly; it is **not** a
            sanitisation control (see the rich text internals documentation).

    Returns:
        The Markdown representation of ``html``.

    Note:
        Rich text feature whitelisting as enforced for editor input does not
        apply to Markdown output. The DB HTML is converted as-is; whatever was
        stored at write time is what is rendered. Pass ``features`` only to
        control which converter rules are loaded for entity rendering.
    """
    return MarkdownConverter(features=features, internal=internal).from_database_format(
        html
    )
