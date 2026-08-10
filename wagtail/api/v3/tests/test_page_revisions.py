from django.contrib.auth.models import Group, Permission
from django.test import TestCase
from django.urls import reverse

from wagtail.api.v3.tests.base import TestV3Base
from wagtail.models import GroupPagePermission
from wagtail.test.utils import Page, WagtailTestUtils


class TestV3PageRevisionsBase(TestV3Base, WagtailTestUtils, TestCase):
    def setUp(self):
        super().setUp()
        self.root_page = Page.objects.get(depth=1)
        self.home_page = Page.objects.get(depth=2)

    def list_url(self, page):
        return reverse("wagtailapi_v3:list_page_revisions", kwargs={"page_id": page.pk})

    def detail_url(self, page, revision):
        return reverse(
            "wagtailapi_v3:detail_page_revision",
            kwargs={"page_id": page.pk, "revision_id": revision.pk},
        )

    def login_with_permissions(self, *codenames, index=0, scope=None):
        """
        Log in as a fresh non-superuser with exactly the given
        GroupPagePermission codenames granted on ``scope`` (default:
        ``self.root_page``, i.e. the whole tree). Passing no codenames logs
        in a user with no page permissions at all. ``index`` (e.g. the row
        number in a permission_matrix loop) keeps usernames unique within a
        single test method.
        """
        scope = scope or self.root_page
        username = f"user-{index}"
        user = self.create_user(username=username, password="password")
        if codenames:
            group = Group.objects.create(name=f"Test group ({username})")
            user.groups.add(group)
            for codename in codenames:
                GroupPagePermission.objects.create(
                    group=group,
                    page=scope,
                    permission=Permission.objects.get(
                        content_type__app_label=Page._meta.app_label, codename=codename
                    ),
                )
        self.login(username=getattr(user, user.USERNAME_FIELD), password="password")
        return user


class TestV3PageRevisionsList(TestV3PageRevisionsBase):
    # Viewing revisions requires "publish" or "change" and nothing less.
    permission_matrix = [
        (None, 401),
        ([], 403),
        ([Page.PERMISSION_CODENAMES.ADD], 403),
        ([Page.PERMISSION_CODENAMES.CHANGE], 200),
        ([Page.PERMISSION_CODENAMES.PUBLISH], 200),
    ]

    def test_permission_matrix(self):
        for i, (codenames, expected_status) in enumerate(self.permission_matrix):
            with self.subTest(codenames=codenames):
                if codenames is None:
                    self.client.logout()
                else:
                    self.login_with_permissions(*codenames, index=i)

                response = self.client.get(self.list_url(self.home_page))
                self.assertEqual(response.status_code, expected_status)

    def test_list_revisions(self):
        user = self.login()
        first_revision = self.home_page.save_revision(user=user)
        second_revision = self.home_page.save_revision(user=user)

        response = self.client.get(self.list_url(self.home_page))
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
        self.assertEqual(item["meta"]["type"], "wagtailcore.Revision")
        self.assertEqual(item["id"], second_revision.pk)
        self.assertEqual(item["object_id"], str(self.home_page.pk))
        self.assertEqual(str(item["user_id"]), str(user.pk))
        self.assertEqual(item["object_str"], str(self.home_page))
        self.assertIsNone(item["approved_go_live_at"])

    def test_list_revisions_empty(self):
        self.login()
        response = self.client.get(self.list_url(self.home_page))
        self.assertEqual(response.status_code, 200)
        content = response.json()
        self.assertEqual(content["count"], 0)
        self.assertEqual(content["items"], [])

    def test_unknown_page_returns_404(self):
        response = self.client.get(
            reverse("wagtailapi_v3:list_page_revisions", kwargs={"page_id": 999999})
        )
        self.assert_problem_response(response, status_code=404)


class TestV3PageRevisionsDetail(TestV3PageRevisionsBase):
    # Viewing a revision requires "publish" or "change" and nothing less.
    permission_matrix = [
        (None, 401),
        ([], 403),
        ([Page.PERMISSION_CODENAMES.ADD], 403),
        ([Page.PERMISSION_CODENAMES.CHANGE], 200),
        ([Page.PERMISSION_CODENAMES.PUBLISH], 200),
    ]

    def test_permission_matrix(self):
        revision = self.home_page.save_revision()
        for i, (codenames, expected_status) in enumerate(self.permission_matrix):
            with self.subTest(codenames=codenames):
                if codenames is None:
                    self.client.logout()
                else:
                    self.login_with_permissions(*codenames, index=i)

                response = self.client.get(self.detail_url(self.home_page, revision))
                self.assertEqual(response.status_code, expected_status)

    def test_detail(self):
        user = self.login()
        revision = self.home_page.save_revision(user=user)

        response = self.client.get(self.detail_url(self.home_page, revision))
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
                "content",
            },
        )
        self.assertEqual(content["meta"]["type"], "wagtailcore.Revision")
        self.assertEqual(content["id"], revision.pk)
        self.assertEqual(
            content["content_type"],
            {
                "meta": {"type": "contenttypes.ContentType"},
                "id": revision.content_type_id,
                "name": Page._meta.label,
                "label": "page",
            },
        )
        self.assertEqual(
            content["base_content_type"],
            {
                "meta": {"type": "contenttypes.ContentType"},
                "id": revision.base_content_type_id,
                "name": Page._meta.label,
                "label": "page",
            },
        )
        self.assertEqual(content["content"], revision.content)

    def test_unknown_page_returns_404(self):
        revision = self.home_page.save_revision()
        response = self.client.get(
            reverse(
                "wagtailapi_v3:detail_page_revision",
                kwargs={"page_id": 999999, "revision_id": revision.pk},
            )
        )
        self.assert_problem_response(response, status_code=404)

    def test_unknown_revision_returns_404(self):
        self.login()
        response = self.client.get(
            reverse(
                "wagtailapi_v3:detail_page_revision",
                kwargs={"page_id": self.home_page.pk, "revision_id": 999999},
            )
        )
        self.assert_problem_response(response, status_code=404)

    def test_revision_belonging_to_another_page_returns_404(self):
        self.login()
        other_page = self.home_page.add_child(
            instance=Page(title="Other", slug="other")
        )
        other_revision = other_page.save_revision()

        response = self.client.get(self.detail_url(self.home_page, other_revision))
        self.assert_problem_response(response, status_code=404)
