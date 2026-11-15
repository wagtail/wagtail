from unittest import mock
from urllib.parse import urlsplit

from django.contrib.auth.models import Group, Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models.signals import post_save
from django.test import override_settings
from django.urls import reverse

from wagtail.documents import get_document_model
from wagtail.documents.models import document_served
from wagtail.models import GroupCollectionPermission

from .base import TestV3DocumentsBase

Document = get_document_model()
FILE_CONTENTS = b"Test document contents"


class TestV3DocumentCreate(TestV3DocumentsBase):
    def post_document(self, **kwargs):
        data = {
            "file": SimpleUploadedFile("test.txt", FILE_CONTENTS),
        }
        data.update(kwargs)
        return self.client.post(reverse("wagtailapi_v3:create_document"), data)

    def grant_collection_permission(self, user, collection, codename="add_document"):
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
        response = self.post_document(title="Test")
        self.assert_problem_response(response, status_code=401)

    def test_superuser_can_create(self):
        user = self.login()
        response = self.post_document(title="Uploaded document")
        self.assertEqual(response.status_code, 201)
        content = response.json()
        document = Document.objects.get(id=content["id"])
        self.assertEqual(document.title, "Uploaded document")
        self.assertEqual(document.uploaded_by_user, user)
        self.assertEqual(document.file_size, len(FILE_CONTENTS))
        self.assertNotEqual(document.file_hash, "")
        self.assertIn("download_url", content["meta"])

    def test_missing_title_returns_422(self):
        self.login()
        self.assert_problem_response(self.post_document(), status_code=422)

    def test_missing_file_returns_422(self):
        self.login()
        response = self.client.post(
            reverse("wagtailapi_v3:create_document"),
            {"title": "No file"},
        )
        self.assert_problem_response(response, status_code=422)

    def test_user_without_add_permission_gets_403(self):
        user = self.create_user(username="noperms", password="password")
        self.authorize(user)
        response = self.post_document(title="Forbidden")
        self.assert_problem_response(
            response,
            status_code=403,
            detail_contains="Permission denied",
        )

    def test_single_permitted_collection_is_selected(self):
        user = self.create_user(username="adder", password="password")
        collection = self.create_collection("Only choice")
        self.grant_collection_permission(user, collection)
        self.authorize(user)
        response = self.post_document(title="In only choice")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            Document.objects.get(id=response.json()["id"]).collection_id,
            collection.id,
        )

    def test_missing_collection_with_multiple_choices_returns_422(self):
        user = self.create_user(username="multi", password="password")
        self.grant_collection_permission(user, self.create_collection("First"))
        self.grant_collection_permission(user, self.create_collection("Second"))
        self.authorize(user)
        response = self.post_document(title="Missing collection")
        self.assert_problem_response(
            response,
            status_code=422,
            errors=[{"loc": ["collection"]}],
        )

    def test_forbidden_collection_returns_422(self):
        user = self.create_user(username="limited", password="password")
        self.grant_collection_permission(user, self.create_collection("Allowed"))
        self.grant_collection_permission(user, self.create_collection("Also allowed"))
        forbidden = self.create_collection("Forbidden")
        self.authorize(user)
        response = self.post_document(
            title="Wrong collection",
            collection_id=forbidden.id,
        )
        self.assert_problem_response(
            response,
            status_code=422,
            errors=[{"loc": ["collection"]}],
        )

    def test_forbidden_collection_with_single_choice_returns_422(self):
        user = self.create_user(username="single-limited", password="password")
        self.grant_collection_permission(user, self.create_collection("Only allowed"))
        forbidden = self.create_collection("Forbidden")
        self.authorize(user)
        response = self.post_document(
            title="Wrong collection",
            collection_id=forbidden.id,
        )
        self.assert_problem_response(
            response,
            status_code=422,
            errors=[{"loc": ["collection"]}],
        )

    @override_settings(WAGTAILDOCS_EXTENSIONS=["pdf"])
    def test_bad_extension_returns_422(self):
        self.login()
        response = self.post_document(title="Wrong extension")
        self.assert_problem_response(
            response,
            status_code=422,
            errors=[{"loc": ["file"]}],
        )

    @override_settings(WAGTAILDOCS_MAX_UPLOAD_SIZE=10)
    def test_oversized_file_returns_422(self):
        self.login()
        response = self.post_document(title="Too large")
        self.assert_problem_response(
            response,
            status_code=422,
            errors=[{"loc": ["file"]}],
        )

    def test_audit_log(self):
        self.login()
        response = self.post_document(title="Logged")
        document = Document.objects.get(id=response.json()["id"])
        self.assert_log_actions(document, ["wagtail.create"])

    def test_post_save_signal_fires_once(self):
        handler = mock.MagicMock()
        post_save.connect(handler, sender=Document)
        try:
            self.login()
            response = self.post_document(title="Signalled")
            self.assertEqual(response.status_code, 201)
            self.assertEqual(handler.call_count, 1)
        finally:
            post_save.disconnect(handler, sender=Document)

    def test_api_uploaded_document_can_be_served(self):
        handler = mock.MagicMock()
        document_served.connect(handler)
        try:
            self.login()
            create_response = self.post_document(title="Served")
            url = create_response.json()["meta"]["download_url"]
            response = self.client.get(urlsplit(url).path)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(b"".join(response.streaming_content), FILE_CONTENTS)
            self.assertEqual(
                response["Content-Security-Policy"],
                "default-src 'none'",
            )
            self.assertEqual(response["X-Content-Type-Options"], "nosniff")
            self.assertEqual(handler.call_count, 1)
        finally:
            document_served.disconnect(handler)
