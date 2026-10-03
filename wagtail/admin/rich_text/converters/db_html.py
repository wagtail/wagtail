from dataclasses import dataclass
from typing import Literal

from bs4 import BeautifulSoup
from django.utils.functional import cached_property
from django.utils.html import escape

from wagtail.admin.rich_text.converters.editor_html import (
    DbWhitelister,
    EditorHTMLConverter,
)


@dataclass
class RichTextRemoval:
    """One out-of-features / unresolvable construct stripped from rich text input.

    ``detail`` is a short snippet of the affected source markup. It is raw
    input content: API clients must treat it as untrusted.
    """

    tag: str
    action: Literal["unwrapped", "removed"]
    reason: Literal[
        "feature_disabled", "unknown_linktype", "unknown_embedtype", "missing_attribute"
    ]
    #: Reserved for future per-attribute reporting granularity.
    attribute: str | None = None
    detail: str | None = None


class DbHtmlInputWhitelister(DbWhitelister):
    """Whitelister for rich text input already in database HTML format.

    DbWhitelister expects editor-flavoured HTML (``data-linktype`` /
    ``data-embedtype``); API input arrives in the database format
    (``linktype`` / ``embedtype``). clean() renames the database-format
    attributes to editor format up front, so the inherited, editor-tested
    logic does the actual whitelisting — including rebuilding link/embed
    attributes via the feature handlers' ``get_db_attributes()``.

    Every element-level removal is recorded in ``self.removals``.
    Attribute-level drops by ``attribute_rule`` are not reported, matching
    editor behaviour.
    """

    def __init__(self, converter_rules):
        super().__init__(converter_rules)
        self.removals: list[RichTextRemoval] = []

    def clean(self, html):
        self.removals = []
        doc = BeautifulSoup(html, "html.parser")
        self._rename_db_attributes(doc)
        self.clean_node(doc, doc)
        # Keep in sync with Whitelister.clean(): escape via django's escape so
        # the regexp-based db-HTML rewriting isn't confused by quote style.
        return doc.decode(formatter=escape)

    @staticmethod
    def _rename_db_attributes(doc):
        for tag in doc.find_all(["a", "embed"]):
            marker = "linktype" if tag.name == "a" else "embedtype"
            if marker not in tag.attrs:
                # A plain <a href> external link is handled by the 'link'
                # feature's href attribute rule; an <embed> without embedtype
                # is an unknown element and gets unwrapped.
                continue
            tag.attrs = {f"data-{name}": value for name, value in tag.attrs.items()}

    def clean_tag_node(self, doc, tag):
        embed_type = tag.attrs.get("data-embedtype")
        link_type = tag.attrs.get("data-linktype") if tag.name == "a" else None

        if embed_type is not None and embed_type not in self.embed_handlers:
            self._record(tag, "removed", "unknown_embedtype")
            tag.decompose()
            return
        if link_type is not None and link_type not in self.link_handlers:
            self._record(tag, "unwrapped", "unknown_linktype")
            # Keep in sync with DbWhitelister's link branch (editor_html.py):
            # children must be cleaned BEFORE unwrapping, or markup nested
            # inside the link (e.g. <script>) would bypass the whitelister.
            for child in list(tag.contents):
                self.clean_node(doc, child)
            tag.unwrap()
            return

        is_known = (
            embed_type is not None
            or link_type is not None
            or tag.name in self.element_rules
        )
        if not is_known:
            self._record(tag, "unwrapped", "feature_disabled")

        try:
            super().clean_tag_node(doc, tag)
        except KeyError:
            # A handler's get_db_attributes() requires an attribute the input
            # didn't provide (e.g. <a linktype="page"> with no id) — input the
            # editor itself would never produce.
            if embed_type is not None:
                self._record(tag, "removed", "missing_attribute")
                tag.decompose()
            elif link_type is not None:
                self._record(tag, "unwrapped", "missing_attribute")
                tag.unwrap()
            else:
                raise

    def _record(self, tag, action, reason):
        self.removals.append(
            RichTextRemoval(
                tag=tag.name, action=action, reason=reason, detail=str(tag)[:80]
            )
        )


class DbHTMLConverter(EditorHTMLConverter):
    """Converter for rich text input already in database HTML format.

    Validates/sanitises DB HTML against a feature list, using the same
    feature-registry converter rules as the editor. Returns the cleaned DB
    HTML along with an itemised list of every element-level removal.
    """

    @cached_property
    def whitelister(self):
        return DbHtmlInputWhitelister(self.converter_rules)

    def clean(self, html) -> tuple[str, list[RichTextRemoval]]:
        cleaned = self.whitelister.clean(html)
        return cleaned, list(self.whitelister.removals)
