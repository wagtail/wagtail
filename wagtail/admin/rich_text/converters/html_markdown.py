"""
Conversion of arbitrary HTML (such as a rendered page or block) to Markdown.

This reuses the rich text conversion pipeline rather than implementing a
separate HTML parser:

1. Normalise: a BeautifulSoup pass that reshapes arbitrary markup into the
   flat "blocks containing inline content" model that contentstate can
   represent. Non-content elements are dropped, layout containers are
   unwrapped, and blocks nested inside inline, list or quote elements are
   split out. Constructs contentstate cannot represent (tables, code
   blocks, linked images) are rendered to Markdown here and carried
   through the rest of the pipeline as opaque tokens.
2. Whitelist: the editor HTML -> DB HTML whitelister (DbWhitelister), with
   the "ingest" feature set plus rules for features without editorhtml rules
   and external images.
3. DB HTML -> contentstate: HtmlToContentStateHandler, extended with a
   handler for <img src>.
4. contentstate -> Markdown: the resolved exporter from markdown_db.
"""

import json
import re
import secrets
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Comment, NavigableString, Tag
from draftjs_exporter.markdown.escape import (
    code_block_fence,
    escape_link_destination,
    escape_text,
)

from wagtail.admin.rich_text.converters.contentstate_models import Entity
from wagtail.admin.rich_text.converters.editor_html import (
    DbWhitelister,
    EditorHTMLConverter,
    WhitelistRule,
)
from wagtail.admin.rich_text.converters.html_to_contentstate import (
    AtomicBlockEntityElementHandler,
    HtmlToContentStateHandler,
)
from wagtail.admin.rich_text.converters.markdown_db import (
    markdown_exporter,
    strip_trailing_line_breaks,
)
from wagtail.whitelist import allow_without_attributes, attribute_rule, check_url

# Rich text features used to ingest arbitrary HTML, for their editorhtml
# (whitelisting) and contentstate (conversion) rules. Features backed by
# database objects (image, embed, document-link) are left out: rendered HTML
# carries URLs, not IDs.
INGEST_FEATURES = [
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "bold",
    "italic",
    "link",
    "ol",
    "ul",
    "hr",
    "blockquote",
    "code",
    "superscript",
    "subscript",
    "strikethrough",
]

# Elements whose content is never meaningful as document text.
DROP_ELEMENTS = {
    "applet",
    "area",
    "audio",
    "base",
    "button",
    "canvas",
    "datalist",
    "dialog",
    "embed",
    "head",
    "iframe",
    "input",
    "link",
    "map",
    "math",
    "meta",
    "meter",
    "nav",
    "noscript",
    "object",
    "optgroup",
    "option",
    "output",
    "param",
    "progress",
    "script",
    "select",
    "slot",
    "source",
    "style",
    "svg",
    "template",
    "textarea",
    "title",
    "track",
    "video",
}

# Layout containers: unwrapped when they hold blocks, otherwise turned into a
# paragraph.
CONTAINER_ELEMENTS = {
    "address",
    "article",
    "aside",
    "body",
    "center",
    "details",
    "div",
    "fieldset",
    "figure",
    "footer",
    "form",
    "header",
    "hgroup",
    "html",
    "legend",
    "main",
    "search",
    "section",
}

HEADING_ELEMENTS = {"h1", "h2", "h3", "h4", "h5", "h6"}

# Elements that the contentstate handler treats as blocks.
TEXT_BLOCK_ELEMENTS = {"p", "blockquote"} | HEADING_ELEMENTS
BLOCK_ELEMENTS = (
    TEXT_BLOCK_ELEMENTS
    | CONTAINER_ELEMENTS
    | {"ul", "ol", "li", "hr", "table", "dl", "dt", "dd", "figcaption", "summary"}
)

# Inline elements with a direct equivalent in the ingest features.
INLINE_RENAMES = {
    "b": "strong",
    "i": "em",
    "cite": "em",
    "dfn": "em",
    "del": "s",
    "strike": "s",
    "kbd": "code",
    "samp": "code",
    "tt": "code",
    "var": "code",
}

# Inline elements kept by the whitelister / contentstate handler.
KNOWN_INLINE_ELEMENTS = {"a", "strong", "em", "code", "s", "sup", "sub", "br", "img"}

# Text of heading permalink links, such as "¶" or "#".
PERMALINK_TEXTS = {"¶", "#", "§", "🔗"}

CODE_LANGUAGE_RE = re.compile(r"^(?:language|lang)-([\w+#.-]+)$")

LINE_START_ESCAPE_RE = re.compile(r"^(\d+)?\\(?=[.)])|^\\(?=[#+\-=>~])")

# Browsers clamp colspan to 1000.
MAX_COLSPAN = 1000

# Deeper lists are flattened into their parent item, keeping the document
# shallow enough for the (recursive) whitelister.
MAX_LIST_DEPTH = 10

# Marks the paragraph holding a block-level token (code block, table).
BLOCK_MARKER_ATTR = "data-markdown-block"


# Code fence, possibly inside a blockquote.
CODE_FENCE_RE = re.compile(r"^((?:> )*)(`{3,}|~{3,})")


def _strip_trailing_whitespace(markdown):
    """Strip whitespace (including non-breaking spaces) at the end of lines,
    outside fenced code blocks. Line breaks never rely on trailing spaces."""
    lines = []
    fence = None
    for line in markdown.split("\n"):
        if fence is None:
            match = CODE_FENCE_RE.match(line)
            if match:
                quote_prefix, fence = match.groups()
            line = line.rstrip(" \t\xa0")
        else:
            content = line.removeprefix(quote_prefix).strip()
            if set(content) == {fence[0]} and len(content) >= len(fence):
                # Closing fence: at least as long as the opening one.
                fence = None
        lines.append(line)
    return "\n".join(lines)


class ExternalImageElementHandler(AtomicBlockEntityElementHandler):
    """<img src> -> IMAGE entity with the source URL, as opposed to the
    <embed embedtype="image"> handler which looks up an image by ID."""

    def create_entity(self, name, attrs, state, contentstate):
        return Entity(
            "IMAGE", "IMMUTABLE", {"src": attrs.get("src", ""), "alt": attrs.get("alt")}
        )


class IngestHtmlToContentStateHandler(HtmlToContentStateHandler):
    def __init__(self, features=()):
        super().__init__(features)
        self.element_handlers.add_rules({"img": ExternalImageElementHandler()})


class HTMLToMarkdownConverter:
    """Convert arbitrary HTML to Markdown.

    ``base_url`` makes relative link and image URLs absolute.
    ``content_selector`` is a CSS selector for the element holding the
    content; by default, ``<main>`` is used if present, then ``<body>``.
    """

    def __init__(self, *, base_url=None, content_selector=None):
        self.base_url = base_url
        self.content_selector = content_selector
        self.tokens = []
        # Random per converter, so text in the input can't match a token.
        self.token_prefix = f"WAGTAILMD{secrets.token_hex(8)}"
        self.token_re = re.compile(self.token_prefix + r"(\d+)Z")

        converter_rules = list(EditorHTMLConverter(INGEST_FEATURES).converter_rules)
        converter_rules += [
            # Features with contentstate rules but no editorhtml rules.
            *(
                WhitelistRule(element, allow_without_attributes)
                for element in ("blockquote", "code", "sup", "sub", "s")
            ),
            WhitelistRule("img", attribute_rule({"src": check_url, "alt": True})),
        ]
        self.whitelister = DbWhitelister(converter_rules)
        self.exporter = markdown_exporter(resolved=True)

    def convert(self, html):
        self.tokens = []
        markdown = self._convert(html)
        return f"{markdown}\n" if markdown else ""

    def _convert(self, html):
        soup = BeautifulSoup(str(html), "html.parser")
        root = self._select_root(soup)
        self._normalise(soup, root)
        db_html = self.whitelister.clean(root.decode_contents())

        handler = IngestHtmlToContentStateHandler(INGEST_FEATURES)
        handler.reset()
        handler.feed(db_html)
        handler.close()
        content_state = json.loads(handler.contentstate.as_json())
        strip_trailing_line_breaks(content_state)
        markdown = self.exporter.render(content_state)
        return self._finalise(markdown)

    def _convert_inline(self, html):
        """Convert an HTML fragment to a single line, e.g. for a table cell."""
        markdown = self._convert(html)
        lines = [line.strip() for line in markdown.split("\n") if line.strip()]
        # Lines are joined with <br>, so drop hard line break backslashes
        # (an odd number of trailing backslashes; an even one is escaped text).
        lines = [
            line[:-1] if (len(line) - len(line.rstrip("\\"))) % 2 else line
            for line in lines
        ]
        # Line-start escapes (for list markers, headings, ...) aren't needed
        # mid-line, e.g. "350\.0" in a table cell.
        return "<br>".join(LINE_START_ESCAPE_RE.sub(r"\1", line) for line in lines)

    # Normalisation

    def _select_root(self, soup):
        if self.content_selector:
            root = soup.select_one(self.content_selector)
            if root is not None:
                return root
        return soup.find("main") or soup.find("body") or soup

    def _normalise(self, soup, root):
        for comment in root.find_all(string=lambda s: isinstance(s, Comment)):
            comment.extract()

        self._convert_media(soup, root)

        for tag in root.find_all(True):
            if tag.decomposed:
                continue
            if tag.name in DROP_ELEMENTS or self._is_excluded(tag):
                tag.decompose()

        self._convert_images(root)
        self._convert_links(root)
        self._convert_preformatted(soup, root)
        self._convert_tables(soup, root)
        self._convert_definition_lists(soup, root)
        self._convert_inline_elements(root)
        self._wrap_orphan_list_items(soup, root)
        self._unwrap_containers(soup, root)
        self._split_nested_blocks(soup, root)
        self._inline_images(root)
        self._flatten_list_items(soup, root)
        self._flatten_blockquotes(soup, root)
        self._tidy_line_breaks(root)

    @staticmethod
    def _is_excluded(tag):
        if tag.attrs is None:
            return False
        return (
            tag.has_attr("data-markdown-ignore")
            or tag.has_attr("hidden")
            or tag.get("aria-hidden") == "true"
            or re.search(r"display\s*:\s*none", tag.get("style", "")) is not None
        )

    def _absolute(self, url):
        url = (url or "").strip()
        if self.base_url and url:
            return urljoin(self.base_url, url)
        return url

    def _make_token(self, markdown):
        self.tokens.append(markdown)
        return NavigableString(f"{self.token_prefix}{len(self.tokens) - 1}Z")

    def _block_token(self, soup, markdown):
        p = soup.new_tag("p", attrs={BLOCK_MARKER_ATTR: ""})
        p.append(self._make_token(markdown))
        return p

    @staticmethod
    def _is_block_token(tag):
        return isinstance(tag, Tag) and tag.has_attr(BLOCK_MARKER_ATTR)

    def _convert_media(self, soup, root):
        """<iframe>, <video> and <audio> become links to their source."""
        for tag in root.find_all(["iframe", "video", "audio"]):
            src = tag.get("src")
            if not src:
                source = tag.find("source", src=True)
                src = source["src"] if source else None
            if not src:
                continue
            link = soup.new_tag("a", href=self._absolute(src))
            link.string = tag.get("title") or tag.get("aria-label") or src
            p = soup.new_tag("p")
            p.append(link)
            tag.replace_with(p)

    def _image_src(self, img):
        src = img.get("src") or img.get("data-src")
        if not src and img.get("srcset"):
            src = img["srcset"].split(",")[0].strip().split(" ")[0]
        if not src or src.startswith("data:"):
            return None
        return check_url(self._absolute(src))

    def _convert_images(self, root):
        for picture in root.find_all("picture"):
            img = picture.find("img")
            if img:
                picture.replace_with(img)
            else:
                picture.decompose()

        for img in root.find_all("img"):
            src = self._image_src(img)
            if not src:
                img.decompose()
                continue
            img.attrs = {"src": src, "alt": img.get("alt", "")}

        for link in root.find_all("a", href=True):
            images = link.find_all("img")
            if not images:
                continue
            if link.get_text(strip=True):
                # Keep the link text, the image is presumably decorative.
                for img in images:
                    img.decompose()
                continue
            href = check_url(self._absolute(link["href"]))
            markdown = " ".join(
                f"[![{escape_text(img['alt'])}]({escape_link_destination(img['src'])})]"
                f"({escape_link_destination(href)})"
                if href
                else f"![{escape_text(img['alt'])}]({escape_link_destination(img['src'])})"
                for img in images
            )
            link.replace_with(self._make_token(markdown))

    def _convert_links(self, root):
        for link in root.find_all("a"):
            href = link.get("href")
            text = link.get_text(strip=True)
            if href and href.startswith("#") and text in PERMALINK_TEXTS:
                link.decompose()
                continue
            if not href or not check_url(href) or not text:
                link.unwrap()
                continue
            link.attrs = {"href": self._absolute(href)}

    def _convert_preformatted(self, soup, root):
        for pre in root.find_all("pre"):
            text = pre.get_text()
            # As per the HTML spec, a newline directly after <pre> is ignored.
            if text.startswith("\n"):
                text = text[1:]
            text = text.rstrip("\n")
            if pre.find_parent(["li", "td", "th"]):
                # List items and table cells are single-line in Markdown.
                code = soup.new_tag("code")
                code.string = text
                pre.replace_with(soup.new_tag("br"), code)
                continue
            fence = code_block_fence(text, "`")
            language = self._code_language(pre)
            pre.replace_with(
                self._block_token(soup, f"{fence}{language}\n{text}\n{fence}")
            )

    @staticmethod
    def _code_language(pre):
        """Language from a language-x / lang-x class on <pre> or its <code>."""
        for tag in (pre, pre.find("code")):
            for class_name in tag.get("class", []) if tag else []:
                match = CODE_LANGUAGE_RE.match(class_name)
                if match and match.group(1) not in ("none", "text"):
                    return match.group(1)
        return ""

    def _convert_tables(self, soup, root):
        # Innermost tables first, so nested tables are flattened into cells.
        for table in reversed(root.find_all("table")):
            rows = [
                tr for tr in table.find_all("tr") if tr.find_parent("table") is table
            ]
            replacement = []
            caption = table.find("caption")
            if caption and caption.get_text(strip=True):
                p = soup.new_tag("p")
                strong = soup.new_tag("strong")
                strong.append(caption.get_text(" ", strip=True))
                p.append(strong)
                replacement.append(p)
            if rows and table.find_parent(["td", "th", "li"]):
                # Markdown tables can't nest, or sit in a list item: flatten
                # to one line per row.
                if any(
                    not isinstance(node, NavigableString) or node.strip()
                    for node in table.previous_siblings
                ):
                    replacement.append(soup.new_tag("br"))
                replacement.append(
                    self._make_token(
                        "<br>".join(" · ".join(row) for row in self._table_grid(rows)),
                    )
                )
            elif rows:
                replacement.append(self._block_token(soup, self._render_table(rows)))
            if replacement:
                table.replace_with(*replacement)
            else:
                table.decompose()

    def _render_table(self, rows):
        grid = self._table_grid(rows)
        width = max(len(row) for row in grid) or 1
        grid = [row + [""] * (width - len(row)) for row in grid]
        lines = [
            self._table_row(grid[0]),
            self._table_row(["---"] * width),
            *(self._table_row(row) for row in grid[1:]),
        ]
        return "\n".join(lines)

    @staticmethod
    def _table_row(cells):
        return "|" + "|".join(f" {cell} " if cell else " " for cell in cells) + "|"

    def _table_grid(self, rows):
        grid = []
        for tr in rows:
            cells = []
            for cell in tr.find_all(["th", "td"], recursive=False):
                text = self._convert_inline(cell.decode_contents())
                cells.append(text.replace("|", "\\|"))
                colspan = cell.get("colspan", "1")
                if colspan.isdigit():
                    cells += [""] * (min(int(colspan), MAX_COLSPAN) - 1)
            grid.append(cells)
        return grid

    def _convert_definition_lists(self, soup, root):
        """Terms (<dt>, <summary>) become bold paragraphs; descriptions and
        captions (<dd>, <figcaption>) plain paragraphs."""
        for tag in root.find_all(["dt", "summary"]):
            strong = soup.new_tag("strong")
            for child in list(tag.contents):
                strong.append(child.extract())
            tag.append(strong)
            tag.name = "p"
            tag.attrs = {}
        for tag in root.find_all(["dd", "figcaption"]):
            tag.name = "p"
            tag.attrs = {}
        for tag in root.find_all("dl"):
            tag.unwrap()

    def _convert_inline_elements(self, root):
        for tag in root.find_all(True):
            if tag.name in INLINE_RENAMES:
                tag.name = INLINE_RENAMES[tag.name]
                tag.attrs = {}
            elif tag.name == "q":
                tag.insert(0, NavigableString("“"))
                tag.append(NavigableString("”"))
                tag.unwrap()
            elif tag.name == "wbr":
                tag.decompose()
            elif tag.name not in BLOCK_ELEMENTS | KNOWN_INLINE_ELEMENTS:
                # span, u, mark, small, abbr, time, label, table parts
                # outside a table, ...
                tag.unwrap()
        # Nested duplicates, often from unclosed tags (<b>a<b>b), add nothing
        # and would produce invalid Markdown (****b****).
        for tag in reversed(root.find_all(KNOWN_INLINE_ELEMENTS - {"br", "img"})):
            if tag.find_parent(tag.name):
                tag.unwrap()

    @staticmethod
    def _has_block_child(tag):
        return any(
            isinstance(child, Tag) and child.name in BLOCK_ELEMENTS
            for child in tag.children
        )

    def _wrap_inline_runs(self, soup, tag, wrapper_name):
        """Wrap runs of inline content among tag's children in wrapper_name
        elements, so tag only has block children."""
        run = []

        def flush():
            if any(
                not isinstance(node, NavigableString) or node.strip() for node in run
            ):
                wrapper = soup.new_tag(wrapper_name)
                run[0].insert_before(wrapper)
                for node in run:
                    wrapper.append(node.extract())
            else:
                for node in run:
                    node.extract()
            run.clear()

        for child in list(tag.children):
            if isinstance(child, Tag) and child.name in BLOCK_ELEMENTS:
                if run:
                    flush()
            else:
                run.append(child)
        if run:
            flush()

    def _unwrap_containers(self, soup, root):
        # Deepest first, so the decision for each container is based on its
        # already-normalised children.
        for tag in reversed(root.find_all(CONTAINER_ELEMENTS)):
            if self._has_block_child(tag):
                self._wrap_inline_runs(soup, tag, "p")
                tag.unwrap()
            elif tag.get_text(strip=True) or tag.find("img"):
                tag.name = "p"
                tag.attrs = {}
            else:
                tag.decompose()

    def _split_nested_blocks(self, soup, root):
        """Split blocks out of inline elements, paragraphs and headings. Each
        pass can leave blocks nested in the other's elements (e.g.
        <h3><em><h1>...), so repeat until none remain."""
        while any(
            self._has_block_child(tag)
            for tag in root.find_all([*KNOWN_INLINE_ELEMENTS, "p", *HEADING_ELEMENTS])
        ):
            self._split_blocks_in_inline_elements(soup, root)
            self._split_blocks_in_text_blocks(soup, root)

    def _split_blocks_in_inline_elements(self, soup, root):
        """<a><h3>Title</h3><p>Text</p></a> -> <h3><a>Title</a></h3><p><a>Text</a></p>"""
        for tag in reversed(root.find_all(KNOWN_INLINE_ELEMENTS)):
            if not self._has_block_child(tag):
                continue
            self._wrap_inline_runs(soup, tag, "p")
            for child in list(tag.children):
                if child.name in TEXT_BLOCK_ELEMENTS and not self._is_block_token(
                    child
                ):
                    inner = soup.new_tag(tag.name, attrs=dict(tag.attrs))
                    for node in list(child.contents):
                        inner.append(node.extract())
                    child.append(inner)
            tag.unwrap()

    def _split_blocks_in_text_blocks(self, soup, root):
        """<p>a<ul>..</ul>b</p> -> <p>a</p><ul>..</ul><p>b</p>"""
        for tag in root.find_all(HEADING_ELEMENTS):
            # Markdown headings are a single line.
            for br in tag.find_all("br"):
                br.replace_with(" ")
        for tag in reversed(root.find_all(["p", *HEADING_ELEMENTS])):
            if not self._has_block_child(tag):
                continue
            self._wrap_inline_runs(soup, tag, tag.name)
            if tag.name in HEADING_ELEMENTS:
                for child in tag.find_all("p", recursive=False):
                    if not self._is_block_token(child):
                        child.name = tag.name
            tag.unwrap()

    def _wrap_orphan_list_items(self, soup, root):
        for li in root.find_all("li"):
            if li.parent is None or li.parent.name not in ("ul", "ol"):
                li.wrap(soup.new_tag("ul"))
        for li in reversed(root.find_all("li")):
            if not li.get_text(strip=True) and not li.find("img"):
                li.decompose()
        for tag in root.find_all(["ul", "ol"]):
            if not tag.find("li"):
                tag.decompose()
        for tag in reversed(root.find_all(["ul", "ol"])):
            if len(tag.find_parents(["ul", "ol"])) >= MAX_LIST_DEPTH:
                tag.unwrap()

    def _inline_images(self, root):
        """Images sharing a block with other content (text, list items, table
        cells) are emitted inline, rather than splitting the block around an
        atomic image block."""
        for img in root.find_all("img"):
            block = (
                img.find_parent(["p", "li", "blockquote", *HEADING_ELEMENTS])
                or img.parent
            )
            in_list_item = img.find_parent("li") is not None
            if not in_list_item and block is root and not block.get_text(strip=True):
                continue
            if (
                not in_list_item
                and block.name == "p"
                and not block.get_text(strip=True)
            ):
                if len(block.find_all("img")) == 1:
                    continue
            img.replace_with(
                self._make_token(
                    f"![{escape_text(img.get('alt', ''))}]"
                    f"({escape_link_destination(img['src'])})",
                )
            )

    def _flatten_list_items(self, soup, root):
        """Contentstate list items are single blocks: paragraphs, headings and
        other blocks inside them become line-broken inline content. Nested
        lists are kept."""
        for li in reversed(root.find_all("li")):
            children = [
                c
                for c in li.children
                if isinstance(c, Tag) and c.name in BLOCK_ELEMENTS - {"ul", "ol"}
            ]
            for child in children:
                if child.name == "hr":
                    child.replace_with(soup.new_tag("br"))
                    continue
                if child.next_sibling is not None:
                    child.insert_after(soup.new_tag("br"))
                child.unwrap()
            # Content after a nested list would end up outside the list item.
            for nested in li.find_all(["ul", "ol"], recursive=False):
                trailing = list(nested.next_siblings)
                if any(
                    not isinstance(node, NavigableString) or node.strip()
                    for node in trailing
                ):
                    nested_li = soup.new_tag("li")
                    for node in trailing:
                        nested_li.append(node.extract())
                    nested.append(nested_li)

    def _flatten_blockquotes(self, soup, root):
        """Contentstate blockquotes are single blocks: split a quote holding
        several paragraphs into consecutive quote blocks."""
        for quote in reversed(root.find_all("blockquote")):
            if not self._has_block_child(quote):
                continue
            self._wrap_inline_runs(soup, quote, "p")
            for child in list(quote.children):
                if child.name in TEXT_BLOCK_ELEMENTS:
                    child.name = "blockquote"
                    child.attrs = {}
            quote.unwrap()

    @staticmethod
    def _is_blank(node):
        return isinstance(node, NavigableString) and not node.strip()

    def _tidy_line_breaks(self, root):
        """Move line breaks at the edge of inline elements outside them, and
        drop breaks at the start of a block or directly after another one."""
        for br in root.find_all("br"):
            while br.parent is not root and br.parent.name in KNOWN_INLINE_ELEMENTS:
                parent = br.parent
                if all(self._is_blank(node) for node in br.previous_siblings):
                    parent.insert_before(br.extract())
                elif all(self._is_blank(node) for node in br.next_siblings):
                    parent.insert_after(br.extract())
                else:
                    break
        for br in root.find_all("br"):
            previous = next(
                (n for n in br.previous_siblings if not self._is_blank(n)), None
            )
            if previous is None or getattr(previous, "name", None) == "br":
                br.decompose()

    # Output

    def _replace_tokens(self, markdown):
        def replace_in_line(line):
            # Multi-line tokens (code blocks, tables) in a quote need the
            # quote marker on each line.
            prefix = re.match(r"(?:> )*", line).group()
            return self.token_re.sub(
                lambda m: self.tokens[int(m.group(1))].replace("\n", "\n" + prefix),
                line,
            )

        return "\n".join(replace_in_line(line) for line in markdown.split("\n"))

    def _finalise(self, markdown):
        markdown = self._replace_tokens(markdown)
        # Atomic blocks (images, rules) are padded with spacer paragraphs.
        markdown = re.sub(r"\n{3,}", "\n\n", markdown)
        return _strip_trailing_whitespace(markdown).strip("\n")


def html_to_markdown(html, *, base_url=None, content_selector=None):
    return HTMLToMarkdownConverter(
        base_url=base_url, content_selector=content_selector
    ).convert(html)
