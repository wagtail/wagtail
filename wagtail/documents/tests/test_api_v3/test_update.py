import json
from unittest import mock

from django.contrib.auth.models import Group, Permission
from django.db.models.signals import post_save
from django.urls import reverse

from wagtail.documents import get_document_model
from wagtail.models import GroupCollectionPermission

from .base import TestV3DocumentsBase

Document = get_document_model()


class TestV3DocumentUpdate(TestV3DocumentsBase):
    def setUp(self):
        super().setUp()
        self.document = self.create_document(title="Original")

    def patch(self, document_id, data):
        return self.client.patch(
            reverse(
                "wagtailapi_v3:update_document",
                kwargs={"document_id": document_id},
            ),
            data=json.dumps(data),
            content_type="application/json",
        )

    def grant_permission(self, user, collection, codename):
        group = Group.objects.create(
            name=f"{user.get_username()}-{collection.pk}-{codename}"
        )
        user.groups.add(group)
        permission = Permission.objects.get(
            content_type__app_label="wagtaildocs",
            codename=codename,
        )
        GroupCollectionPermission.objects.create(
            group=group,
            collection=collection,
            permission=permission,
        )

    def test_anonymous_returns_401(self):
        response = self.patch(self.document.id, {"title": "Changed"})
        self.assert_problem_response(response, status_code=401)

    def test_superuser_can_update_title(self):
        self.login()
        response = self.patch(self.document.id, {"title": "Changed"})
        self.assertEqual(response.status_code, 200)
        self.document.refresh_from_db()
        self.assertEqual(self.document.title, "Changed")

    def test_partial_update_leaves_collection_and_file_unchanged(self):
        self.login()
        original = (
            self.document.collection_id,
            self.document.file.name,
            self.document.file_hash,
            self.document.file_size,
        )
        response = self.patch(self.document.id, {"title": "Metadata only"})
        self.assertEqual(response.status_code, 200)
        self.document.refresh_from_db()
        self.assertEqual(
            (
                self.document.collection_id,
                self.document.file.name,
                self.document.file_hash,
                self.document.file_size,
            ),
            original,
        )

    def test_update_collection_to_permitted_collection(self):
        user = self.create_user(username="editor", password="password")
        old_collection = self.document.collection
        new_collection = self.create_collection("New home")
        self.grant_permission(user, old_collection, "change_document")
        self.grant_permission(user, new_collection, "add_document")
        self.authorize(user)
        response = self.patch(
            self.document.id,
            {"collection_id": new_collection.id},
        )
        self.assertEqual(response.status_code, 200)
        self.document.refresh_from_db()
        self.assertEqual(self.document.collection_id, new_collection.id)

    def test_update_to_forbidden_collection_returns_422(self):
        user = self.create_user(username="limited-editor", password="password")
        self.grant_permission(user, self.document.collection, "change_document")
        self.grant_permission(user, self.create_collection("Allowed"), "add_document")
        self.grant_permission(
            user,
            self.create_collection("Also allowed"),
            "add_document",
        )
        forbidden = self.create_collection("Forbidden")
        self.authorize(user)
        response = self.patch(
            self.document.id,
            {"collection_id": forbidden.id},
        )
        self.assert_problem_response(
            response,
            status_code=422,
            errors=[{"loc": ["collection"]}],
        )

    def test_update_to_forbidden_collection_with_single_choice_returns_422(self):
        user = self.create_user(username="single-choice-editor", password="password")
        self.grant_permission(user, self.document.collection, "change_document")
        forbidden = self.create_collection("Forbidden")
        self.authorize(user)
        response = self.patch(
            self.document.id,
            {"collection_id": forbidden.id},
        )
        self.assert_problem_response(
            response,
            status_code=422,
            errors=[{"loc": ["collection"]}],
        )

    def test_uploader_with_add_permission_can_edit_own_document(self):
        user = self.create_user(username="uploader", password="password")
        self.grant_permission(user, self.document.collection, "add_document")
        self.document.uploaded_by_user = user
        self.document.save(update_fields=["uploaded_by_user"])
        self.authorize(user)
        response = self.patch(self.document.id, {"title": "Mine"})
        self.assertEqual(response.status_code, 200)

    def test_cannot_edit_other_users_document_without_change_permission(self):
        owner = self.create_user(username="owner", password="password")
        user = self.create_user(username="other", password="password")
        self.grant_permission(user, self.document.collection, "add_document")
        self.document.uploaded_by_user = owner
        self.document.save(update_fields=["uploaded_by_user"])
        self.authorize(user)
        response = self.patch(self.document.id, {"title": "Not mine"})
        self.assert_problem_response(
            response,
            status_code=403,
            detail_contains=(
                "You do not have permission to perform the 'edit' "
                "action on this object."
            ),
        )

    def test_unknown_id_returns_404(self):
        self.login()
        self.assertEqual(self.patch(999999, {"title": "Missing"}).status_code, 404)

    def test_audit_log(self):
        self.login()
        self.patch(self.document.id, {"title": "Logged"})
        self.assert_log_actions(self.document, ["wagtail.edit"])

    def test_post_save_signal_fires_once(self):
        handler = mock.MagicMock()
        post_save.connect(handler, sender=Document)
        try:
            self.login()
            response = self.patch(self.document.id, {"title": "Signalled"})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(handler.call_count, 1)
        finally:
            post_save.disconnect(handler, sender=Document)
