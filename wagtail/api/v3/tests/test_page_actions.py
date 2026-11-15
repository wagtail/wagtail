import json

from django.contrib.auth.models import AnonymousUser, Group, Permission
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from wagtail.api.v3.tests.base import TestV3Base
from wagtail.models import GroupPagePermission, Locale
from wagtail.test.testapp.models import SimplePage
from wagtail.test.utils import Page, WagtailTestUtils


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
                        content_type__app_label=Page._meta.app_label, codename=codename
                    ),
                )
        self.login(username=getattr(user, user.USERNAME_FIELD), password="password")
        return user


class TestV3PagePublish(TestV3PageActionsBase):
    # Publishing requires "publish" and nothing less.
    permission_matrix = [
        (None, 401),
        ([], 403),
        ([Page.PERMISSION_CODENAMES.ADD], 403),
        ([Page.PERMISSION_CODENAMES.PUBLISH], 200),
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
                    self.unauthorize()
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
        self.login_with_permissions(Page.PERMISSION_CODENAMES.PUBLISH)
        self.assertIsNone(page.get_latest_revision())
        response = self.post(page)
        self.assertEqual(response.status_code, 200)
        page.refresh_from_db()
        self.assertTrue(page.live)
        self.assertIsNotNone(page.get_latest_revision())

    def test_unknown_page_returns_404(self):
        self.login_with_permissions(Page.PERMISSION_CODENAMES.PUBLISH)
        response = self.client.post(
            reverse("wagtailapi_v3:pages_actions_publish", kwargs={"page_id": 999999})
        )
        self.assert_problem_response(response, status_code=404)


class TestV3PageUnpublish(TestV3PageActionsBase):
    # Unpublishing requires "publish" and nothing less.
    permission_matrix = [
        (None, 401),
        ([], 403),
        ([Page.PERMISSION_CODENAMES.ADD], 403),
        ([Page.PERMISSION_CODENAMES.PUBLISH], 200),
    ]

    def post(self, page, data=None):
        return self.client.post(
            reverse(
                "wagtailapi_v3:pages_actions_unpublish",
                kwargs={"page_id": page.pk},
            ),
            data=json.dumps(data or {}),
            content_type="application/json",
        )

    def test_permission_matrix(self):
        for i, (codenames, expected_status) in enumerate(self.permission_matrix):
            with self.subTest(codenames=codenames):
                page = self.add_simple_page(
                    self.home_page, title="Live", slug=f"live-{i}"
                )
                if codenames is None:
                    self.unauthorize()
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

    def test_non_live_page_returns_403(self):
        # can_unpublish() rejects non-live pages outright
        self.login()
        page = self.add_simple_page(
            self.home_page, title="Draft", slug="draft", live=False
        )
        response = self.post(page)
        self.assert_problem_response(
            response,
            status_code=403,
            detail_contains="You do not have permission to unpublish this page.",
        )

    def test_unknown_page_returns_404(self):
        self.login_with_permissions(Page.PERMISSION_CODENAMES.PUBLISH)
        response = self.post_unknown_page()
        self.assert_problem_response(response, status_code=404)

    def post_unknown_page(self):
        return self.client.post(
            reverse(
                "wagtailapi_v3:pages_actions_unpublish", kwargs={"page_id": 999999}
            ),
            data=json.dumps({}),
            content_type="application/json",
        )

    def test_recursive_unpublishes_descendants(self):
        self.login()
        section = self.add_simple_page(self.home_page, title="Section", slug="section")
        child = self.add_simple_page(section, title="Child", slug="child")
        response = self.post(section, {"recursive": True})
        self.assertEqual(response.status_code, 200)
        section.refresh_from_db()
        child.refresh_from_db()
        self.assertFalse(section.live)
        self.assertFalse(child.live)

    def test_non_recursive_keeps_descendants_live(self):
        self.login()
        section = self.add_simple_page(self.home_page, title="Section", slug="section")
        child = self.add_simple_page(section, title="Child", slug="child")
        response = self.post(section)
        self.assertEqual(response.status_code, 200)
        section.refresh_from_db()
        child.refresh_from_db()
        self.assertFalse(section.live)
        self.assertTrue(child.live)


class TestV3PageCopy(TestV3PageActionsBase):
    # Copying only requires "add" on the source/destination tree, provided
    # the copy is requested with keep_live=False. Keeping the copy live
    # additionally requires "publish" at the destination.
    permission_matrix = [
        (None, {}, 401),
        ([], {}, 403),
        ([Page.PERMISSION_CODENAMES.ADD], {}, 403),
        # keep_live defaults True, needs "publish" too
        ([Page.PERMISSION_CODENAMES.ADD], {"keep_live": False}, 201),
        ([Page.PERMISSION_CODENAMES.ADD, Page.PERMISSION_CODENAMES.PUBLISH], {}, 201),
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
                    self.unauthorize()
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
                    page, {"destination_id": destination.pk, **extra_payload}
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
        response = self.post(page, {"destination_id": destination.pk})
        self.assertEqual(response.status_code, 201)
        new_page = Page.objects.get(pk=response.json()["id"])
        self.assert_log_actions(
            new_page, ["wagtail.create", "wagtail.copy", "wagtail.publish"]
        )

    def test_copy_defaults_to_recursive_false(self):
        self.login()
        destination = self.add_simple_page(
            self.home_page, title="Destination", slug="destination"
        )
        page = self.add_simple_page(self.home_page, title="Src", slug="src")
        self.add_simple_page(page, title="Child", slug="child")
        response = self.post(page, {"destination_id": destination.pk})
        self.assertEqual(response.status_code, 201)
        new_page = Page.objects.get(pk=response.json()["id"])
        self.assertEqual(new_page.get_children().count(), 0)

    def test_copy_recursive_includes_descendants(self):
        self.login()
        destination = self.add_simple_page(
            self.home_page, title="Destination", slug="destination"
        )
        page = self.add_simple_page(self.home_page, title="Src", slug="src")
        self.add_simple_page(page, title="Child", slug="child")
        response = self.post(
            page, {"destination_id": destination.pk, "recursive": True}
        )
        self.assertEqual(response.status_code, 201)
        new_page = Page.objects.get(pk=response.json()["id"])
        self.assertEqual(new_page.get_children().count(), 1)

    def test_duplicate_slug_finds_available_slug(self):
        self.login()
        page = self.add_simple_page(self.home_page, title="Src", slug="src")
        response = self.post(page, {"destination_id": self.home_page.pk})
        self.assertEqual(response.status_code, 201)
        new_page = Page.objects.get(pk=response.json()["id"])
        self.assertNotEqual(new_page.slug, "src")

    def test_defaults_destination_to_parent(self):
        self.login()
        page = self.add_simple_page(self.home_page, title="Src", slug="src")
        response = self.post(page, {})
        self.assertEqual(response.status_code, 201)
        new_page = Page.objects.get(pk=response.json()["id"])
        self.assertEqual(new_page.get_parent().pk, self.home_page.pk)

    def test_slug_override(self):
        self.login()
        destination = self.add_simple_page(
            self.home_page, title="Destination", slug="destination"
        )
        page = self.add_simple_page(self.home_page, title="Src", slug="src")
        response = self.post(
            page, {"destination_id": destination.pk, "slug": "custom-slug"}
        )
        self.assertEqual(response.status_code, 201)
        new_page = Page.objects.get(pk=response.json()["id"])
        self.assertEqual(new_page.slug, "custom-slug")

    def test_title_override(self):
        self.login()
        destination = self.add_simple_page(
            self.home_page, title="Destination", slug="destination"
        )
        page = self.add_simple_page(self.home_page, title="Src", slug="src")
        response = self.post(
            page, {"destination_id": destination.pk, "title": "Custom Title"}
        )
        self.assertEqual(response.status_code, 201)
        new_page = Page.objects.get(pk=response.json()["id"])
        self.assertEqual(new_page.title, "Custom Title")

    def test_invalid_slug_returns_422(self):
        self.login()
        page = self.add_simple_page(self.home_page, title="Src", slug="src")
        # keep_live=False exercises minimal_clean(), which previously skipped
        # slug format validation and allowed a malformed slug to be saved.
        response = self.post(page, {"keep_live": False, "slug": "bad slug"})
        self.assert_problem_response(
            response,
            status_code=422,
            detail_contains="Validation failed",
            errors=[{"type": "value_error", "loc": ["body", "data", "slug"]}],
        )

    def test_non_ascii_slug_rejected_when_unicode_disabled(self):
        self.login()
        page = self.add_simple_page(self.home_page, title="Src", slug="src")
        with self.settings(WAGTAIL_ALLOW_UNICODE_SLUGS=False):
            response = self.post(page, {"keep_live": False, "slug": "pàgé"})
        self.assert_problem_response(
            response,
            status_code=422,
            detail_contains="Validation failed",
            errors=[{"type": "value_error", "loc": ["body", "data", "slug"]}],
        )

    def test_unknown_destination_returns_404(self):
        self.login()
        page = self.add_simple_page(self.home_page, title="Src", slug="src")
        response = self.post(page, {"destination_id": 999999})
        self.assert_problem_response(response, status_code=404)

    def test_unknown_page_returns_404(self):
        self.login()
        response = self.client.post(
            reverse("wagtailapi_v3:pages_actions_copy", kwargs={"page_id": 999999}),
            data=json.dumps({"destination_id": self.home_page.pk}),
            content_type="application/json",
        )
        self.assert_problem_response(response, status_code=404)

    def test_recursive_copy_into_own_descendant_returns_422(self):
        self.login()
        section = self.add_simple_page(self.home_page, title="Section", slug="section")
        child = self.add_simple_page(section, title="Child", slug="child")
        response = self.post(section, {"destination_id": child.pk, "recursive": True})
        self.assert_problem_response(
            response,
            status_code=422,
            detail_contains="Validation failed",
            errors=[
                {
                    "type": "copy_page_integrity_error",
                    "msg": "You cannot copy a tree branch recursively into itself",
                }
            ],
        )


class TestV3PageMove(TestV3PageActionsBase):
    # Moving a leaf, non-live page owned by the user only requires "add"
    # (equivalent to deleting + re-adding a page you own).
    permission_matrix = [
        (None, 401),
        ([], 403),
        ([Page.PERMISSION_CODENAMES.ADD], 200),
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
                    self.unauthorize()
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
                    page, {"destination_id": section.pk, "position": "last-child"}
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
            page, {"destination_id": section.pk, "position": "first-child"}
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
        response = self.post(second, {"destination_id": first.pk, "position": "left"})
        self.assertEqual(response.status_code, 200)
        siblings = list(self.home_page.get_children().values_list("slug", flat=True))
        self.assertLess(siblings.index("second"), siblings.index("first"))
        second.refresh_from_db()
        self.assert_log_actions(second, ["wagtail.reorder"], since=since)

    def test_move_first_sibling(self):
        self.login()
        first = self.add_simple_page(self.home_page, title="First", slug="first")
        second = self.add_simple_page(self.home_page, title="Second", slug="second")
        response = self.post(
            second, {"destination_id": first.pk, "position": "first-sibling"}
        )
        self.assertEqual(response.status_code, 200)
        siblings = list(self.home_page.get_children().values_list("slug", flat=True))
        self.assertEqual(siblings[0], "second")

    def test_move_last_sibling(self):
        self.login()
        first = self.add_simple_page(self.home_page, title="First", slug="first")
        second = self.add_simple_page(self.home_page, title="Second", slug="second")
        response = self.post(
            first, {"destination_id": second.pk, "position": "last-sibling"}
        )
        self.assertEqual(response.status_code, 200)
        siblings = list(self.home_page.get_children().values_list("slug", flat=True))
        self.assertEqual(siblings[-1], "first")

    def test_move_omitted_position_defaults_to_last_sibling(self):
        self.login()
        section = self.add_simple_page(self.home_page, title="Section", slug="section")
        page = self.add_simple_page(self.home_page, title="Movable", slug="movable")
        response = self.post(page, {"destination_id": section.pk})
        self.assertEqual(response.status_code, 200)
        siblings = list(self.home_page.get_children().values_list("slug", flat=True))
        self.assertEqual(siblings[-1], "movable")

    def test_invalid_position_returns_422(self):
        self.login()
        section = self.add_simple_page(self.home_page, title="Section", slug="section")
        page = self.add_simple_page(self.home_page, title="Movable", slug="movable")
        response = self.post(
            page, {"destination_id": section.pk, "position": "not-a-position"}
        )
        self.assert_problem_response(
            response,
            status_code=422,
            detail_contains="Validation failed",
            errors=[{"type": "literal_error", "loc": ["body", "data", "position"]}],
        )

    def test_unknown_destination_returns_404(self):
        self.login()
        page = self.add_simple_page(self.home_page, title="Movable", slug="movable")
        response = self.post(page, {"destination_id": 999999, "position": "last-child"})
        self.assert_problem_response(response, status_code=404)

    def test_unknown_page_returns_404(self):
        self.login()
        section = self.add_simple_page(self.home_page, title="Section", slug="section")
        response = self.client.post(
            reverse("wagtailapi_v3:pages_actions_move", kwargs={"page_id": 999999}),
            data=json.dumps({"destination_id": section.pk, "position": "last-child"}),
            content_type="application/json",
        )
        self.assert_problem_response(response, status_code=404)

    def test_moving_into_own_descendant_returns_403(self):
        self.login()
        section = self.add_simple_page(self.home_page, title="Section", slug="section")
        child = self.add_simple_page(section, title="Child", slug="child")
        response = self.post(
            section, {"destination_id": child.pk, "position": "last-child"}
        )
        self.assert_problem_response(response, status_code=403)


class TestV3PageDelete(TestV3PageActionsBase):
    # Deleting a leaf, non-live page owned by the user only requires "add"
    # (mirrors can_delete()'s "add"-only branch for non-bulk deletes).
    permission_matrix = [
        (None, 401),
        ([], 403),
        ([Page.PERMISSION_CODENAMES.ADD], 204),
    ]
    url_name = "wagtailapi_v3:delete_page"

    def delete(self, page):
        return self.client.delete(reverse(self.url_name, kwargs={"page_id": page.pk}))

    def test_permission_matrix(self):
        for i, (codenames, expected_status) in enumerate(self.permission_matrix):
            with self.subTest(codenames=codenames):
                if codenames is None:
                    self.unauthorize()
                    owner = None
                else:
                    owner = self.login_with_permissions(*codenames, index=i)

                page = self.add_simple_page(
                    self.home_page,
                    title="Deletable",
                    slug=f"deletable-{i}",
                    live=False,
                    owner=owner,
                )

                response = self.delete(page)

                self.assertEqual(response.status_code, expected_status)
                self.assertEqual(
                    Page.objects.filter(pk=page.pk).exists(), expected_status != 204
                )

    def test_superuser_can_delete_page(self):
        self.login()
        page = self.add_simple_page(self.home_page, title="Live", slug="live")
        response = self.delete(page)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Page.objects.filter(pk=page.pk).exists())

    def test_delete_logs_action(self):
        self.login()
        page = self.add_simple_page(self.home_page, title="Live", slug="live")
        response = self.delete(page)
        self.assertEqual(response.status_code, 204)
        self.assert_log_actions(page, ["wagtail.create", "wagtail.delete"])

    def test_delete_removes_descendants(self):
        self.login()
        section = self.add_simple_page(self.home_page, title="Section", slug="section")
        child = self.add_simple_page(section, title="Child", slug="child")
        response = self.delete(section)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Page.objects.filter(pk=section.pk).exists())
        self.assertFalse(Page.objects.filter(pk=child.pk).exists())

    def test_unknown_page_returns_404(self):
        self.login()
        response = self.client.delete(
            reverse(self.url_name, kwargs={"page_id": 999999})
        )
        self.assert_problem_response(response, status_code=404)

    def test_cannot_delete_root_page(self):
        self.login()
        response = self.client.delete(
            reverse(self.url_name, kwargs={"page_id": self.root_page.pk})
        )
        self.assert_problem_response(response, status_code=403)

    def test_non_leaf_page_requires_bulk_delete_permission(self):
        owner = self.login_with_permissions(Page.PERMISSION_CODENAMES.ADD)
        section = self.add_simple_page(
            self.home_page, title="Section", slug="section", live=False, owner=owner
        )
        self.add_simple_page(
            section, title="Child", slug="child", live=False, owner=owner
        )
        response = self.delete(section)
        self.assert_problem_response(response, status_code=403)


class TestV3PageDeleteAction(TestV3PageDelete):
    # The delete action is exposed both on the /{page_id}/ endpoint and the
    # discrete /{page_id}/actions/delete/ endpoint.
    url_name = "wagtailapi_v3:pages_actions_delete"


class TestV3PageRevert(TestV3PageActionsBase):
    # Reverting only requires "change" (or "add" on a page you own).
    permission_matrix = [
        (None, 401),
        ([], 403),
        ([Page.PERMISSION_CODENAMES.ADD], 200),
        ([Page.PERMISSION_CODENAMES.CHANGE], 200),
    ]

    def post(self, page, revision_id):
        return self.client.post(
            reverse("wagtailapi_v3:pages_actions_revert", kwargs={"page_id": page.pk}),
            data=json.dumps({"revision_id": revision_id}),
            content_type="application/json",
        )

    def test_permission_matrix(self):
        for i, (codenames, expected_status) in enumerate(self.permission_matrix):
            with self.subTest(codenames=codenames):
                if codenames is None:
                    self.unauthorize()
                    owner = None
                else:
                    owner = self.login_with_permissions(*codenames, index=i)

                page = self.add_simple_page(
                    self.home_page,
                    title="Original",
                    slug=f"revert-{i}",
                    owner=owner,
                )
                original_revision = page.save_revision(user=owner)
                page.title = "Changed"
                page.save_revision(user=owner)
                page.save()

                response = self.post(page, original_revision.pk)

                self.assertEqual(response.status_code, expected_status)
                if expected_status == 200:
                    content = response.json()
                    self.assertEqual(content["title"], "Original")

    def test_revert_creates_new_revision_without_publishing(self):
        self.login()
        page = self.add_simple_page(
            self.home_page, title="Original", slug="revert", live=False
        )
        original_revision = page.save_revision()
        page.title = "Changed"
        page.save_revision()
        page.save()

        response = self.post(page, original_revision.pk)

        self.assertEqual(response.status_code, 200)
        page.refresh_from_db()
        self.assertEqual(page.title, "Changed")
        self.assertEqual(page.get_latest_revision().as_object().title, "Original")
        self.assert_log_actions(page, ["wagtail.create", "wagtail.revert"])

    def test_unknown_page_returns_404(self):
        self.login()
        response = self.client.post(
            reverse("wagtailapi_v3:pages_actions_revert", kwargs={"page_id": 999999}),
            data=json.dumps({"revision_id": 1}),
            content_type="application/json",
        )
        self.assert_problem_response(response, status_code=404)

    def test_unknown_revision_returns_404(self):
        self.login()
        page = self.add_simple_page(self.home_page, title="Original", slug="revert")
        response = self.post(page, 999999)
        self.assert_problem_response(response, status_code=404)

    def test_revision_belonging_to_another_page_returns_404(self):
        self.login()
        page = self.add_simple_page(self.home_page, title="Page", slug="page")
        other_page = self.add_simple_page(self.home_page, title="Other", slug="other")
        other_revision = other_page.save_revision()
        response = self.post(page, other_revision.pk)
        self.assert_problem_response(response, status_code=404)


class TestV3PageConvertAlias(TestV3PageActionsBase):
    permission_matrix = [
        (None, 401),
        ([], 403),
        ([Page.PERMISSION_CODENAMES.CHANGE], 200),
    ]

    def post(self, page):
        return self.client.post(
            reverse(
                "wagtailapi_v3:pages_actions_convert_alias",
                kwargs={"page_id": page.pk},
            )
        )

    def make_alias(self, index=0):
        source = self.add_simple_page(
            self.home_page, title="Source", slug=f"source-{index}"
        )
        return source.create_alias(parent=self.home_page, update_slug=f"alias-{index}")

    def test_permission_matrix(self):
        for i, (codenames, expected_status) in enumerate(self.permission_matrix):
            with self.subTest(codenames=codenames):
                alias = self.make_alias(index=i)
                if codenames is None:
                    self.unauthorize()
                else:
                    self.login_with_permissions(*codenames, index=i)

                response = self.post(alias)

                self.assertEqual(response.status_code, expected_status)
                alias.refresh_from_db()
                if expected_status == 200:
                    self.assertIsNone(alias.alias_of_id)
                else:
                    self.assertIsNotNone(alias.alias_of_id)

    def test_convert_alias_logs_action(self):
        self.login()
        alias = self.make_alias()
        since = timezone.now()
        response = self.post(alias)
        self.assertEqual(response.status_code, 200)
        alias.refresh_from_db()
        self.assertIsNone(alias.alias_of_id)
        self.assert_log_actions(alias, ["wagtail.convert_alias"], since=since)

    def test_non_alias_page_returns_422(self):
        self.login()
        page = self.add_simple_page(self.home_page, title="Regular", slug="regular")
        response = self.post(page)
        self.assert_problem_response(
            response,
            status_code=422,
            detail_contains="Validation failed",
            errors=[
                {
                    "type": "convert_alias_page_error",
                    "msg": "Page must be an alias to be converted.",
                }
            ],
        )

    def test_unknown_page_returns_404(self):
        self.login()
        response = self.client.post(
            reverse(
                "wagtailapi_v3:pages_actions_convert_alias", kwargs={"page_id": 999999}
            )
        )
        self.assert_problem_response(response, status_code=404)


class TestV3PageCreateAlias(TestV3PageActionsBase):
    # Aliases mirror the source page's live state, so creating one requires
    # "publish" at the destination in addition to "add".
    permission_matrix = [
        (None, {}, 401),
        ([], {}, 403),
        ([Page.PERMISSION_CODENAMES.ADD], {}, 403),
        (
            [Page.PERMISSION_CODENAMES.ADD, Page.PERMISSION_CODENAMES.PUBLISH],
            {},
            201,
        ),
    ]

    def post(self, page, data=None):
        return self.client.post(
            reverse(
                "wagtailapi_v3:pages_actions_create_alias",
                kwargs={"page_id": page.pk},
            ),
            data=json.dumps(data or {}),
            content_type="application/json",
        )

    def test_permission_matrix(self):
        for i, (codenames, extra_payload, expected_status) in enumerate(
            self.permission_matrix
        ):
            with self.subTest(codenames=codenames):
                if codenames is None:
                    self.unauthorize()
                    owner = None
                else:
                    owner = self.login_with_permissions(*codenames, index=i)

                page = self.add_simple_page(
                    self.home_page, title="Src", slug=f"src-{i}", owner=owner
                )

                response = self.post(page, extra_payload)

                self.assertEqual(response.status_code, expected_status)
                if expected_status == 201:
                    content = response.json()
                    new_page = Page.objects.get(pk=content["id"])
                    self.assertEqual(new_page.alias_of_id, page.pk)

    def test_create_alias_defaults_to_sibling_of_source(self):
        self.login()
        page = self.add_simple_page(self.home_page, title="Src", slug="src")
        response = self.post(page)
        self.assertEqual(response.status_code, 201)
        new_page = Page.objects.get(pk=response.json()["id"])
        self.assertEqual(new_page.get_parent().pk, self.home_page.pk)

    def test_create_alias_finds_available_slug(self):
        self.login()
        page = self.add_simple_page(self.home_page, title="Src", slug="src")
        response = self.post(page)
        self.assertEqual(response.status_code, 201)
        new_page = Page.objects.get(pk=response.json()["id"])
        self.assertNotEqual(new_page.slug, "src")

    def test_create_alias_under_destination(self):
        self.login()
        destination = self.add_simple_page(
            self.home_page, title="Destination", slug="destination"
        )
        page = self.add_simple_page(self.home_page, title="Src", slug="src")
        response = self.post(page, {"destination_id": destination.pk})
        self.assertEqual(response.status_code, 201)
        new_page = Page.objects.get(pk=response.json()["id"])
        self.assertEqual(new_page.get_parent().pk, destination.pk)
        self.assertEqual(new_page.slug, "src")

    def test_create_alias_recursive_includes_descendants(self):
        self.login()
        page = self.add_simple_page(self.home_page, title="Src", slug="src")
        self.add_simple_page(page, title="Child", slug="child")
        response = self.post(page, {"recursive": True})
        self.assertEqual(response.status_code, 201)
        new_page = Page.objects.get(pk=response.json()["id"])
        self.assertEqual(new_page.get_children().count(), 1)

    def test_create_alias_slug_override(self):
        self.login()
        page = self.add_simple_page(self.home_page, title="Src", slug="src")
        response = self.post(page, {"slug": "custom-alias-slug"})
        self.assertEqual(response.status_code, 201)
        new_page = Page.objects.get(pk=response.json()["id"])
        self.assertEqual(new_page.slug, "custom-alias-slug")

    def test_invalid_slug_returns_422(self):
        self.login()
        page = self.add_simple_page(self.home_page, title="Src", slug="src")
        response = self.post(page, {"slug": "bad slug"})
        self.assert_problem_response(
            response,
            status_code=422,
            detail_contains="Validation failed",
            errors=[{"type": "value_error", "loc": ["body", "data", "slug"]}],
        )

    def test_unknown_destination_returns_404(self):
        self.login()
        page = self.add_simple_page(self.home_page, title="Src", slug="src")
        response = self.post(page, {"destination_id": 999999})
        self.assert_problem_response(response, status_code=404)

    def test_unknown_page_returns_404(self):
        self.login()
        response = self.client.post(
            reverse(
                "wagtailapi_v3:pages_actions_create_alias", kwargs={"page_id": 999999}
            ),
            data=json.dumps({}),
            content_type="application/json",
        )
        self.assert_problem_response(response, status_code=404)

    def test_recursive_alias_into_own_descendant_returns_422(self):
        self.login()
        section = self.add_simple_page(self.home_page, title="Section", slug="section")
        child = self.add_simple_page(section, title="Child", slug="child")
        response = self.post(section, {"destination_id": child.pk, "recursive": True})
        self.assert_problem_response(
            response,
            status_code=422,
            detail_contains="Validation failed",
            errors=[
                {
                    "type": "create_page_alias_integrity_error",
                    "msg": "You cannot copy a tree branch recursively into itself",
                }
            ],
        )


@override_settings(WAGTAIL_I18N_ENABLED=True)
class TestV3PageCopyForTranslation(TestV3PageActionsBase):
    def setUp(self):
        super().setUp()
        self.french = Locale.objects.create(language_code="fr")

    def grant_submit_translation(self, user):
        user.user_permissions.add(Permission.objects.get(codename="submit_translation"))

    def post(self, page, data):
        return self.client.post(
            reverse(
                "wagtailapi_v3:pages_actions_copy_for_translation",
                kwargs={"page_id": page.pk},
            ),
            data=json.dumps(data),
            content_type="application/json",
        )

    def test_requires_submit_translation_permission(self):
        self.login_with_permissions(
            Page.PERMISSION_CODENAMES.ADD, Page.PERMISSION_CODENAMES.CHANGE
        )
        page = self.add_simple_page(self.home_page, title="Src", slug="src")
        response = self.post(page, {"locale": "fr"})
        self.assert_problem_response(response, status_code=403)

    def test_copy_for_translation(self):
        user = self.login_with_permissions(
            Page.PERMISSION_CODENAMES.ADD, Page.PERMISSION_CODENAMES.CHANGE
        )
        self.grant_submit_translation(user)
        self.home_page.copy_for_translation(self.french)
        page = self.add_simple_page(self.home_page, title="Src", slug="src")

        response = self.post(page, {"locale": "fr"})

        self.assertEqual(response.status_code, 201)
        new_page = Page.objects.get(pk=response.json()["id"])
        self.assertEqual(new_page.locale, self.french)
        self.assertFalse(new_page.live)

    def test_alias_copy_for_translation(self):
        user = self.login_with_permissions(
            Page.PERMISSION_CODENAMES.ADD, Page.PERMISSION_CODENAMES.CHANGE
        )
        self.grant_submit_translation(user)
        self.home_page.copy_for_translation(self.french)
        page = self.add_simple_page(self.home_page, title="Src", slug="src")

        response = self.post(page, {"locale": "fr", "alias": True})

        self.assertEqual(response.status_code, 201)
        new_page = Page.objects.get(pk=response.json()["id"])
        self.assertEqual(new_page.alias_of_id, page.pk)

    def test_missing_translated_parent_returns_422(self):
        user = self.login_with_permissions(
            Page.PERMISSION_CODENAMES.ADD, Page.PERMISSION_CODENAMES.CHANGE
        )
        self.grant_submit_translation(user)
        page = self.add_simple_page(self.home_page, title="Src", slug="src")

        response = self.post(page, {"locale": "fr"})

        self.assert_problem_response(
            response,
            status_code=422,
            detail_contains="Validation failed",
            errors=[
                {
                    "type": "parent_not_translated_error",
                    "msg": "Parent page 'Welcome to your new Wagtail site!' "
                    "is not translated.",
                }
            ],
        )

    def test_copy_parents_creates_missing_translated_parents(self):
        user = self.login_with_permissions(
            Page.PERMISSION_CODENAMES.ADD, Page.PERMISSION_CODENAMES.CHANGE
        )
        self.grant_submit_translation(user)
        page = self.add_simple_page(self.home_page, title="Src", slug="src")

        response = self.post(page, {"locale": "fr", "copy_parents": True})

        self.assertEqual(response.status_code, 201)
        new_page = Page.objects.get(pk=response.json()["id"])
        self.assertEqual(new_page.locale, self.french)

    def test_unknown_locale_returns_404(self):
        user = self.login_with_permissions(
            Page.PERMISSION_CODENAMES.ADD, Page.PERMISSION_CODENAMES.CHANGE
        )
        self.grant_submit_translation(user)
        page = self.add_simple_page(self.home_page, title="Src", slug="src")
        response = self.post(page, {"locale": "de"})
        self.assert_problem_response(response, status_code=404)

    def test_unknown_page_returns_404(self):
        self.login_with_permissions(
            Page.PERMISSION_CODENAMES.ADD, Page.PERMISSION_CODENAMES.CHANGE
        )
        response = self.client.post(
            reverse(
                "wagtailapi_v3:pages_actions_copy_for_translation",
                kwargs={"page_id": 999999},
            ),
            data=json.dumps({"locale": "fr"}),
            content_type="application/json",
        )
        self.assert_problem_response(response, status_code=404)

    @override_settings(WAGTAIL_I18N_ENABLED=False)
    def test_disabled_when_i18n_disabled(self):
        self.login()
        page = self.add_simple_page(self.home_page, title="Src", slug="src")
        response = self.post(page, {"locale": "fr"})
        self.assert_problem_response(
            response,
            status_code=404,
            detail_contains="Internationalization is not enabled.",
        )
