from django.urls import reverse

from wagtail.models import CollectionViewRestriction

from .base import TestV3DocumentsBase


class TestV3DocumentDetail(TestV3DocumentsBase):
    def get_response(self, document_id):
        return self.client.get(
            reverse(
                "wagtailapi_v3:detail_document",
                kwargs={"document_id": document_id},
            )
        )

    def test_anonymous_can_get_detail(self):
        document = self.create_document(title="Public document")
        response = self.get_response(document.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], document.id)
        self.assertEqual(response.json()["title"], "Public document")

    def test_direct_restriction_returns_404(self):
        collection = self.create_collection("Restricted")
        document = self.create_document(collection=collection)
        CollectionViewRestriction.objects.create(
            collection=collection,
            restriction_type=CollectionViewRestriction.LOGIN,
        )
        self.assertEqual(self.get_response(document.id).status_code, 404)

    def test_ancestor_restriction_returns_404(self):
        parent = self.create_collection("Restricted parent")
        child = self.create_collection("Child", parent=parent)
        document = self.create_document(collection=child)
        CollectionViewRestriction.objects.create(
            collection=parent,
            restriction_type=CollectionViewRestriction.LOGIN,
        )
        self.assertEqual(self.get_response(document.id).status_code, 404)

    def test_unknown_id_returns_404(self):
        self.assertEqual(self.get_response(999999).status_code, 404)
