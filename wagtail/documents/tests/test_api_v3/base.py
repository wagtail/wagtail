from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from wagtail.api.v3.tests.base import TestV3Base
from wagtail.documents import get_document_model
from wagtail.test.utils import WagtailTestUtils
from wagtail.test.utils.wagtail_factories import CollectionFactory

Document = get_document_model()


class TestV3DocumentsBase(TestV3Base, WagtailTestUtils, TestCase):
    def create_document(self, **kwargs):
        defaults = {
            "title": "Test document",
            "file": SimpleUploadedFile("test.txt", b"Test document contents"),
        }
        defaults.update(kwargs)
        return Document.objects.create(**defaults)

    def create_collection(self, name="Test collection", parent=None):

        return CollectionFactory.create(name=name, parent=parent)
