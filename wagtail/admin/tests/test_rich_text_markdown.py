from unittest.mock import patch

from django.core.files.base import ContentFile
from django.test import SimpleTestCase, TestCase
from draftjs_exporter import MarkdownParseError

from wagtail.admin.rich_text.converters.db_html import DbHTMLConverter
from wagtail.admin.rich_text.converters.markdown_db import MarkdownConverter
from wagtail.documents.models import Document
from wagtail.embeds.exceptions import EmbedException
from wagtail.images import get_image_model
from wagtail.images.tests.utils import get_test_image_file
from wagtail.test.utils import Page


class TestMarkdownToDbHtml(SimpleTestCase):
    def convert(self, markdown, **kwargs):
        return MarkdownConverter(**kwargs).to_database_format(markdown)

    def test_paragraph_and_basic_blocks(self):
        self.assertEqual(
            self.convert("Hello, world!"),
            "<p>Hello, world!</p>",
        )
        self.assertEqual(self.convert("# T"), "<h1>T</h1>")
        self.assertEqual(self.convert("###### T"), "<h6>T</h6>")
        self.assertEqual(self.convert("##### T"), "<h5>T</h5>")
        self.assertEqual(self.convert("> quoted"), "<blockquote>quoted</blockquote>")

    def test_inline_styles(self):
        self.assertEqual(
            self.convert("**bold** _it_ `c`"),
            "<p><b>bold</b> <i>it</i> <code>c</code></p>",
        )
        self.assertEqual(
            self.convert("E = mc<sup>2</sup> and x<sub>1</sub>"),
            "<p>E = mc<sup>2</sup> and x<sub>1</sub></p>",
        )

    def test_fenced_code_becomes_pre(self):
        self.assertEqual(
            self.convert("```\nimport os\n```"),
            "<pre>import os</pre>",
        )

    def test_lists(self):
        self.assertEqual(
            self.convert("- a\n- b\n\n1. c\n2. d"),
            "<ul><li>a</li><li>b</li></ul><ol><li>c</li><li>d</li></ol>",
        )

    def test_thematic_break(self):
        self.assertEqual(self.convert("---"), "<hr/>")

    def test_external_link(self):
        self.assertEqual(
            self.convert("[x](https://example.com/)"),
            '<p><a href="https://example.com/">x</a></p>',
        )

    def test_page_link_reference(self):
        self.assertEqual(
            self.convert("[home](wagtail://page?id=3)"),
            '<p><a linktype="page" id="3">home</a></p>',
        )

    def test_document_link_reference(self):
        self.assertEqual(
            self.convert("[pdf](wagtail://document?id=5)"),
            '<p><a linktype="document" id="5">pdf</a></p>',
        )

    def test_image_reference_standalone(self):
        self.assertEqual(
            self.convert("![cute](wagtail://image?id=42&format=left)"),
            '<embed embedtype="image" format="left" id="42" alt="cute"/>',
        )

    def test_media_embed_reference(self):
        self.assertEqual(
            self.convert("![vid](wagtail://media?url=https%3A%2F%2Fyoutu.be%2Fabc)"),
            '<embed embedtype="media" url="https://youtu.be/abc"/>',
        )

    def test_raw_html_is_not_interpreted(self):
        # The built-in parser never interprets HTML: tags pass through as
        # literal text. The STRING engine does not escape text, so converter
        # output may contain `<script>` as characters — neutralising that is
        # the whitelister's job downstream, asserted in the Task 4 tests
        # (`APIRichText.convert_input` must not let `<script` survive).
        result = self.convert("<div onclick='x()'>hi</div>")
        self.assertIn("hi", result)
        self.assertIn("onclick", result)

    def test_unknown_wagtail_kind_degrades_to_dead_link(self):
        # Unknown kinds fall through to the default LINK resolver; check_url
        # rejects the scheme, so the href is blanked.
        result = self.convert("[x](wagtail://unknown?id=1)")
        self.assertIn("<a", result)
        self.assertNotIn("wagtail://unknown", result)

    def test_malformed_id_raises_parse_error(self):
        with self.assertRaises(MarkdownParseError) as cm:
            self.convert("[x](wagtail://page?id=notanint)")
        self.assertIsNotNone(cm.exception.line)
        self.assertIn("notanint", str(cm.exception))

    def test_wagtail_ref_without_id_raises_parse_error(self):
        # A wagtail:// page/document reference with no id is meaningless and
        # would crash/unpredictably store; it must fail as a parse error (the
        # API layer renders it as 422).
        with self.assertRaises(MarkdownParseError):
            self.convert("[x](wagtail://page)")
        with self.assertRaises(MarkdownParseError):
            self.convert("[x](wagtail://page?foo=bar)")
        with self.assertRaises(MarkdownParseError):
            self.convert("[x](wagtail://document)")

    def test_empty_url_external_link_still_tolerated(self):
        # Not a wagtail:// reference - `check_url("")` allows it, so it keeps
        # its pre-existing tolerated behaviour (dead link, no parse error).
        self.assertEqual(self.convert("[x]()"), '<p><a href="">x</a></p>')

    def test_empty_image_format_dropped_and_reported(self):
        # `format=` (empty) is treated as a missing format: nothing is stored
        # silently - the whitelister removes the embed with a
        # missing_attribute removal report. (The existing `format` attribute
        # of a *valid* reference is unaffected; this asserts only the empty
        # form is gone.)
        html = self.convert("![a](wagtail://image?id=42&format=)")
        self.assertNotIn('format=""', html)
        clean, removals = DbHTMLConverter().clean(html)
        self.assertNotIn("<embed", clean)
        self.assertTrue(
            any(r.tag == "embed" and r.reason == "missing_attribute" for r in removals)
        )

    def test_empty_media_url_dropped_and_reported(self):
        html = self.convert("![a](wagtail://media?url=)")
        self.assertNotIn('url=""', html)
        clean, removals = DbHTMLConverter().clean(html)
        self.assertNotIn("<embed", clean)
        self.assertTrue(
            any(r.tag == "embed" and r.reason == "missing_attribute" for r in removals)
        )

    def test_valid_references_still_convert(self):
        # Regression guard for the entity-map normalisation: valid references
        # (page/document with id, image with format, media with url) convert
        # exactly as before.
        self.assertEqual(
            self.convert("[home](wagtail://page?id=3)"),
            '<p><a linktype="page" id="3">home</a></p>',
        )
        self.assertEqual(
            self.convert("[pdf](wagtail://document?id=5)"),
            '<p><a linktype="document" id="5">pdf</a></p>',
        )
        self.assertEqual(
            self.convert("![cute](wagtail://image?id=42&format=left)"),
            '<embed embedtype="image" format="left" id="42" alt="cute"/>',
        )
        self.assertEqual(
            self.convert("![vid](wagtail://media?url=https%3A%2F%2Fyoutu.be%2Fabc)"),
            '<embed embedtype="media" url="https://youtu.be/abc"/>',
        )

    def test_fenced_code_block_newlines(self):
        # Deferred from Task 2's ledger note: multi-line fenced code must
        # keep its newlines in <pre> output (not become <br/>).
        result = self.convert("```\nimport os\nprint(1)\n```")
        self.assertIn("import os\nprint(1)", result)
        self.assertIn("<pre>", result)

    def test_unsupported_constructs_become_text(self):
        # Documented plain-text behaviour for out-of-scope CommonMark.
        self.assertIn("[text][ref]", self.convert("[text][ref]"))
        self.assertIn("| a | b |", self.convert("| a | b |"))
        # A setext heading MUST NOT become an h1; it stays literal text.
        self.assertEqual(self.convert("Title\n====="), "<p>Title<br/>=====</p>")


class TestDbHtmlToMarkdown(TestCase):
    def convert(self, html, *, resolved=False, **kwargs):
        return MarkdownConverter(**kwargs).from_database_format(html, resolved=resolved)

    def setUp(self):
        self.image = get_image_model().objects.create(
            title="Test image",
            file=get_test_image_file(),
        )
        self.document = Document.objects.create(
            title="Test doc",
            file=ContentFile(b"doc-contents", name="test.txt"),
        )

    def test_paragraph_blocks_and_styles(self):
        result = self.convert("<p>Hello <b>bold</b> and <i>italic</i></p><h2>T</h2>")
        self.assertEqual(result, "Hello **bold** and *italic*\n\n## T\n\n")

    def test_hr(self):
        self.assertEqual(self.convert("<hr/>"), "---\n\n")

    def test_sup_sub_fall_through_to_inline_html(self):
        # sup/sub are not default features, so the converter must be told
        # the field declares them — the same way the editor behaves.
        result = self.convert(
            "<p>E = mc<sup>2</sup></p>", features=["superscript", "subscript"]
        )
        self.assertIn("<sup>2</sup>", result)
        # and it round-trips back
        self.assertEqual(
            MarkdownConverter().to_database_format(result),
            "<p>E = mc<sup>2</sup></p>",
        )

    def test_sup_sub_dropped_without_feature(self):
        # Editor parity: without the feature, the style does not survive the
        # contentstate conversion either.
        result = self.convert("<p>E = mc<sup>2</sup></p>")
        self.assertEqual(result, "E = mc2\n\n")

    def test_external_link(self):
        self.assertEqual(
            self.convert('<p><a href="https://example.com/">x</a></p>'),
            "[x](https://example.com/)\n\n",
        )

    def test_page_link_reference_preserved(self):
        page = Page.objects.get(id=2)
        html = '<p><a linktype="page" id="%d">home</a></p>' % page.id
        self.assertEqual(
            self.convert(html),
            "[home](wagtail://page?id=%d)\n\n" % page.id,
        )

    def test_page_link_dangling_id_preserved_in_db_markdown(self):
        self.assertEqual(
            self.convert('<p><a linktype="page" id="99999">gone</a></p>'),
            "[gone](wagtail://page?id=99999)\n\n",
        )

    def test_page_link_dangling_id_plain_text_in_resolved(self):
        self.assertEqual(
            self.convert(
                '<p><a linktype="page" id="99999">gone</a></p>', resolved=True
            ),
            "gone\n\n",
        )

    def test_page_link_resolved_uses_url(self):
        page = Page.objects.get(id=2)
        result = self.convert(
            '<p><a linktype="page" id="%d">home</a></p>' % page.id,
            resolved=True,
        )
        self.assertEqual(result, "[home](%s)\n\n" % (page.url or "/"))

    def test_document_reference(self):
        html = '<p><a id="%d" linktype="document">doc</a></p>' % self.document.id
        self.assertEqual(
            self.convert(html),
            "[doc](wagtail://document?id=%d)\n\n" % self.document.id,
        )

    def test_document_reference_resolved_uses_url(self):
        html = '<p><a id="%d" linktype="document">doc</a></p>' % self.document.id
        result = self.convert(html, resolved=True)
        self.assertEqual(result, "[doc](%s)\n\n" % self.document.url)

    def test_image_reference(self):
        html = (
            '<embed alt="pic" embedtype="image" format="left" id="%d"/>' % self.image.id
        )
        self.assertEqual(
            self.convert(html),
            "![pic](wagtail://image?id=%d&format=left)\n\n" % self.image.id,
        )

    def test_image_reference_resolved_uses_rendition_url(self):
        html = (
            '<embed alt="pic" embedtype="image" format="left" id="%d"/>' % self.image.id
        )
        result = self.convert(html, resolved=True)
        self.assertRegex(result, r"!\[pic\]\(/media/images/.*\)")
        self.assertNotIn("wagtail://", result)

    def test_media_embed_reference(self):
        with patch("wagtail.embeds.embeds.get_embed", side_effect=EmbedException):
            result = self.convert(
                '<embed embedtype="media" url="https://youtu.be/abc"/>'
            )
        self.assertEqual(
            result,
            "![https://youtu.be/abc](wagtail://media?url=https%3A%2F%2Fyoutu.be%2Fabc)\n\n",
        )

    def test_media_embed_resolved_is_block_link(self):
        with patch("wagtail.embeds.embeds.get_embed", side_effect=EmbedException):
            result = self.convert(
                '<embed embedtype="media" url="https://youtu.be/abc"/>',
                resolved=True,
            )
        self.assertEqual(
            result,
            "[https://youtu.be/abc](https://youtu.be/abc)\n\n",
        )

    def test_round_trip_db_markdown_stable_after_first_normalisation(self):
        md = (
            "## Hi\n\n- a\n- b\n\n[home](wagtail://page?id=2)\n\n"
            "![pic](wagtail://image?id=1&format=fullwidth)\n"
        )
        conv = MarkdownConverter()
        once = conv.from_database_format(conv.to_database_format(md), resolved=False)
        twice = conv.from_database_format(conv.to_database_format(once), resolved=False)
        self.assertEqual(once, twice)

    def test_round_trip_db_html_entity_references_exact(self):
        md = (
            "[home](wagtail://page?id=2) and [doc](wagtail://document?id=1)\n\n"
            "![pic](wagtail://image?id=1&format=fullwidth)\n"
        )
        conv = MarkdownConverter()
        db_html = conv.to_database_format(md)
        md_again = MarkdownConverter().from_database_format(db_html, resolved=False)
        db_html_again = MarkdownConverter().to_database_format(md_again)
        for ref in (
            'linktype="page" id="2"',
            'linktype="document" id="1"',
            'embedtype="image"',
            'id="1"',
        ):
            self.assertIn(ref, db_html_again)


class TestDbHtmlToMarkdownFormatting(SimpleTestCase):
    features = [
        "bold",
        "italic",
        "strikethrough",
        "link",
        "h2",
        "ul",
        "ol",
        "blockquote",
    ]

    def convert(self, html, *, resolved=True):
        return MarkdownConverter(self.features).from_database_format(
            html, resolved=resolved
        )

    def round_trip(self, html):
        converter = MarkdownConverter(self.features)
        return converter.to_database_format(
            converter.from_database_format(html, resolved=False)
        )

    def test_style_split_around_link_keeps_whitespace_outside(self):
        html = '<p><b>bold <a href="https://x.com">link</a> more</b></p>'
        self.assertEqual(
            self.convert(html), "**bold** [**link**](https://x.com) **more**\n\n"
        )
        self.assertEqual(
            self.round_trip(html),
            '<p><b>bold</b> <a href="https://x.com"><b>link</b></a> <b>more</b></p>',
        )

    def test_whitespace_at_link_text_edges(self):
        html = '<p>a<a href="https://x.com"> spaced </a>b</p>'
        self.assertEqual(self.convert(html), "a [spaced](https://x.com) b\n\n")
        self.assertEqual(
            self.round_trip(html), '<p>a <a href="https://x.com">spaced</a> b</p>'
        )

    def test_nested_styles(self):
        self.assertEqual(
            self.convert("<p><b>bold <i>both</i></b></p>"), "**bold** ***both***\n\n"
        )

    def test_line_break_is_hard_break(self):
        self.assertEqual(self.convert("<p>a<br/>b</p>"), "a\\\nb\n\n")

    def test_line_break_in_list_item_and_quote(self):
        self.assertEqual(
            self.convert("<ul><li>a<br/>b</li></ul><blockquote>q<br/>r</blockquote>"),
            "- a\\\nb\n\n> q\\\nr\n\n",
        )

    def test_line_break_in_heading_becomes_space(self):
        self.assertEqual(self.convert("<h2>one<br/>two</h2>"), "## one two\n\n")

    def test_trailing_line_break_dropped(self):
        self.assertEqual(
            self.convert("<p><b>a<br/></b><br/></p><p>b</p>"), "**a**\n\nb\n\n"
        )

    def test_db_markdown_keeps_line_breaks_round_trippable(self):
        html = "<p>a<br/>b</p><h2>one<br/>two</h2>"
        self.assertEqual(self.convert(html, resolved=False), "a\nb\n\n## one\ntwo\n\n")
        self.assertEqual(self.round_trip("<p>a<br/>b</p>"), "<p>a<br/>b</p>")

    def test_consecutive_blockquotes_form_one_quote(self):
        html = (
            "<blockquote>one</blockquote><blockquote>two</blockquote>"
            "<p>after</p><blockquote>three</blockquote>"
        )
        self.assertEqual(self.convert(html), "> one\n>\n> two\n\nafter\n\n> three\n\n")
        self.assertEqual(self.round_trip(html), html)

    def test_nested_ordered_list_indented_to_content_column(self):
        html = "<ol><li>a<ol><li>x</li><li>y</li></ol></li><li>b</li></ol>"
        self.assertEqual(self.convert(html), "1. a\n   1. x\n   2. y\n2. b\n\n")
        self.assertEqual(self.round_trip(html), html)

    def test_nested_list_under_multi_digit_number(self):
        html = (
            "<ol>"
            + "".join(f"<li>{i}</li>" for i in range(1, 10))
            + "<li>ten<ul><li>nested</li></ul></li></ol>"
        )
        self.assertTrue(self.convert(html).endswith("9. 9\n10. ten\n    - nested\n\n"))

    def test_numbering_continues_after_nested_list_of_other_type(self):
        self.assertEqual(
            self.convert(
                "<ol><li>one</li><li>two<ul><li>nested</li></ul></li><li>three</li></ol>"
            ),
            "1. one\n2. two\n   - nested\n3. three\n\n",
        )

    def test_mixed_nesting_is_a_tight_list(self):
        html = "<ul><li>a<ol><li>x</li></ol></li><li>b</li></ul>"
        self.assertEqual(self.convert(html), "- a\n  1. x\n- b\n\n")
        self.assertEqual(
            self.round_trip("<ul><li>a<ol><li>x</li></ol></li></ul>"),
            "<ul><li>a<ol><li>x</li></ol></li></ul>",
        )
        # The importer starts a new list after a nested list of another type.
        self.assertEqual(
            self.round_trip(html),
            "<ul><li>a<ol><li>x</li></ol></li></ul><ul><li>b</li></ul>",
        )
