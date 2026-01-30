from django.test import TestCase

from wagtail.images.rich_text.contentstate import ImageElementHandler
from wagtail.test.utils import WagtailTestUtils

from .utils import Image, get_test_image_file


class TestImageElementHandler(WagtailTestUtils, TestCase):
    def test_create_entity_with_missing_id(self):
        handler = ImageElementHandler()
        attrs = {"format": "left", "alt": "Test Image"}
        
        entity = handler.create_entity("embed", attrs, None, None)
        
        self.assertEqual(entity.entity_type, "IMAGE")
        self.assertEqual(entity.mutability, "IMMUTABLE")
        self.assertEqual(entity.data["id"], None)
        self.assertEqual(entity.data["alt"], "Test Image")
        self.assertEqual(entity.data["format"], "left")
        self.assertEqual(entity.data["src"], "")

    def test_create_entity_with_missing_format(self):
        handler = ImageElementHandler()
        attrs = {"id": 1, "alt": "Test Image"}
        
        entity = handler.create_entity("embed", attrs, None, None)
        
        self.assertEqual(entity.entity_type, "IMAGE")
        self.assertEqual(entity.mutability, "IMMUTABLE")
        self.assertEqual(entity.data["id"], 1)
        self.assertEqual(entity.data["alt"], "Test Image")
        self.assertEqual(entity.data["format"], None)
        self.assertEqual(entity.data["src"], "")

    def test_create_entity_with_invalid_id(self):
        handler = ImageElementHandler()
        attrs = {"id": 9999, "format": "left", "alt": "Test Image"}
        
        entity = handler.create_entity("embed", attrs, None, None)
        
        self.assertEqual(entity.entity_type, "IMAGE")
        self.assertEqual(entity.mutability, "IMMUTABLE")
        self.assertEqual(entity.data["id"], 9999)
        self.assertEqual(entity.data["alt"], "Test Image")
        self.assertEqual(entity.data["format"], "left")
        self.assertEqual(entity.data["src"], "")

    def test_create_entity_with_valid_image(self):
        image = Image.objects.create(title="Test Image", file=get_test_image_file())
        handler = ImageElementHandler()
        attrs = {"id": image.id, "format": "left", "alt": "Test Image"}
        
        entity = handler.create_entity("embed", attrs, None, None)
        
        self.assertEqual(entity.entity_type, "IMAGE")
        self.assertEqual(entity.mutability, "IMMUTABLE")
        self.assertEqual(entity.data["id"], image.id)
        self.assertEqual(entity.data["alt"], "Test Image")
        self.assertEqual(entity.data["format"], "left")
        self.assertNotEqual(entity.data["src"], "")
