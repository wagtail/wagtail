import json

from django.contrib.auth.models import Group, Permission
from django.test import TestCase
from django.urls import reverse

from wagtail.api.v3.tests.base import TestV3Base
from wagtail.models import GroupPagePermission, Page, PageLogEntry, PageSubscription
from wagtail.test.demosite.models import HomePage
from wagtail.test.testapp.models import MultiPreviewModesPage, StreamPage
from wagtail.test.utils import WagtailTestUtils


class TestV3PageCreate(TestV3Base, WagtailTestUtils, TestCase):
    def setUp(self):
        super().setUp()
        self.root_page = Page.objects.get(depth=1)

    def post(self, data):
        return self.client.post(
            reverse("wagtailapi_v3:create_page"),
            data=json.dumps(data),
            content_type="application/json",
        )

    def test_anonymous_returns_401(self):
        response = self.post(
            {
                "meta": {
                    "parent_id": self.root_page.pk,
                    "type": "tests.MultiPreviewModesPage",
                },
                "title": "New page",
                "slug": "new-page",
            }
        )
        self.assert_problem_response(response, status_code=401)

    def test_superuser_can_create_page(self):
        self.login()
        response = self.post(
            {
                "meta": {
                    "parent_id": self.root_page.pk,
                    "type": "tests.MultiPreviewModesPage",
                },
                "title": "New page",
                "slug": "new-page",
            }
        )
        self.assertEqual(response.status_code, 201)
        page = MultiPreviewModesPage.objects.get(slug="new-page")
        self.assertEqual(page.title, "New page")
        self.assertEqual(page.get_parent().pk, self.root_page.pk)
        self.assertFalse(page.live)
        self.assertIsNotNone(page.owner_id)

        content = response.json()
        self.assertEqual(content["title"], "New page")
        self.assertEqual(content["meta"]["type"], "tests.MultiPreviewModesPage")
        self.assertEqual(content["meta"]["slug"], "new-page")

    def test_create_page_subscribes_creator_to_comment_notifications(self):
        """
        Matches the admin create view, which subscribes the creating user to
        comment notifications on the new page by default.
        """
        user = self.login()
        response = self.post(
            {
                "meta": {
                    "parent_id": self.root_page.pk,
                    "type": "tests.MultiPreviewModesPage",
                },
                "title": "New page",
                "slug": "new-page",
            }
        )
        self.assertEqual(response.status_code, 201)
        page = MultiPreviewModesPage.objects.get(slug="new-page")
        subscription = PageSubscription.objects.get(page=page, user=user)
        self.assertTrue(subscription.comment_notifications)

    def test_create_saves_one_revision_and_matches_admin_log_entries(self):
        """
        add_child() saves the page directly, which already logs its own
        "wagtail.create" entry via Page.save() - so the router must not also
        use CreateAction (which would log a second, redundant "wagtail.create").
        The real admin create view logs "wagtail.create" (from add_child's
        save) plus "wagtail.edit" (from save_revision(log_action=True)) for
        every new page; this asserts the API produces that same pair, not a
        duplicate "wagtail.create".
        """
        self.login()
        response = self.post(
            {
                "meta": {
                    "parent_id": self.root_page.pk,
                    "type": "tests.MultiPreviewModesPage",
                },
                "title": "Logged page",
                "slug": "logged-page",
            }
        )
        self.assertEqual(response.status_code, 201)
        page = MultiPreviewModesPage.objects.get(slug="logged-page")

        self.assertEqual(page.revisions.count(), 1)
        self.assertIsNotNone(page.latest_revision)

        actions = list(
            PageLogEntry.objects.filter(page=page)
            .order_by("timestamp")
            .values_list("action", flat=True)
        )
        self.assertEqual(actions, ["wagtail.create", "wagtail.edit"])

    def test_superuser_can_create_page_with_api_field(self):
        """
        Only fields listed in a page model's api_fields (plus the base
        title/slug/seo_title/search_description/show_in_menus) are writable.
        A model with required panel fields outside api_fields (e.g.
        SimplePage.content) can't be created via this endpoint: the real
        admin form used for validation will reject the create for missing
        that field, since it isn't exposed in the input schema. StreamPage's
        body is in api_fields, so it's fully creatable.
        """
        self.login()
        response = self.post(
            {
                "meta": {"parent_id": self.root_page.pk, "type": "tests.StreamPage"},
                "title": "Stream page",
                "slug": "api-field-page",
                "body": [{"type": "text", "value": "hello world"}],
            }
        )
        self.assertEqual(response.status_code, 201)
        page = StreamPage.objects.get(slug="api-field-page")
        self.assertEqual(page.body[0].value, "hello world")

    def test_slug_is_auto_generated_from_title_when_omitted(self):
        self.login()
        response = self.post(
            {
                "meta": {
                    "parent_id": self.root_page.pk,
                    "type": "tests.MultiPreviewModesPage",
                },
                "title": "Auto Slug Page",
            }
        )
        self.assertEqual(response.status_code, 201)
        page = MultiPreviewModesPage.objects.get(title="Auto Slug Page")
        self.assertEqual(page.slug, "auto-slug-page")

    def test_duplicate_slug_returns_422(self):
        self.login()
        self.root_page.add_child(
            instance=MultiPreviewModesPage(title="Existing", slug="existing")
        )
        response = self.post(
            {
                "meta": {
                    "parent_id": self.root_page.pk,
                    "type": "tests.MultiPreviewModesPage",
                },
                "title": "Another",
                "slug": "existing",
            }
        )
        self.assert_problem_response(response, status_code=422)

    def test_missing_required_field_returns_422(self):
        self.login()
        response = self.post(
            {
                "meta": {
                    "parent_id": self.root_page.pk,
                    "type": "tests.MultiPreviewModesPage",
                },
                "slug": "no-title",
            }
        )
        self.assert_problem_response(response, status_code=422)

    def test_page_type_with_required_field_outside_api_fields_returns_422(self):
        """
        SimplePage.content is required by the real admin form but isn't in
        api_fields, so it's absent from the input schema entirely - the form
        rejects the create rather than silently creating a blank page.
        """
        self.login()
        response = self.post(
            {
                "meta": {"parent_id": self.root_page.pk, "type": "tests.SimplePage"},
                "title": "New page",
                "slug": "new-page",
            }
        )
        self.assert_problem_response(response, status_code=422)

    def test_unknown_parent_returns_404(self):
        self.login()
        response = self.post(
            {
                "meta": {"parent_id": 999999, "type": "tests.MultiPreviewModesPage"},
                "title": "New page",
                "slug": "new-page",
            }
        )
        self.assert_problem_response(response, status_code=404)

    def test_unknown_type_returns_422(self):
        self.login()
        response = self.post(
            {
                "meta": {"parent_id": self.root_page.pk, "type": "not.AType"},
                "title": "New page",
                "slug": "new-page",
            }
        )
        self.assert_problem_response(response, status_code=422)

    def test_user_without_add_permission_gets_403(self):
        self.create_user(username="noperms", password="password")
        self.login(username="noperms", password="password")
        response = self.post(
            {
                "meta": {
                    "parent_id": self.root_page.pk,
                    "type": "tests.MultiPreviewModesPage",
                },
                "title": "New page",
                "slug": "new-page",
            }
        )
        self.assert_problem_response(response, status_code=403)

    def test_user_with_add_permission_on_branch_can_create(self):
        editor = self.create_user(username="editor", password="password")
        editor_group = Group.objects.create(name="Page branch editors")
        editor.groups.add(editor_group)
        GroupPagePermission.objects.create(
            group=editor_group,
            page=self.root_page,
            permission=Permission.objects.get(
                content_type__app_label="wagtailcore", codename="add_page"
            ),
        )
        self.login(username="editor", password="password")
        response = self.post(
            {
                "meta": {
                    "parent_id": self.root_page.pk,
                    "type": "tests.MultiPreviewModesPage",
                },
                "title": "New page",
                "slug": "new-page",
            }
        )
        self.assertEqual(response.status_code, 201)

    def test_disallowed_subpage_type_returns_403(self):
        self.login()
        # MultiPreviewModesPage's default page-type rules allow being created
        # under the root, but wagtailcore.Page itself is not creatable at all.
        parent = self.root_page.add_child(
            instance=MultiPreviewModesPage(title="Parent", slug="parent-page")
        )
        response = self.post(
            {
                "meta": {"parent_id": parent.pk, "type": "wagtailcore.Page"},
                "title": "New page",
                "slug": "new-page",
            }
        )
        self.assert_problem_response(response, status_code=403)

    def test_create_streamfield_page(self):
        self.login()
        response = self.post(
            {
                "meta": {"parent_id": self.root_page.pk, "type": "tests.StreamPage"},
                "title": "Stream page",
                "slug": "stream-page",
                "body": [{"type": "text", "value": "hello streamfield"}],
            }
        )
        self.assertEqual(response.status_code, 201)
        page = StreamPage.objects.get(slug="stream-page")
        self.assertEqual(len(page.body), 1)
        self.assertEqual(page.body[0].block_type, "text")
        self.assertEqual(page.body[0].value, "hello streamfield")

    def test_create_streamfield_page_with_invalid_block_type_returns_422(self):
        self.login()
        response = self.post(
            {
                "meta": {"parent_id": self.root_page.pk, "type": "tests.StreamPage"},
                "title": "Stream page",
                "slug": "stream-page-invalid",
                "body": [{"type": "not_a_real_block", "value": "hello"}],
            }
        )
        self.assert_problem_response(response, status_code=422)

    def test_create_page_with_rich_text_field(self):
        self.login()
        response = self.post(
            {
                "meta": {"parent_id": self.root_page.pk, "type": "demosite.HomePage"},
                "title": "Home",
                "slug": "home-rich-text",
                "body": "<p>hello</p>",
                "carousel_items": [],
            }
        )
        self.assertEqual(response.status_code, 201)
        page = HomePage.objects.get(slug="home-rich-text")
        self.assertIn("hello", page.body)

    def test_create_page_with_child_relations(self):
        self.login()
        response = self.post(
            {
                "meta": {"parent_id": self.root_page.pk, "type": "demosite.HomePage"},
                "title": "Home",
                "slug": "home-with-children",
                "body": "<p>hi</p>",
                "carousel_items": [
                    {
                        "caption": "First",
                        "embed_url": "http://example.com/1",
                        "link_external": "http://example.com/1",
                    },
                    {
                        "caption": "Second",
                        "embed_url": "http://example.com/2",
                        "link_external": "http://example.com/2",
                    },
                ],
            }
        )
        self.assertEqual(response.status_code, 201)
        page = HomePage.objects.get(slug="home-with-children")
        items = list(page.carousel_items.order_by("sort_order"))
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].caption, "First")
        self.assertEqual(items[1].caption, "Second")
        self.assertEqual(items[0].sort_order, 0)
        self.assertEqual(items[1].sort_order, 1)

    def test_create_page_with_invalid_child_relation_field_returns_422(self):
        self.login()
        response = self.post(
            {
                "meta": {"parent_id": self.root_page.pk, "type": "demosite.HomePage"},
                "title": "Home",
                "slug": "home-invalid-child",
                "body": "<p>hi</p>",
                "carousel_items": [
                    {
                        "caption": "x" * 1000,
                        "embed_url": "http://example.com/1",
                        "link_external": "http://example.com/1",
                    },
                ],
            }
        )
        self.assert_problem_response(response, status_code=422)

    def test_create_page_with_child_relation_missing_link_returns_422(self):
        """
        AbstractLinkFields.clean() (a custom cross-field validator on
        HomePageCarouselItem's own form) requires a related page, document,
        or external URL - this is real form-level validation, not something
        the input schema itself can express, and it runs because we validate
        through the model's actual admin form rather than bypassing it.
        """
        self.login()
        response = self.post(
            {
                "meta": {"parent_id": self.root_page.pk, "type": "demosite.HomePage"},
                "title": "Home",
                "slug": "home-missing-link",
                "body": "<p>hi</p>",
                "carousel_items": [{"caption": "No link"}],
            }
        )
        self.assert_problem_response(response, status_code=422)
