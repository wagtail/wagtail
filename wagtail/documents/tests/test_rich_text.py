from bs4 import BeautifulSoup
from django.test import TestCase

from wagtail.documents.rich_text import (
    DocumentLinkHandler as FrontendDocumentLinkHandler,
)
from wagtail.documents.rich_text.editor_html import (
    DocumentLinkHandler as EditorHtmlDocumentLinkHandler,
)


class TestEditorHtmlDocumentLinkHandler(TestCase):
    fixtures = ["test.json"]

    def test_get_db_attributes(self):
        soup = BeautifulSoup('<a data-id="test-id">foo</a>', "html5lib")
        tag = soup.a
        result = EditorHtmlDocumentLinkHandler.get_db_attributes(tag)
        self.assertEqual(result, {"id": "test-id"})

    def test_expand_db_attributes_for_editor(self):
        result = EditorHtmlDocumentLinkHandler.expand_db_attributes({"id": 1})
        self.assertEqual(
            result,
            '<a data-linktype="document" data-id="1" href="/documents/1/test.pdf">',
        )

    def test_expand_db_attributes_for_editor_preserves_id_of_nonexistent_document(self):
        result = EditorHtmlDocumentLinkHandler.expand_db_attributes({"id": 0})
        self.assertEqual(result, '<a data-linktype="document" data-id="0">')

    def test_expand_db_attributes_for_editor_with_missing_id(self):
        result = EditorHtmlDocumentLinkHandler.expand_db_attributes({})
        self.assertEqual(result, '<a data-linktype="document">')


class TestFrontendDocumentLinkHandler(TestCase):
    fixtures = ["test.json"]

    def test_expand_db_attributes_for_frontend(self):
        result = FrontendDocumentLinkHandler.expand_db_attributes({"id": 1})
        self.assertEqual(result, '<a href="/documents/1/test.pdf">')

    def test_expand_db_attributes_document_does_not_exist(self):
        result = FrontendDocumentLinkHandler.expand_db_attributes({"id": 0})
        self.assertEqual(result, "<a>")

    def test_expand_db_attributes_with_missing_id(self):
        result = FrontendDocumentLinkHandler.expand_db_attributes({})
        self.assertEqual(result, "<a>")
