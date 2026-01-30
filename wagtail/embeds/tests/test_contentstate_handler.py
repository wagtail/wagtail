from django.test import TestCase

from wagtail.embeds.rich_text.contentstate import MediaEmbedElementHandler
from wagtail.test.utils import WagtailTestUtils


class TestMediaEmbedElementHandler(WagtailTestUtils, TestCase):
    def test_create_entity_with_missing_url(self):
        handler = MediaEmbedElementHandler()
        attrs = {"embedtype": "media"}
        
        entity = handler.create_entity("embed", attrs, None, None)
        
        self.assertEqual(entity.entity_type, "EMBED")
        self.assertEqual(entity.mutability, "IMMUTABLE")
        self.assertEqual(entity.data["url"], None)

    def test_create_entity_with_url(self):
        # Note: We aren't testing actual embed retrieval here, just that the URL is passed through
        # appropriately to the exception handler which defaults to basic data if retrieval fails
        handler = MediaEmbedElementHandler()
        attrs = {"embedtype": "media", "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
        
        entity = handler.create_entity("embed", attrs, None, None)
        
        self.assertEqual(entity.entity_type, "EMBED")
        self.assertEqual(entity.mutability, "IMMUTABLE")
        self.assertEqual(entity.data["url"], "https://www.youtube.com/watch?v=dQw4w9WgXcQ")
