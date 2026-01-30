from django.test import TestCase
from wagtail.admin.rich_text.converters.html_to_contentstate import PageLinkElementHandler
from wagtail.models import Page
from wagtail.test.utils import WagtailTestUtils


class TestPageLinkElementHandler(WagtailTestUtils, TestCase):
    def setUp(self):
        super().setUp()
        self.root_page = Page.objects.get(id=2)

    def test_get_attribute_data_with_missing_id(self):
        handler = PageLinkElementHandler(None)
        attrs = {"linktype": "page"}
        
        data = handler.get_attribute_data(attrs)
        
        self.assertEqual(data["id"], None)
        self.assertEqual(data["url"], None)
        self.assertEqual(data["parentId"], None)

    def test_get_attribute_data_with_nonexistent_id(self):
        handler = PageLinkElementHandler(None)
        attrs = {"linktype": "page", "id": 9999}
        
        data = handler.get_attribute_data(attrs)
        
        self.assertEqual(data["id"], 9999)
        self.assertEqual(data["url"], None)
        self.assertEqual(data["parentId"], None)

    def test_get_attribute_data_with_valid_page(self):
        handler = PageLinkElementHandler(None)
        attrs = {"linktype": "page", "id": self.root_page.id}
        
        data = handler.get_attribute_data(attrs)
        
        self.assertEqual(data["id"], self.root_page.id)
        self.assertEqual(data["url"], "/")
        # The default root page (id=2) has a parent (id=1)
        self.assertIsNotNone(data["parentId"])
