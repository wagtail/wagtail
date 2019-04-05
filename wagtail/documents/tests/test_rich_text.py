from bs4 import BeautifulSoup
from django.test import TestCase

from wagtail.documents.rich_text import DocumentLinkHandler as DocumentFrontendHandler
from wagtail.documents.rich_text.editor_html import DocumentLinkHandler as DocumentEditorHTMLHandler


class TestDocumentRichTextLinkHandler(TestCase):
    fixtures = ['test.json']

    def test_get_db_attributes(self):
        soup = BeautifulSoup('<a data-id="test-id">foo</a>', 'html5lib')
        tag = soup.a
        result = DocumentEditorHTMLHandler.get_db_attributes(tag)
        self.assertEqual(result,
                         {'id': 'test-id'})

    def test_expand_db_attributes(self):
        result = DocumentFrontendHandler.expand_db_attributes({'id': 1})
        self.assertEqual(result,
                         '<a href="/documents/1/test.pdf">')

    def test_expand_db_attributes_document_does_not_exist(self):
        result = DocumentFrontendHandler.expand_db_attributes({'id': 0})
        self.assertEqual(result, '<a>')

    def test_expand_db_attributes_with_missing_id(self):
        result = DocumentFrontendHandler.expand_db_attributes({})
        self.assertEqual(result, '<a>')

    def test_expand_db_attributes_for_editor(self):
        result = DocumentEditorHTMLHandler.expand_db_attributes({'id': 1})
        self.assertEqual(result,
                         '<a data-linktype="document" data-id="1" href="/documents/1/test.pdf">')

    def test_expand_db_attributes_for_editor_preserves_id_of_nonexistent_document(self):
        result = DocumentEditorHTMLHandler.expand_db_attributes({'id': 0})
        self.assertEqual(result,
                         '<a data-linktype="document" data-id="0">')

    def test_expand_db_attributes_for_editor_with_missing_id(self):
        result = DocumentEditorHTMLHandler.expand_db_attributes({})
        self.assertEqual(result, '<a data-linktype="document">')
