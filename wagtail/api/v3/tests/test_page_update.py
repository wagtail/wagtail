import json

from django.contrib.auth.models import Group, Permission
from django.test import TestCase
from django.urls import reverse

from wagtail.api.v3.tests.base import TestV3Base
from wagtail.models import GroupPagePermission, Page, PageLogEntry
from wagtail.test.demosite.models import BlogIndexPage, EventPage, HomePage
from wagtail.test.testapp.models import StreamPage
from wagtail.test.utils import WagtailTestUtils


class TestV3PageUpdate(TestV3Base, WagtailTestUtils, TestCase):
    def setUp(self):
        super().setUp()
        self.root_page = Page.objects.get(depth=1)
        self.user = self.login()

    def patch(self, page, data):
        return self.client.patch(
            reverse("wagtailapi_v3:update_page", kwargs={"page_id": page.pk}),
            data=json.dumps(data),
            content_type="application/json",
        )

    def test_anonymous_returns_401(self):
        page = self.root_page.add_child(
            instance=BlogIndexPage(title="Original", slug="original", live=False)
        )
        self.client.logout()
        response = self.patch(
            page,
            {
                "meta": {"type": "demosite.BlogIndexPage"},
                "title": "New title",
            },
        )
        self.assert_problem_response(response, status_code=401)

    def test_superuser_can_update_page(self):
        page = self.root_page.add_child(
            instance=BlogIndexPage(title="Original", slug="original", live=False)
        )
        response = self.patch(
            page,
            {
                "meta": {"type": "demosite.BlogIndexPage"},
                "title": "New title",
            },
        )
        self.assertEqual(response.status_code, 200)
        page.refresh_from_db()
        self.assertEqual(page.title, "New title")
        # slug wasn't sent, so it must be untouched.
        self.assertEqual(page.slug, "original")

        content = response.json()
        self.assertEqual(content["title"], "New title")
        self.assertEqual(content["meta"]["slug"], "original")

    def test_omitted_field_is_left_untouched(self):
        """
        This is a partial update: a writable field that isn't in the request
        body must keep its existing value, not get cleared to empty/False -
        which is what would happen if it were bound on the form unset.
        """
        page = self.root_page.add_child(
            instance=BlogIndexPage(
                title="Original", slug="original", show_in_menus=True, live=False
            )
        )
        response = self.patch(
            page,
            {
                "meta": {"type": "demosite.BlogIndexPage"},
                "title": "New title",
            },
        )
        self.assertEqual(response.status_code, 200)
        page.refresh_from_db()
        self.assertTrue(page.show_in_menus)

    def test_omitted_non_blank_extra_field_does_not_fail_validation(self):
        """
        EventPage.date_from is a plain, non-blank model field exposed as a
        writable APIField. It's required on create, but omitting it from a
        patch must not be rejected as missing - the patch schema forces
        every such field optional (see patch_generator's force_optional),
        independent of what the create schema requires for the same field.
        """
        page = self.root_page.add_child(
            instance=EventPage(
                title="Event",
                slug="event",
                date_from="2026-01-01",
                audience="public",
                location="Somewhere",
                cost="Free",
                live=False,
            )
        )
        response = self.patch(
            page,
            {
                "meta": {"type": "demosite.EventPage"},
                "title": "Event Renamed",
            },
        )
        self.assertEqual(response.status_code, 200)
        page.refresh_from_db()
        self.assertEqual(page.title, "Event Renamed")
        self.assertEqual(str(page.date_from), "2026-01-01")

    def test_update_page_with_publish_action_publishes_page(self):
        page = self.root_page.add_child(
            instance=BlogIndexPage(title="Original", slug="original", live=False)
        )
        self.assertFalse(page.live)
        response = self.patch(
            page,
            {
                "meta": {"type": "demosite.BlogIndexPage", "action": "publish"},
                "title": "New title",
            },
        )
        self.assertEqual(response.status_code, 200)
        page.refresh_from_db()
        self.assertTrue(page.live)
        self.assertEqual(page.title, "New title")
        self.assertIsNotNone(page.live_revision)
        self.assertEqual(page.live_revision, page.latest_revision)

    def test_update_page_with_invalid_action_returns_422(self):
        page = self.root_page.add_child(
            instance=BlogIndexPage(title="Original", slug="original", live=False)
        )
        response = self.patch(
            page,
            {
                "meta": {
                    "type": "demosite.BlogIndexPage",
                    "action": "not_a_real_action",
                },
                "title": "New title",
            },
        )
        self.assert_problem_response(response, status_code=422)

    def test_update_saves_one_revision_and_logs_edit(self):
        page = self.root_page.add_child(
            instance=BlogIndexPage(title="Original", slug="original", live=False)
        )
        entries_before = set(
            PageLogEntry.objects.filter(page=page).values_list("pk", flat=True)
        )
        response = self.patch(
            page,
            {
                "meta": {"type": "demosite.BlogIndexPage"},
                "title": "New title",
            },
        )
        self.assertEqual(response.status_code, 200)
        page.refresh_from_db()
        self.assertEqual(page.revisions.count(), 1)

        new_actions = list(
            PageLogEntry.objects.filter(page=page)
            .exclude(pk__in=entries_before)
            .order_by("timestamp")
            .values_list("action", flat=True)
        )
        self.assertEqual(new_actions, ["wagtail.edit"])

    def test_update_page_with_api_field(self):
        page = self.root_page.add_child(
            instance=StreamPage(
                title="Stream page",
                slug="stream-page",
                body=[{"type": "text", "value": "hello world"}],
                live=False,
            )
        )
        response = self.patch(
            page,
            {
                "meta": {"type": "tests.StreamPage"},
                "body": [{"type": "text", "value": "updated"}],
            },
        )
        self.assertEqual(response.status_code, 200)
        page.refresh_from_db()
        self.assertEqual(page.body[0].value, "updated")
        # title wasn't sent, so it must be untouched.
        self.assertEqual(page.title, "Stream page")

    def test_update_page_with_non_writable_api_field_ignores_it(self):
        page = self.root_page.add_child(
            instance=BlogIndexPage(
                title="Original",
                slug="original",
                intro="Original intro",
                live=False,
            )
        )
        response = self.patch(
            page,
            {
                "meta": {"type": "demosite.BlogIndexPage"},
                "intro": "should be ignored",
            },
        )
        self.assertEqual(response.status_code, 200)
        page.refresh_from_db()
        self.assertEqual(page.intro, "Original intro")

    def test_update_page_with_unknown_field_ignores_it(self):
        page = self.root_page.add_child(
            instance=BlogIndexPage(title="Original", slug="original", live=False)
        )
        response = self.patch(
            page,
            {
                "meta": {"type": "demosite.BlogIndexPage"},
                "not_a_real_field_at_all": "should be ignored",
            },
        )
        self.assertEqual(response.status_code, 200)

    def test_update_page_with_duplicate_slug_returns_422(self):
        self.root_page.add_child(
            instance=BlogIndexPage(title="Existing", slug="existing", live=False)
        )
        page = self.root_page.add_child(
            instance=BlogIndexPage(title="Original", slug="original", live=False)
        )
        response = self.patch(
            page,
            {
                "meta": {"type": "demosite.BlogIndexPage"},
                "slug": "existing",
            },
        )
        self.assert_problem_response(response, status_code=422)

    def test_update_page_with_child_relations_replaces_them(self):
        page = self.root_page.add_child(
            instance=HomePage(
                title="Home", slug="home-with-children", body="<p>hi</p>", live=False
            )
        )
        # DeferringRelatedManager.create() only stages the child in memory -
        # it isn't written to the database until the parent is saved.
        page.carousel_items.create(
            caption="Old", link_external="http://example.com/old", sort_order=0
        )
        page.save()
        response = self.patch(
            page,
            {
                "meta": {"type": "demosite.HomePage"},
                "carousel_items": [
                    {
                        "caption": "New",
                        "link_external": "http://example.com/new",
                    },
                ],
            },
        )
        self.assertEqual(response.status_code, 200)
        # refresh_from_db() doesn't clear modelcluster's own child-relation
        # cache, so re-fetch the page outright to see the real DB state.
        page = HomePage.objects.get(pk=page.pk)
        items = list(page.carousel_items.order_by("sort_order"))
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].caption, "New")

    def test_update_page_with_child_relation_id_edits_in_place(self):
        page = self.root_page.add_child(
            instance=HomePage(
                title="Home",
                slug="home-with-matched-child",
                body="<p>hi</p>",
                live=False,
            )
        )
        item = page.carousel_items.create(
            caption="Old", link_external="http://example.com/old", sort_order=0
        )
        page.save()
        response = self.patch(
            page,
            {
                "meta": {"type": "demosite.HomePage"},
                "carousel_items": [
                    {
                        "id": item.pk,
                        "caption": "Edited",
                        "link_external": "http://example.com/old",
                    },
                ],
            },
        )
        self.assertEqual(response.status_code, 200)
        page = HomePage.objects.get(pk=page.pk)
        items = list(page.carousel_items.order_by("sort_order"))
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].pk, item.pk)
        self.assertEqual(items[0].caption, "Edited")

    def test_update_of_live_page_does_not_touch_live_rows_until_published(self):
        """
        Updating a live page without publishing must save the changes as a
        new draft revision - matching the admin edit view - without
        touching the live DB rows for the page or its child relations.
        Publishing the resulting revision is what applies the change.
        """
        page = self.root_page.add_child(
            instance=HomePage(
                title="Home", slug="home-live-draft-edit", body="<p>hi</p>", live=True
            )
        )
        item = page.carousel_items.create(
            caption="Old", link_external="http://example.com/old", sort_order=0
        )
        page.save()
        page.save_revision().publish()

        response = self.patch(
            page,
            {
                "meta": {"type": "demosite.HomePage"},
                "title": "New Draft Title",
                "carousel_items": [
                    {
                        "caption": "New Draft Item",
                        "link_external": "http://example.com/new",
                    },
                ],
            },
        )
        self.assertEqual(response.status_code, 200)

        page = HomePage.objects.get(pk=page.pk)
        self.assertTrue(page.live)
        self.assertEqual(page.title, "Home")
        items = list(page.carousel_items.order_by("sort_order"))
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].pk, item.pk)
        self.assertEqual(items[0].caption, "Old")

        latest_revision = page.get_latest_revision()
        self.assertNotEqual(page.live_revision_id, latest_revision.pk)
        self.assertEqual(latest_revision.content["title"], "New Draft Title")
        self.assertEqual(
            latest_revision.content["carousel_items"][0]["caption"], "New Draft Item"
        )

        latest_revision.publish()
        page.refresh_from_db()
        self.assertEqual(page.title, "New Draft Title")
        items = list(page.carousel_items.order_by("sort_order"))
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].caption, "New Draft Item")

    def test_update_page_with_child_relation_unknown_id_is_treated_as_new(self):
        page = self.root_page.add_child(
            instance=HomePage(
                title="Home",
                slug="home-with-unknown-child-id",
                body="<p>hi</p>",
                live=False,
            )
        )
        item = page.carousel_items.create(
            caption="Old", link_external="http://example.com/old", sort_order=0
        )
        page.save()
        response = self.patch(
            page,
            {
                "meta": {"type": "demosite.HomePage"},
                "carousel_items": [
                    {
                        "id": item.pk + 999,
                        "caption": "New",
                        "link_external": "http://example.com/new",
                    },
                ],
            },
        )
        self.assertEqual(response.status_code, 200)
        page = HomePage.objects.get(pk=page.pk)
        items = list(page.carousel_items.order_by("sort_order"))
        self.assertEqual(len(items), 1)
        # The unmatched id is discarded entirely, not used as the new row's
        # pk - it's DB-autogenerated on insert, like any other new row.
        self.assertNotEqual(items[0].pk, item.pk)
        self.assertNotEqual(items[0].pk, item.pk + 999)
        self.assertEqual(items[0].caption, "New")

    def test_child_relations_untouched_when_omitted(self):
        page = self.root_page.add_child(
            instance=HomePage(
                title="Home", slug="home-untouched", body="<p>hi</p>", live=False
            )
        )
        # DeferringRelatedManager.create() only stages the child in memory -
        # it isn't written to the database until the parent is saved.
        page.carousel_items.create(
            caption="Kept", link_external="http://example.com/kept", sort_order=0
        )
        page.save()
        response = self.patch(
            page,
            {
                "meta": {"type": "demosite.HomePage"},
                "title": "Home renamed",
            },
        )
        self.assertEqual(response.status_code, 200)
        page = HomePage.objects.get(pk=page.pk)
        items = list(page.carousel_items.order_by("sort_order"))
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].caption, "Kept")

    def test_page_type_mismatch_returns_422(self):
        page = self.root_page.add_child(
            instance=BlogIndexPage(title="Original", slug="original", live=False)
        )
        response = self.patch(
            page,
            {
                "meta": {"type": "demosite.EventPage"},
                "title": "New title",
            },
        )
        self.assert_problem_response(response, status_code=422)

    def test_unknown_page_id_returns_404(self):
        response = self.client.patch(
            reverse("wagtailapi_v3:update_page", kwargs={"page_id": 999999}),
            data=json.dumps(
                {
                    "meta": {"type": "demosite.BlogIndexPage"},
                    "title": "New title",
                }
            ),
            content_type="application/json",
        )
        self.assert_problem_response(response, status_code=404)

    def test_user_without_change_permission_gets_403(self):
        page = self.root_page.add_child(
            instance=BlogIndexPage(title="Original", slug="original", live=False)
        )
        self.create_user(username="noperms", password="password")
        self.login(username="noperms", password="password")
        response = self.patch(
            page,
            {
                "meta": {"type": "demosite.BlogIndexPage"},
                "title": "New title",
            },
        )
        self.assert_problem_response(response, status_code=403)

    def test_user_with_change_permission_on_branch_can_update(self):
        page = self.root_page.add_child(
            instance=BlogIndexPage(title="Original", slug="original", live=False)
        )
        editor = self.create_user(username="editor", password="password")
        editor_group = Group.objects.create(name="Page branch editors")
        editor.groups.add(editor_group)
        GroupPagePermission.objects.create(
            group=editor_group,
            page=self.root_page,
            permission=Permission.objects.get(
                content_type__app_label="wagtailcore", codename="change_page"
            ),
        )
        self.login(username="editor", password="password")
        response = self.patch(
            page,
            {
                "meta": {"type": "demosite.BlogIndexPage"},
                "title": "New title",
            },
        )
        self.assertEqual(response.status_code, 200)
