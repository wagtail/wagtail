from bs4 import BeautifulSoup
from django.test import TestCase

from wagtail.documents.rich_text import DocumentLinkHandler


class TestDocumentRichTextLinkHandler(TestCase):
    fixtures = ['test.json']

    def test_get_db_attributes(self):
        soup = BeautifulSoup('<a data-id="test-id">foo</a>', 'html5lib')
        tag = soup.a
        result = DocumentLinkHandler.get_db_attributes(tag)
        self.assertEqual(result,
                         {'id': 'test-id'})

    def test_to_frontend_open_tag_document_does_not_exist(self):
        result = DocumentLinkHandler.to_frontend_open_tag({'id': 0})
        self.assertEqual(result, '<a>')

    def test_to_editor_open_tag_for_editor(self):
        result = DocumentLinkHandler.to_editor_open_tag({'id': 1})
        self.assertEqual(result,
                         '<a data-id="1" data-linktype="document" href="/documents/1/test.pdf">')

    def test_to_frontend_open_tag(self):
        result = DocumentLinkHandler.to_frontend_open_tag({'id': 1})
        self.assertEqual(result,
                         '<a href="/documents/1/test.pdf">')
