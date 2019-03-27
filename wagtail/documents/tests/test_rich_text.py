from bs4 import BeautifulSoup
from django.test import TestCase

from wagtail.documents.rich_text import DocumentLinkHandler as FrontendDocumentLinkHandler
from wagtail.documents.rich_text.editor_html import DocumentLinkHandler as EditorHtmlDocumentLinkHandler


class TestEditorHtmlDocumentLinkHandler(TestCase):
    fixtures = ['test.json']

    def test_get_db_attributes(self):
        soup = BeautifulSoup('<a data-id="test-id">foo</a>', 'html5lib')
        self.assertEqual(
            EditorHtmlDocumentLinkHandler.get_db_attributes(soup.a),
            {'id': 'test-id'}
        )

    def test_expand_db_attributes_for_editor(self):
        self.assertEqual(
            EditorHtmlDocumentLinkHandler.expand_db_attributes({'id': 1}),
            '<a data-linktype="document" data-id="1" href="/documents/1/test.pdf">'
        )

    def test_expand_db_attributes_for_editor_preserves_missing_id_of_nonexistent_document(self):
        self.assertEqual(
            EditorHtmlDocumentLinkHandler.expand_db_attributes({'id': 0}),
            '<a data-linktype="document" data-id="0">'
        )

    def test_expand_db_attributes_for_editor_with_missing_id(self):
        self.assertEqual(
            EditorHtmlDocumentLinkHandler.expand_db_attributes({}),
            '<a data-linktype="document">'
        )


class TestFrontendDocumentLinkHandler(TestCase):
    fixtures = ['test.json']

    def test_expand_db_attributes_for_frontend(self):
       self.assertEqual(
            FrontendDocumentLinkHandler.expand_db_attributes({'id': 1}),
            '<a href="/documents/1/test.pdf">'
        )

    def test_expand_db_attributes_for_frontend_with_nonexistent_document(self):
        self.assertEqual(
            FrontendDocumentLinkHandler.expand_db_attributes({'id': 0}),
            '<a>'
        )
