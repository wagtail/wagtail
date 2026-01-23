from django.test import TestCase

from wagtail.documents import get_document_model
from wagtail.documents.blocks import DocumentChooserBlock

from .utils import get_test_document_file


class TestDocumentChooserBlock(TestCase):
    def test_deconstruct(self):
        block = DocumentChooserBlock(required=False)
        path, args, kwargs = block.deconstruct()
        self.assertEqual(path, "wagtail.documents.blocks.DocumentChooserBlock")
        self.assertEqual(args, ())
        self.assertEqual(kwargs, {"required": False})

    def test_extract_references(self):
        Document = get_document_model()
        document = Document.objects.create(
            title="Test document", file=get_test_document_file()
        )
        block = DocumentChooserBlock()

        self.assertListEqual(
            list(block.extract_references(document)),
            [(Document, str(document.id), "", "")],
        )

        # None should not yield any references
        self.assertListEqual(list(block.extract_references(None)), [])
