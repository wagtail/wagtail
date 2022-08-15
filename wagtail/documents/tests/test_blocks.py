from django.test import TestCase

from wagtail.documents.blocks import DocumentChooserBlock


class TestDocumentChooserBlock(TestCase):
    def test_deconstruct(self):
        block = DocumentChooserBlock(required=False)
        path, args, kwargs = block.deconstruct()
        self.assertEqual(path, "wagtail.documents.blocks.DocumentChooserBlock")
        self.assertEqual(args, ())
        self.assertEqual(kwargs, {"required": False})
