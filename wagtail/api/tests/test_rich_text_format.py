from django.test import SimpleTestCase, TestCase, override_settings

from wagtail.api.rich_text import APIRichText, RichTextFormatError
from wagtail.api.v2.serializers import RichTextFieldSerializer
from wagtail.models import Page


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
        request = self.request_factory.get("/", {"rich_text_format": "invalid"})
        with self.assertRaises(RichTextFormatError) as cm:
            APIRichText.resolve_format(request)
        self.assertIn("invalid", str(cm.exception))

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
