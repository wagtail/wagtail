from django.test import SimpleTestCase
from draftjs_exporter import MarkdownParseError

from wagtail.admin.rich_text.converters.markdown_db import MarkdownConverter


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

    def test_unsupported_constructs_become_text(self):
        # Documented plain-text behaviour for out-of-scope CommonMark.
        self.assertIn("[text][ref]", self.convert("[text][ref]"))
        self.assertIn("| a | b |", self.convert("| a | b |"))
        # A setext heading MUST NOT become an h1; it stays literal text.
        self.assertEqual(self.convert("Title\n====="), "<p>Title<br/>=====</p>")
