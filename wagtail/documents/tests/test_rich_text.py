from django.test import TestCase
from django.urls import reverse_lazy

from wagtail.documents import get_document_model
from wagtail.documents.rich_text import (
    DocumentLinkHandler as FrontendDocumentLinkHandler,
)
from wagtail.documents.rich_text.editor_html import (
    DocumentLinkHandler as EditorHtmlDocumentLinkHandler,
)
from wagtail.fields import RichTextField
from wagtail.rich_text.feature_registry import FeatureRegistry
from wagtail.test.utils import WagtailTestUtils


class TestEditorHtmlDocumentLinkHandler(WagtailTestUtils, TestCase):
    fixtures = ["test.json"]

    def test_get_db_attributes(self):
        soup = self.get_soup('<a data-id="test-id">foo</a>')
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

    def test_extract_references(self):
        self.assertEqual(
            list(
                RichTextField().extract_references(
                    '<a linktype="document" id="1">Link to a document</a>'
                )
            ),
            [(get_document_model(), "1", "", "")],
        )


class TestEntityFeatureChooserUrls(TestCase):
    def test_chooser_urls_exist(self):
        features = FeatureRegistry()
        document = features.get_editor_plugin("draftail", "document-link")

        self.assertIsNotNone(document.data.get("chooserUrls"))
        self.assertEqual(
            document.data["chooserUrls"]["documentChooser"],
            reverse_lazy("wagtaildocs_chooser:choose"),
        )
