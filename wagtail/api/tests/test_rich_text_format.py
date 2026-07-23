from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings

from wagtail.api.rich_text import APIRichText, RichTextFormatError
from wagtail.api.v2.serializers import RichTextFieldSerializer
from wagtail.models import Page


class TestRichTextFormatResolution(SimpleTestCase):
    def setUp(self):
        self.request_factory = RequestFactory()

    def test_default_format_is_db_html(self):
        self.assertEqual(APIRichText.get_default_format(), APIRichText.DEFAULT_FORMAT)

    @override_settings(WAGTAILAPI_RICH_TEXT_FORMAT="html")
    def test_setting_overrides_default(self):
        self.assertEqual(APIRichText.get_default_format(), "html")

    @override_settings(WAGTAILAPI_RICH_TEXT_FORMAT="markdown")
    def test_setting_supports_markdown(self):
        self.assertEqual(APIRichText.get_default_format(), "markdown")

    @override_settings(WAGTAILAPI_RICH_TEXT_FORMAT="internal_markdown")
    def test_setting_supports_internal_markdown(self):
        self.assertEqual(APIRichText.get_default_format(), "internal_markdown")

    def test_query_parameter_overrides_setting(self):
        request = self.request_factory.get("/", {"rich_text_format": "html"})
        with override_settings(WAGTAILAPI_RICH_TEXT_FORMAT="db_html"):
            self.assertEqual(APIRichText.resolve_format(request), "html")

    def test_query_parameter_supports_markdown(self):
        request = self.request_factory.get("/", {"rich_text_format": "markdown"})
        self.assertEqual(APIRichText.resolve_format(request), "markdown")

    def test_query_parameter_supports_internal_markdown(self):
        request = self.request_factory.get(
            "/", {"rich_text_format": "internal_markdown"}
        )
        self.assertEqual(APIRichText.resolve_format(request), "internal_markdown")

    def test_invalid_query_parameter_raises(self):
        request = self.request_factory.get("/", {"rich_text_format": "unsupported"})
        with self.assertRaises(RichTextFormatError) as cm:
            APIRichText.resolve_format(request)
        self.assertIn("unsupported", str(cm.exception))
        # Error message lists the supported formats, including the new ones.
        self.assertIn("'markdown'", str(cm.exception))
        self.assertIn("'internal_markdown'", str(cm.exception))

    @override_settings(WAGTAILAPI_RICH_TEXT_FORMAT="invalid")
    def test_invalid_setting_raises(self):
        with self.assertRaises(RichTextFormatError) as cm:
            APIRichText.get_default_format()
        self.assertIn("invalid", str(cm.exception))


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
        result = APIRichText.serialize(value, format="html")
        self.assertIn('href="/events/"', result)
        self.assertNotIn("linktype=", result)

    def test_markdown_delegates_to_expand_db_html_to_markdown(self):
        # The API serialiser is a thin wrapper over
        # expand_db_html_to_markdown; detailed Markdown output is tested in
        # wagtail.tests.test_rich_text_markdown. Here we just verify the
        # dispatch produces Markdown, not DB HTML.
        page = Page.objects.get(url_path="/home/events/")
        value = f'<p><a linktype="page" id="{page.id}">Events</a></p>'
        result = APIRichText.serialize(value, format="markdown")
        self.assertIn("[Events](", result)
        self.assertNotIn("linktype=", result)
        self.assertNotIn("wagtail://", result)

    def test_internal_markdown_preserves_references(self):
        page = Page.objects.get(url_path="/home/events/")
        value = f'<p><a linktype="page" id="{page.id}">Events</a></p>'
        result = APIRichText.serialize(value, format="internal_markdown")
        self.assertIn(f"wagtail://page?id={page.id}", result)
        self.assertNotIn("linktype=", result)

    def test_none_returns_none(self):
        self.assertIsNone(APIRichText.serialize(None, format="html"))
        self.assertIsNone(APIRichText.serialize(None, format="markdown"))
        self.assertIsNone(APIRichText.serialize(None, format="internal_markdown"))


class TestRichTextFieldSerializer(SimpleTestCase):
    def test_accepts_text_field_kwargs(self):
        field = RichTextFieldSerializer(max_length=120)
        self.assertEqual(field.max_length, 120)
