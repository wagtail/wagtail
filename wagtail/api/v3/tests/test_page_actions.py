import json

from django.contrib.auth.models import AnonymousUser, Group, Permission
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from wagtail.api.v3.tests.base import TestV3Base
from wagtail.models import GroupPagePermission, Page
from wagtail.test.testapp.models import SimplePage
from wagtail.test.utils import WagtailTestUtils


class TestV3PageActionsBase(TestV3Base, WagtailTestUtils, TestCase):
    def setUp(self):
        super().setUp()
        self.root_page = Page.objects.get(depth=1)
        self.home_page = Page.objects.get(depth=2)

    def add_simple_page(self, parent, **kwargs):
        kwargs.setdefault("content", "some content")
        return parent.add_child(instance=SimplePage(**kwargs))

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
                        content_type__app_label="wagtailcore", codename=codename
                    ),
                )
        self.login(username=user.username, password="password")
        return user


class TestV3PagePublish(TestV3PageActionsBase):
    # Publishing requires "publish" and nothing less.
    permission_matrix = [
        (None, 401),
        ([], 403),
        (["add_page"], 403),
        (["publish_page"], 200),
    ]

    def post(self, page):
        return self.client.post(
            reverse("wagtailapi_v3:pages_actions_publish", kwargs={"page_id": page.pk})
        )

    def test_permission_matrix(self):
        for i, (codenames, expected_status) in enumerate(self.permission_matrix):
            with self.subTest(codenames=codenames):
                page = self.add_simple_page(
                    self.home_page,
                    title="Draft",
                    slug=f"draft-{i}",
                    live=False,
                )
                if codenames is None:
                    self.client.logout()
                else:
                    self.login_with_permissions(*codenames, index=i)

                since = timezone.now()
                response = self.post(page)

                self.assertEqual(response.status_code, expected_status)
                page.refresh_from_db()
                if expected_status == 200:
                    self.assertTrue(page.live)
                    self.assert_log_actions(page, ["wagtail.publish"], since=since)
                else:
                    self.assertFalse(page.live)

    def test_publish_page_with_no_revision_creates_one(self):
        page = self.add_simple_page(
            self.home_page, title="Draft", slug="draft", live=False
        )
        self.login_with_permissions("publish_page")
        self.assertIsNone(page.get_latest_revision())
        response = self.post(page)
        self.assertEqual(response.status_code, 200)
        page.refresh_from_db()
        self.assertTrue(page.live)
        self.assertIsNotNone(page.get_latest_revision())

    def test_unknown_page_returns_404(self):
        self.login_with_permissions("publish_page")
        response = self.client.post(
            reverse("wagtailapi_v3:pages_actions_publish", kwargs={"page_id": 999999})
        )
        self.assert_problem_response(response, status_code=404)


class TestV3PageUnpublish(TestV3PageActionsBase):
    # Unpublishing requires "publish" and nothing less.
    permission_matrix = [
        (None, 401),
        ([], 403),
        (["add_page"], 403),
        (["publish_page"], 200),
    ]

    def post(self, page):
        return self.client.post(
            reverse(
                "wagtailapi_v3:pages_actions_unpublish",
                kwargs={"page_id": page.pk},
            )
        )

    def test_permission_matrix(self):
        for i, (codenames, expected_status) in enumerate(self.permission_matrix):
            with self.subTest(codenames=codenames):
                page = self.add_simple_page(
                    self.home_page, title="Live", slug=f"live-{i}"
                )
                if codenames is None:
                    self.client.logout()
                else:
                    self.login_with_permissions(*codenames, index=i)

                since = timezone.now()
                response = self.post(page)

                self.assertEqual(response.status_code, expected_status)
                page.refresh_from_db()
                if expected_status == 200:
                    self.assertFalse(page.live)
                    self.assert_log_actions(page, ["wagtail.unpublish"], since=since)
                else:
                    self.assertTrue(page.live)

    def test_unknown_page_returns_404(self):
        self.login_with_permissions("publish_page")
        response = self.client.post(
            reverse("wagtailapi_v3:pages_actions_unpublish", kwargs={"page_id": 999999})
        )
        self.assert_problem_response(response, status_code=404)


class TestV3PageCopy(TestV3PageActionsBase):
    # Copying only requires "add" on the source/destination tree, provided
    # the copy is requested with keep_live=False. Keeping the copy live
    # additionally requires "publish" at the destination.
    permission_matrix = [
        (None, {}, 401),
        ([], {}, 403),
        (["add_page"], {}, 403),  # keep_live defaults True, needs "publish" too
        (["add_page"], {"keep_live": False}, 201),
        (["add_page", "publish_page"], {}, 201),
    ]

    def post(self, page, data):
        return self.client.post(
            reverse("wagtailapi_v3:pages_actions_copy", kwargs={"page_id": page.pk}),
            data=json.dumps(data),
            content_type="application/json",
        )

    def test_permission_matrix(self):
        for i, (codenames, extra_payload, expected_status) in enumerate(
            self.permission_matrix
        ):
            with self.subTest(codenames=codenames, extra_payload=extra_payload):
                if codenames is None:
                    self.client.logout()
                    owner = AnonymousUser()
                else:
                    owner = self.login_with_permissions(*codenames, index=i)

                destination = self.add_simple_page(
                    self.home_page,
                    title="Destination",
                    slug=f"destination-{i}",
                    owner=owner if codenames else None,
                )
                page = self.add_simple_page(
                    self.home_page,
                    title="Src",
                    slug=f"src-{i}",
                    owner=owner if codenames else None,
                )

                response = self.post(
                    page, {"destination": destination.pk, **extra_payload}
                )

                self.assertEqual(response.status_code, expected_status)
                if expected_status == 201:
                    content = response.json()
                    new_page = Page.objects.get(pk=content["id"])
                    self.assertEqual(new_page.get_parent().pk, destination.pk)
                    self.assertEqual(
                        new_page.live, extra_payload.get("keep_live", True)
                    )

    def test_superuser_copy_logs_actions(self):
        self.login()
        destination = self.add_simple_page(
            self.home_page, title="Destination", slug="destination"
        )
        page = self.add_simple_page(self.home_page, title="Src", slug="src")
        response = self.post(page, {"destination": destination.pk})
        self.assertEqual(response.status_code, 201)
        new_page = Page.objects.get(pk=response.json()["id"])
        self.assert_log_actions(
            new_page, ["wagtail.create", "wagtail.copy", "wagtail.publish"]
        )

    def test_copy_defaults_to_recursive_true(self):
        self.login()
        destination = self.add_simple_page(
            self.home_page, title="Destination", slug="destination"
        )
        page = self.add_simple_page(self.home_page, title="Src", slug="src")
        self.add_simple_page(page, title="Child", slug="child")
        response = self.post(page, {"destination": destination.pk})
        self.assertEqual(response.status_code, 201)
        new_page = Page.objects.get(pk=response.json()["id"])
        self.assertEqual(new_page.get_children().count(), 1)

    def test_copy_non_recursive_omits_descendants(self):
        self.login()
        destination = self.add_simple_page(
            self.home_page, title="Destination", slug="destination"
        )
        page = self.add_simple_page(self.home_page, title="Src", slug="src")
        self.add_simple_page(page, title="Child", slug="child")
        response = self.post(page, {"destination": destination.pk, "recursive": False})
        self.assertEqual(response.status_code, 201)
        new_page = Page.objects.get(pk=response.json()["id"])
        self.assertEqual(new_page.get_children().count(), 0)

    def test_duplicate_slug_returns_422(self):
        self.login()
        page = self.add_simple_page(self.home_page, title="Src", slug="src")
        response = self.post(page, {"destination": self.home_page.pk})
        self.assert_problem_response(response, status_code=422)

    def test_unknown_destination_returns_404(self):
        self.login()
        page = self.add_simple_page(self.home_page, title="Src", slug="src")
        response = self.post(page, {"destination": 999999})
        self.assert_problem_response(response, status_code=404)

    def test_unknown_page_returns_404(self):
        self.login()
        response = self.client.post(
            reverse("wagtailapi_v3:pages_actions_copy", kwargs={"page_id": 999999}),
            data=json.dumps({"destination": self.home_page.pk}),
            content_type="application/json",
        )
        self.assert_problem_response(response, status_code=404)


class TestV3PageMove(TestV3PageActionsBase):
    # Moving a leaf, non-live page owned by the user only requires "add"
    # (equivalent to deleting + re-adding a page you own).
    permission_matrix = [
        (None, 401),
        ([], 403),
        (["add_page"], 200),
    ]

    def post(self, page, data):
        return self.client.post(
            reverse("wagtailapi_v3:pages_actions_move", kwargs={"page_id": page.pk}),
            data=json.dumps(data),
            content_type="application/json",
        )

    def test_permission_matrix(self):
        for i, (codenames, expected_status) in enumerate(self.permission_matrix):
            with self.subTest(codenames=codenames):
                if codenames is None:
                    self.client.logout()
                    owner = None
                else:
                    owner = self.login_with_permissions(*codenames, index=i)

                section = self.add_simple_page(
                    self.home_page,
                    title="Section",
                    slug=f"section-{i}",
                    owner=owner,
                )
                page = self.add_simple_page(
                    self.home_page,
                    title="Movable",
                    slug=f"movable-{i}",
                    live=False,
                    owner=owner,
                )

                since = timezone.now()
                response = self.post(
                    page, {"destination": section.pk, "position": "last-child"}
                )

                self.assertEqual(response.status_code, expected_status)
                page.refresh_from_db()
                if expected_status == 200:
                    self.assertEqual(page.get_parent().pk, section.pk)
                    self.assert_log_actions(page, ["wagtail.move"], since=since)
                else:
                    self.assertEqual(page.get_parent().pk, self.home_page.pk)

    def test_move_first_child(self):
        self.login()
        section = self.add_simple_page(self.home_page, title="Section", slug="section")
        self.add_simple_page(section, title="Existing", slug="existing")
        page = self.add_simple_page(self.home_page, title="Movable", slug="movable")
        response = self.post(
            page, {"destination": section.pk, "position": "first-child"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            list(section.get_children().values_list("slug", flat=True))[0], "movable"
        )

    def test_move_left_right_reorders_siblings(self):
        self.login()
        first = self.add_simple_page(self.home_page, title="First", slug="first")
        second = self.add_simple_page(self.home_page, title="Second", slug="second")
        since = timezone.now()
        response = self.post(second, {"destination": first.pk, "position": "left"})
        self.assertEqual(response.status_code, 200)
        siblings = list(self.home_page.get_children().values_list("slug", flat=True))
        self.assertLess(siblings.index("second"), siblings.index("first"))
        second.refresh_from_db()
        self.assert_log_actions(second, ["wagtail.reorder"], since=since)

    def test_invalid_position_returns_422(self):
        self.login()
        section = self.add_simple_page(self.home_page, title="Section", slug="section")
        page = self.add_simple_page(self.home_page, title="Movable", slug="movable")
        response = self.post(
            page, {"destination": section.pk, "position": "not-a-position"}
        )
        self.assert_problem_response(response, status_code=422)

    def test_unknown_destination_returns_404(self):
        self.login()
        page = self.add_simple_page(self.home_page, title="Movable", slug="movable")
        response = self.post(page, {"destination": 999999, "position": "last-child"})
        self.assert_problem_response(response, status_code=404)

    def test_unknown_page_returns_404(self):
        self.login()
        section = self.add_simple_page(self.home_page, title="Section", slug="section")
        response = self.client.post(
            reverse("wagtailapi_v3:pages_actions_move", kwargs={"page_id": 999999}),
            data=json.dumps({"destination": section.pk, "position": "last-child"}),
            content_type="application/json",
        )
        self.assert_problem_response(response, status_code=404)

    def test_moving_into_own_descendant_returns_403(self):
        self.login()
        section = self.add_simple_page(self.home_page, title="Section", slug="section")
        child = self.add_simple_page(section, title="Child", slug="child")
        response = self.post(
            section, {"destination": child.pk, "position": "last-child"}
        )
        self.assert_problem_response(response, status_code=403)
