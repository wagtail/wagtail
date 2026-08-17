from unittest import mock

from django.contrib.auth.models import Group, Permission
from django.db.models.signals import post_delete
from django.urls import reverse

from wagtail.documents import get_document_model
from wagtail.models import GroupCollectionPermission

from .base import TestV3DocumentsBase

Document = get_document_model()


class TestV3DocumentDelete(TestV3DocumentsBase):
    def delete(self, document_id):
        return self.client.delete(
            reverse(
                "wagtailapi_v3:delete_document",
                kwargs={"document_id": document_id},
            )
        )

    def grant_add_permission(self, user, collection):
        group = Group.objects.create(name=f"{user.get_username()}-{collection.pk}-add")
        user.groups.add(group)
        permission = Permission.objects.get(
            content_type__app_label="wagtaildocs",
            codename="add_document",
        )
        GroupCollectionPermission.objects.create(
            group=group,
            collection=collection,
            permission=permission,
        )

    def test_anonymous_returns_401(self):
        document = self.create_document()
        self.assert_problem_response(self.delete(document.id), status_code=401)

    def test_superuser_can_delete(self):
        self.login()
        document = self.create_document()
        response = self.delete(document.id)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Document.objects.filter(id=document.id).exists())

    def test_user_without_delete_permission_gets_403(self):
        document = self.create_document()
        user = self.create_user(username="other", password="password")
        self.grant_add_permission(user, document.collection)
        self.authorize(user)
        response = self.delete(document.id)
        self.assert_problem_response(
            response,
            status_code=403,
            detail_contains=(
                "You do not have permission to perform the 'delete' "
                "action on this object."
            ),
        )

    def test_uploader_with_add_permission_can_delete_own_document(self):
        user = self.create_user(username="uploader", password="password")
        document = self.create_document(uploaded_by_user=user)
        self.grant_add_permission(user, document.collection)
        self.authorize(user)
        response = self.delete(document.id)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Document.objects.filter(id=document.id).exists())

    def test_unknown_id_returns_404(self):
        self.login()
        self.assertEqual(self.delete(999999).status_code, 404)

    def test_audit_log(self):
        self.login()
        document = self.create_document(title="Logged")
        self.delete(document.id)
        self.assert_log_actions(document, ["wagtail.delete"])

    def test_post_delete_signal_fires_once(self):
        handler = mock.MagicMock()
        post_delete.connect(handler, sender=Document)
        try:
            self.login()
            document = self.create_document()
            response = self.delete(document.id)
            self.assertEqual(response.status_code, 204)
            self.assertEqual(handler.call_count, 1)
        finally:
            post_delete.disconnect(handler, sender=Document)

    def test_stored_file_is_deleted_on_commit(self):
        self.login()
        document = self.create_document()
        storage = document.file.storage
        name = document.file.name
        self.assertTrue(storage.exists(name))
        with self.captureOnCommitCallbacks(execute=True):
            response = self.delete(document.id)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(storage.exists(name))
