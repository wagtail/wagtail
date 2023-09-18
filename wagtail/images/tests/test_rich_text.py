from django.test import TestCase

from wagtail.fields import RichTextField
from wagtail.images.rich_text import ImageEmbedHandler as FrontendImageEmbedHandler
from wagtail.images.rich_text.editor_html import (
    ImageEmbedHandler as EditorHtmlImageEmbedHandler,
)
from wagtail.test.utils import WagtailTestUtils

from .utils import Image, get_test_image_file


class TestEditorHtmlImageEmbedHandler(WagtailTestUtils, TestCase):
    def test_get_db_attributes(self):
        soup = self.get_soup(
            '<b data-id="test-id" data-format="test-format" data-alt="test-alt">foo</b>',
        )
        tag = soup.b
        result = EditorHtmlImageEmbedHandler.get_db_attributes(tag)
        self.assertEqual(
            result,
            {
                "alt": "test-alt",
                "id": "test-id",
                "format": "test-format",
            },
        )

    def test_expand_db_attributes_for_editor(self):
        Image.objects.create(id=1, title="Test", file=get_test_image_file())
        result = EditorHtmlImageEmbedHandler.expand_db_attributes(
            {
                "id": 1,
                "alt": "test-alt",
                "format": "left",
            }
        )
        self.assertTagInHTML(
            (
                '<img data-embedtype="image" data-id="1" data-format="left" '
                'data-alt="test-alt" class="richtext-image left" />'
            ),
            result,
            allow_extra_attrs=True,
        )

    def test_expand_db_attributes_for_editor_nonexistent_image(self):
        self.assertEqual(
            EditorHtmlImageEmbedHandler.expand_db_attributes({"id": 0}), '<img alt="">'
        )

    def test_expand_db_attributes_for_editor_escapes_alt_text(self):
        Image.objects.create(id=1, title="Test", file=get_test_image_file())
        result = EditorHtmlImageEmbedHandler.expand_db_attributes(
            {
                "id": 1,
                "alt": 'Arthur "two sheds" Jackson',
                "format": "left",
            }
        )

        self.assertTagInHTML(
            (
                '<img data-embedtype="image" data-id="1" data-format="left" '
                'data-alt="Arthur &quot;two sheds&quot; Jackson" class="richtext-image left" />'
            ),
            result,
            allow_extra_attrs=True,
        )

        self.assertIn('alt="Arthur &quot;two sheds&quot; Jackson"', result)

    def test_expand_db_attributes_for_editor_with_missing_alt(self):
        Image.objects.create(id=1, title="Test", file=get_test_image_file())
        result = EditorHtmlImageEmbedHandler.expand_db_attributes(
            {
                "id": 1,
                "format": "left",
            }
        )
        self.assertTagInHTML(
            (
                '<img data-embedtype="image" data-id="1" data-format="left" data-alt="" '
                'class="richtext-image left" />'
            ),
            result,
            allow_extra_attrs=True,
        )


class TestFrontendImageEmbedHandler(WagtailTestUtils, TestCase):
    def test_expand_db_attributes_for_frontend(self):
        Image.objects.create(id=1, title="Test", file=get_test_image_file())
        result = FrontendImageEmbedHandler.expand_db_attributes(
            {
                "id": 1,
                "alt": "test-alt",
                "format": "left",
            }
        )
        self.assertTagInHTML(
            '<img class="richtext-image left" />', result, allow_extra_attrs=True
        )

    def test_expand_db_attributes_for_frontend_with_nonexistent_image(self):
        result = FrontendImageEmbedHandler.expand_db_attributes({"id": 0})
        self.assertEqual(result, '<img alt="">')

    def test_expand_db_attributes_for_frontend_escapes_alt_text(self):
        Image.objects.create(id=1, title="Test", file=get_test_image_file())
        result = FrontendImageEmbedHandler.expand_db_attributes(
            {
                "id": 1,
                "alt": 'Arthur "two sheds" Jackson',
                "format": "left",
            }
        )
        self.assertIn('alt="Arthur &quot;two sheds&quot; Jackson"', result)

    def test_expand_db_attributes_for_frontend_with_missing_alt(self):
        Image.objects.create(id=1, title="Test", file=get_test_image_file())
        result = FrontendImageEmbedHandler.expand_db_attributes(
            {
                "id": 1,
                "format": "left",
            }
        )
        self.assertTagInHTML(
            '<img class="richtext-image left" alt="" />', result, allow_extra_attrs=True
        )


class TestExtractReferencesWithImage(WagtailTestUtils, TestCase):
    def test_extract_references(self):
        self.assertEqual(
            list(
                RichTextField().extract_references(
                    '<embed alt="Olivia Ava" embedtype="image" format="left" id="52"/>'
                )
            ),
            [(Image, "52", "", "")],
        )
