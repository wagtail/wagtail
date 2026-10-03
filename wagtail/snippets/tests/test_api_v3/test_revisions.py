from django.contrib.admin.utils import quote
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from wagtail.api.v3.tests.base import TestV3Base
from wagtail.test.testapp.models import (
    QUOTABLE_PK,
    Advert,
    DraftStateCustomPrimaryKeyModel,
    FullFeaturedSnippet,
)
from wagtail.test.utils import WagtailTestUtils


class TestV3SnippetRevisionsBase(TestV3Base, WagtailTestUtils, TestCase):
    model = FullFeaturedSnippet

    def setUp(self):
        super().setUp()
        self.snippet = FullFeaturedSnippet.objects.create(text="Original")

    def list_url(self, snippet):
        return reverse(
            "wagtailapi_v3:list_snippet_revisions",
            kwargs={"type": self.model._meta.label, "pk": snippet.pk},
        )

    def detail_url(self, snippet, revision):
        return reverse(
            "wagtailapi_v3:detail_snippet_revision",
            kwargs={
                "type": self.model._meta.label,
                "pk": snippet.pk,
                "revision_id": revision.pk,
            },
        )

    def login_with_permissions(self, *codenames, index=0):
        """
        Log in as a fresh non-superuser with exactly the given permission
        codenames on ``self.model``. Passing no codenames logs in a user with
        no permissions on the model at all. ``index`` keeps usernames unique
        within a single test method (e.g. across a permission_matrix loop).
        """
        username = f"user-{index}"
        user = self.create_user(username=username, password="password")
        for codename in codenames:
            user.user_permissions.add(
                Permission.objects.get(
                    content_type__app_label=self.model._meta.app_label,
                    codename=codename,
                )
            )
        self.login(username=username, password="password")
        return user


class TestV3SnippetRevisionsList(TestV3SnippetRevisionsBase):
    permission_matrix = [
        (None, 401),
        ([], 403),
        (["add_fullfeaturedsnippet"], 403),
        (["change_fullfeaturedsnippet"], 200),
    ]

    def test_permission_matrix(self):
        for i, (codenames, expected_status) in enumerate(self.permission_matrix):
            with self.subTest(codenames=codenames):
                if codenames is None:
                    self.unauthorize()
                else:
                    self.login_with_permissions(*codenames, index=i)

                response = self.client.get(self.list_url(self.snippet))
                self.assertEqual(response.status_code, expected_status)

    def test_list_revisions(self):
        user = self.login()
        first_revision = self.snippet.save_revision(user=user)
        second_revision = self.snippet.save_revision(user=user)

        response = self.client.get(self.list_url(self.snippet))
        self.assertEqual(response.status_code, 200)
        content = response.json()

        self.assertEqual(content["count"], 2)
        ids = [item["id"] for item in content["items"]]
        # Most recent revision first.
        self.assertEqual(ids, [second_revision.pk, first_revision.pk])

        item = content["items"][0]
        self.assertEqual(
            set(item.keys()),
            {
                "meta",
                "id",
                "object_id",
                "created_at",
                "user_id",
                "object_str",
                "approved_go_live_at",
            },
        )
        self.assertEqual(item["meta"], {"type": "wagtailcore.Revision"})
        self.assertEqual(item["id"], second_revision.pk)
        self.assertEqual(item["object_id"], str(self.snippet.pk))
        self.assertEqual(str(item["user_id"]), str(user.pk))
        self.assertEqual(item["object_str"], str(self.snippet))
        self.assertIsNone(item["approved_go_live_at"])

    def test_list_revisions_empty(self):
        self.login()
        response = self.client.get(self.list_url(self.snippet))
        self.assertEqual(response.status_code, 200)
        content = response.json()
        self.assertEqual(content["count"], 0)
        self.assertEqual(content["items"], [])

    def test_unknown_snippet_returns_404(self):
        self.login()
        response = self.client.get(
            reverse(
                "wagtailapi_v3:list_snippet_revisions",
                kwargs={"type": self.model._meta.label, "pk": 999999},
            )
        )
        self.assert_problem_response(response, status_code=404)

    def test_non_revisable_type_is_rejected(self):
        self.login()
        advert = Advert.objects.create(text="Hi")
        response = self.client.get(
            reverse(
                "wagtailapi_v3:list_snippet_revisions",
                kwargs={"type": "tests.Advert", "pk": advert.pk},
            )
        )
        self.assert_problem_response(
            response,
            status_code=422,
            detail_contains="Validation failed",
            errors=[{"type": "literal_error", "loc": ["path", "type"]}],
        )

    def test_list_revisions_with_quotable_pk(self):
        user = self.login()
        snippet = DraftStateCustomPrimaryKeyModel.objects.create(
            custom_id=QUOTABLE_PK, text="Original"
        )
        revision = snippet.save_revision(user=user)
        response = self.client.get(
            reverse(
                "wagtailapi_v3:list_snippet_revisions",
                kwargs={
                    "type": "tests.DraftStateCustomPrimaryKeyModel",
                    "pk": quote(snippet.pk),
                },
            )
        )
        self.assertEqual(response.status_code, 200)
        ids = [item["id"] for item in response.json()["items"]]
        self.assertEqual(ids, [revision.pk])


class TestV3SnippetRevisionsListFilters(TestV3SnippetRevisionsBase):
    def setUp(self):
        super().setUp()
        self.user = self.login()
        self.other_user = self.create_superuser(username="other")

        self.old_revision = self.snippet.save_revision(user=self.user)
        self.old_revision.created_at = "2020-01-01T00:00:00Z"
        self.old_revision.object_str = "Old title"
        self.old_revision.save()

        self.new_revision = self.snippet.save_revision(user=self.other_user)
        self.new_revision.created_at = "2024-06-01T00:00:00Z"
        self.new_revision.object_str = "New Title"
        self.new_revision.approved_go_live_at = "2024-06-02T00:00:00Z"
        self.new_revision.save()

    def get_ids(self, **params):
        response = self.client.get(self.list_url(self.snippet), params)
        self.assertEqual(response.status_code, 200)
        return {item["id"] for item in response.json()["items"]}

    def test_filter_created_at_from(self):
        self.assertEqual(
            self.get_ids(created_at_from="2022-01-01T00:00:00Z"),
            {self.new_revision.pk},
        )

    def test_filter_created_at_to(self):
        self.assertEqual(
            self.get_ids(created_at_to="2022-01-01T00:00:00Z"),
            {self.old_revision.pk},
        )

    def test_filter_user_id(self):
        self.assertEqual(
            self.get_ids(user_id=self.other_user.pk),
            {self.new_revision.pk},
        )

    def test_filter_approved_go_live_at_from(self):
        self.assertEqual(
            self.get_ids(approved_go_live_at_from="2024-01-01T00:00:00Z"),
            {self.new_revision.pk},
        )

    def test_filter_approved_go_live_at_to(self):
        self.assertEqual(
            self.get_ids(approved_go_live_at_to="2024-12-31T00:00:00Z"),
            {self.new_revision.pk},
        )

    def test_filter_object_str_icontains(self):
        self.assertEqual(
            self.get_ids(object_str="title"),
            {self.old_revision.pk, self.new_revision.pk},
        )
        self.assertEqual(
            self.get_ids(object_str="New"),
            {self.new_revision.pk},
        )


class TestV3SnippetRevisionsDetail(TestV3SnippetRevisionsBase):
    permission_matrix = [
        (None, 401),
        ([], 403),
        (["add_fullfeaturedsnippet"], 403),
        (["change_fullfeaturedsnippet"], 200),
    ]

    def test_permission_matrix(self):
        revision = self.snippet.save_revision()
        for i, (codenames, expected_status) in enumerate(self.permission_matrix):
            with self.subTest(codenames=codenames):
                if codenames is None:
                    self.unauthorize()
                else:
                    self.login_with_permissions(*codenames, index=i)

                response = self.client.get(self.detail_url(self.snippet, revision))
                self.assertEqual(response.status_code, expected_status)

    def test_detail(self):
        user = self.login()
        revision = self.snippet.save_revision(user=user)
        revision.refresh_from_db()

        response = self.client.get(self.detail_url(self.snippet, revision))
        self.assertEqual(response.status_code, 200)
        content = response.json()

        self.assertEqual(
            set(content.keys()),
            {
                "meta",
                "id",
                "object_id",
                "created_at",
                "user_id",
                "object_str",
                "approved_go_live_at",
                "content_type",
                "base_content_type",
                "content_object",
            },
        )
        self.assertEqual(content["meta"], {"type": "wagtailcore.Revision"})
        self.assertEqual(content["id"], revision.pk)
        self.assertEqual(
            content["content_type"],
            {
                "meta": {"type": "contenttypes.ContentType"},
                "id": revision.content_type_id,
                "name": "tests.FullFeaturedSnippet",
                "label": "full-featured snippet",
            },
        )
        self.assertEqual(
            content["base_content_type"],
            {
                "meta": {"type": "contenttypes.ContentType"},
                "id": revision.base_content_type_id,
                "name": "tests.FullFeaturedSnippet",
                "label": "full-featured snippet",
            },
        )
        self.assertEqual(content["content_object"]["id"], self.snippet.pk)
        self.assertEqual(content["content_object"]["text"], self.snippet.text)

    def test_unknown_snippet_returns_404(self):
        self.login()
        revision = self.snippet.save_revision()
        response = self.client.get(
            reverse(
                "wagtailapi_v3:detail_snippet_revision",
                kwargs={
                    "type": self.model._meta.label,
                    "pk": 999999,
                    "revision_id": revision.pk,
                },
            )
        )
        self.assert_problem_response(response, status_code=404)

    def test_unknown_revision_returns_404(self):
        self.login()
        response = self.client.get(
            reverse(
                "wagtailapi_v3:detail_snippet_revision",
                kwargs={
                    "type": self.model._meta.label,
                    "pk": self.snippet.pk,
                    "revision_id": 999999,
                },
            )
        )
        self.assert_problem_response(response, status_code=404)

    def test_revision_belonging_to_another_snippet_returns_404(self):
        self.login()
        other_snippet = FullFeaturedSnippet.objects.create(text="Other")
        other_revision = other_snippet.save_revision()

        response = self.client.get(self.detail_url(self.snippet, other_revision))
        self.assert_problem_response(response, status_code=404)

    def test_non_revisable_type_is_rejected(self):
        self.login()
        advert = Advert.objects.create(text="Hi")
        response = self.client.get(
            reverse(
                "wagtailapi_v3:detail_snippet_revision",
                kwargs={"type": "tests.Advert", "pk": advert.pk, "revision_id": 1},
            )
        )
        self.assert_problem_response(
            response,
            status_code=422,
            detail_contains="Validation failed",
            errors=[{"type": "literal_error", "loc": ["path", "type"]}],
        )

    def test_detail_with_quotable_pk(self):
        user = self.login()
        snippet = DraftStateCustomPrimaryKeyModel.objects.create(
            custom_id=QUOTABLE_PK, text="Original"
        )
        revision = snippet.save_revision(user=user)
        response = self.client.get(
            reverse(
                "wagtailapi_v3:detail_snippet_revision",
                kwargs={
                    "type": "tests.DraftStateCustomPrimaryKeyModel",
                    "pk": quote(snippet.pk),
                    "revision_id": revision.pk,
                },
            )
        )
        self.assertEqual(response.status_code, 200)
        content = response.json()
        self.assertEqual(content["content_object"]["custom_id"], QUOTABLE_PK)
        self.assertEqual(content["content_object"]["text"], "Original")
