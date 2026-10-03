from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, TestCase, override_settings

from wagtail.api.rich_text import APIRichText, RichTextFormatError
from wagtail.api.v2.serializers import RichTextFieldSerializer
from wagtail.test.utils import Page


class TestRichTextFormatResolution(SimpleTestCase):
    def test_default_format_is_db_html(self):
        self.assertEqual(APIRichText.get_default_format(), APIRichText.DEFAULT_FORMAT)

    @override_settings(WAGTAILAPI_RICH_TEXT_FORMAT="html")
    def test_setting_overrides_default(self):
        self.assertEqual(APIRichText.get_default_format(), "html")

    def test_query_parameter_overrides_setting(self):
        with override_settings(WAGTAILAPI_RICH_TEXT_FORMAT="db_html"):
            self.assertEqual(APIRichText.resolve_format("html"), "html")

    def test_invalid_query_parameter_raises(self):
        with self.assertRaises(RichTextFormatError) as cm:
            APIRichText.resolve_format("invalid")
        self.assertIn("invalid", str(cm.exception))

    @override_settings(WAGTAILAPI_RICH_TEXT_FORMAT="invalid")
    def test_invalid_setting_raises(self):
        with self.assertRaises(ImproperlyConfigured) as cm:
            APIRichText.check_setting()
        self.assertIn("invalid", str(cm.exception))
        self.assertIn(APIRichText.SETTING_NAME, str(cm.exception))


class TestSerializeRichText(TestCase):
    fixtures = ["test.json"]

    def test_db_html_returns_value_unchanged(self):
        value = '<p><a linktype="page" id="4">Events</a></p>'
        self.assertEqual(
            APIRichText.serialize(value, format=APIRichText.FORMAT_DB_HTML),
            value,
        )

    def test_html_expands_entity_references(self):
        page = Page.objects.get(url_path="/home/events/")
        value = f'<p><a linktype="page" id="{page.id}">Events</a></p>'
        self.assertEqual(
            APIRichText.serialize(value, format="html"),
            '<p><a href="/events/">Events</a></p>',
        )

    def test_none_returns_none(self):
        self.assertIsNone(APIRichText.serialize(None, format="html"))


class TestRichTextFieldSerializer(SimpleTestCase):
    def test_accepts_text_field_kwargs(self):
        field = RichTextFieldSerializer(max_length=120)
        self.assertEqual(field.max_length, 120)


class TestParseInput(SimpleTestCase):
    def test_plain_string_is_db_html(self):
        self.assertEqual(APIRichText.parse_input("<p>x</p>"), ("db_html", "<p>x</p>"))

    def test_envelope(self):
        self.assertEqual(
            APIRichText.parse_input({"format": "db_html", "content": "<p>x</p>"}),
            ("db_html", "<p>x</p>"),
        )

    def test_envelope_format_defaults_to_db_html(self):
        self.assertEqual(
            APIRichText.parse_input({"content": "<p>x</p>"}), ("db_html", "<p>x</p>")
        )

    def test_unknown_format_raises(self):
        with self.assertRaises(RichTextFormatError) as cm:
            APIRichText.parse_input({"format": "markdown", "content": "# Hi"})
        self.assertIn("markdown", str(cm.exception))
        self.assertIn("db_html", str(cm.exception))

    def test_missing_content_raises(self):
        with self.assertRaises(RichTextFormatError):
            APIRichText.parse_input({"format": "db_html"})

    def test_non_string_content_raises(self):
        with self.assertRaises(RichTextFormatError):
            APIRichText.parse_input({"format": "db_html", "content": 42})

    def test_other_types_raise(self):
        with self.assertRaises(RichTextFormatError):
            APIRichText.parse_input(["<p>x</p>"])


class TestConvertInput(SimpleTestCase):
    def test_plain_string_is_sanitised(self):
        cleaned, removals = APIRichText.convert_input(
            "<p><b>x</b></p><script>alert(1)</script>", features=["bold"]
        )
        self.assertEqual(cleaned, "<p><b>x</b></p>alert(1)")
        self.assertEqual([r.tag for r in removals], ["script"])

    def test_envelope_is_sanitised(self):
        cleaned, removals = APIRichText.convert_input(
            {"format": "db_html", "content": "<h1>T</h1>"}, features=["bold"]
        )
        self.assertEqual(cleaned, "T")
        self.assertEqual(len(removals), 1)

    def test_unknown_format_raises(self):
        with self.assertRaises(RichTextFormatError):
            APIRichText.convert_input({"format": "html", "content": "<p>x</p>"})

    def test_features_none_uses_registry_defaults(self):
        cleaned, removals = APIRichText.convert_input("<p><b>x</b></p>")
        self.assertEqual(cleaned, "<p><b>x</b></p>")
        self.assertEqual(removals, [])


class TestMarkdownFormats(TestCase):
    def test_resolve_db_markdown_output(self):
        self.assertEqual(APIRichText.resolve_format("db_markdown"), "db_markdown")

    def test_resolve_markdown_output(self):
        self.assertEqual(APIRichText.resolve_format("markdown"), "markdown")

    def test_markdown_rejected_as_input(self):
        with self.assertRaises(RichTextFormatError):
            APIRichText.parse_input({"format": "markdown", "content": "# hi"})

    def test_db_markdown_input_converted_and_sanitised(self):
        db_html, removals = APIRichText.convert_input(
            {"format": "db_markdown", "content": "# Title\n\n<script>alert(1)</script>"}
        )
        self.assertNotIn("<script", db_html)
        self.assertTrue(
            any(r.tag == "h1" and r.reason == "feature_disabled" for r in removals)
        )

    def test_db_markdown_input_respects_field_features(self):
        # "link" is not in these features → external link unwrapped + reported
        db_html, removals = APIRichText.convert_input(
            {"format": "db_markdown", "content": "[x](https://example.com/)"},
            features=["bold"],
        )
        self.assertNotIn("<a", db_html)

    def test_serialize_db_markdown(self):
        result = APIRichText.serialize(
            '<p><a linktype="page" id="2">home</a></p>', format="db_markdown"
        )
        self.assertEqual(result, "[home](wagtail://page?id=2)\n\n")

    def test_serialize_markdown_resolved(self):
        result = APIRichText.serialize(
            '<p><a href="https://example.com/">x</a></p>', format="markdown"
        )
        self.assertEqual(result, "[x](https://example.com/)\n\n")

    def test_serialize_none_passthrough(self):
        self.assertIsNone(
            APIRichText.serialize(None, format="markdown", features=["h2"])
        )

    def test_features_forwarded_to_serializer(self):
        # features=[] means nothing converts → ContentstateConverter sees no
        # rules; output is plain text without heading markers.
        with_features = APIRichText.serialize(
            "<h2>T</h2>", format="db_markdown", features=["h2"]
        )
        self.assertIn("## T", with_features)

    @override_settings(WAGTAILAPI_RICH_TEXT_FORMAT="markdown")
    def test_setting_validation_accepts_new_formats(self):
        APIRichText.check_setting()
