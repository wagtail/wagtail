from django.test import TestCase
from django.urls import reverse_lazy

from wagtail.fields import RichTextField
from wagtail.images.rich_text import ImageEmbedHandler as FrontendImageEmbedHandler
from wagtail.images.rich_text.contentstate import ImageElementHandler
from wagtail.images.rich_text.editor_html import (
    ImageEmbedHandler as EditorHtmlImageEmbedHandler,
)
from wagtail.rich_text.feature_registry import FeatureRegistry
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


class TestEntityFeatureChooserUrls(TestCase):
    def test_chooser_urls_exist(self):
        features = FeatureRegistry()
        image = features.get_editor_plugin("draftail", "image")

        self.assertIsNotNone(image.data.get("chooserUrls"))
        self.assertEqual(
            image.data["chooserUrls"]["imageChooser"],
            reverse_lazy("wagtailimages_chooser:choose"),
        )


class TestImageElementHandler(WagtailTestUtils, TestCase):
    def setUp(self):
        self.image = Image.objects.create(
            id=1, title="Test", file=get_test_image_file()
        )
        self.handler = ImageElementHandler()

    def test_create_entity_with_valid_attrs(self):
        entity = self.handler.create_entity(
            "embed",
            {"id": "1", "format": "left", "alt": "A test image"},
            None,
            None,
        )
        self.assertEqual(entity.entity_type, "IMAGE")
        self.assertEqual(entity.mutability, "IMMUTABLE")
        self.assertEqual(entity.data["id"], "1")
        self.assertEqual(entity.data["format"], "left")
        self.assertEqual(entity.data["alt"], "A test image")
        self.assertTrue(
            entity.data["src"].endswith(".png") or "/images/" in entity.data["src"]
        )

    def test_create_entity_with_missing_id(self):
        # Reproduces issue where pasting broken embed or image+link has no 'id' in attrs
        entity = self.handler.create_entity(
            "embed",
            {"format": "left", "alt": "A test image"},
            None,
            None,
        )
        self.assertEqual(entity.entity_type, "IMAGE")
        self.assertIsNone(entity.data["id"])
        self.assertEqual(entity.data["src"], "")
        self.assertEqual(entity.data["format"], "left")

    def test_create_entity_with_missing_format(self):
        entity = self.handler.create_entity(
            "embed",
            {"id": "1", "alt": "A test image"},
            None,
            None,
        )
        self.assertEqual(entity.entity_type, "IMAGE")
        self.assertEqual(entity.data["id"], "1")
        self.assertEqual(entity.data["src"], "")
        self.assertIsNone(entity.data["format"])

    def test_create_entity_with_invalid_id(self):
        entity = self.handler.create_entity(
            "embed",
            {"id": "not-an-int", "format": "left"},
            None,
            None,
        )
        self.assertEqual(entity.entity_type, "IMAGE")
        self.assertEqual(entity.data["id"], "not-an-int")
        self.assertEqual(entity.data["src"], "")

    def test_create_entity_with_nonexistent_image(self):
        entity = self.handler.create_entity(
            "embed",
            {"id": "9999", "format": "left"},
            None,
            None,
        )
        self.assertEqual(entity.entity_type, "IMAGE")
        self.assertEqual(entity.data["id"], "9999")
        self.assertEqual(entity.data["src"], "")
