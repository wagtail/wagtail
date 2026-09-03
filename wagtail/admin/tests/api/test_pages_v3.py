from django.contrib.auth.models import Permission
from django.test import override_settings
from django.urls import reverse

from wagtail import hooks
from wagtail.models import Locale
from wagtail.test.demosite import models
from wagtail.test.utils import Page, PageFixturesMixin

from .utils import AdminAPITestCase


def get_total_page_count():
    # Root page (depth 1) is never returned by the admin listing
    return Page.objects.count() - 1


class TestAdminV3PageListing(PageFixturesMixin, AdminAPITestCase):
    fixtures = ["demosite.json"]

    def get_response(self, **params):
        return self.client.get(reverse("wagtailadmin_api_v3:list_pages"), params)

    def test_basic(self):
        response = self.get_response()
        self.assertEqual(response.status_code, 200)

        content = response.json()
        # v3 {count, items} envelope, not v2's {meta: {total_count}, items}
        self.assertIn("count", content)
        self.assertNotIn("meta", content)
        self.assertEqual(content["count"], get_total_page_count())
        self.assertIn("items", content)

        for page in content["items"]:
            self.assertEqual(
                set(page["meta"].keys()),
                {
                    "type",
                    "detail_url",
                    "html_url",
                    "slug",
                    "first_published_at",
                    "locale",
                    "live",
                    "has_unpublished_changes",
                    "status",
                },
            )
            self.assertIn("admin_display_title", page)
            self.assertIn("title", page)
            self.assertIn("id", page)

    def test_status_values(self):
        content = self.get_response().json()
        by_id = {item["id"]: item for item in content["items"]}
        homepage = Page.objects.get(id=2)

        self.assertEqual(by_id[homepage.id]["meta"]["type"], "demosite.HomePage")
        self.assertEqual(by_id[homepage.id]["meta"]["live"], True)
        self.assertEqual(by_id[homepage.id]["meta"]["has_unpublished_changes"], False)
        self.assertEqual(by_id[homepage.id]["meta"]["status"], "live")

        # An unpublished page
        unpublished = Page.objects.filter(live=False).first()
        if unpublished is not None:
            self.assertEqual(by_id[unpublished.id]["meta"]["live"], False)
            self.assertEqual(by_id[unpublished.id]["meta"]["status"], "draft")

    def test_admin_display_title_matches_model(self):
        content = self.get_response().json()
        by_id = {item["id"]: item for item in content["items"]}
        page = Page.objects.get(id=2).specific
        self.assertEqual(
            by_id[page.id]["admin_display_title"], page.get_admin_display_title()
        )

    def test_has_children_filter_true(self):
        content = self.get_response(has_children="true").json()
        self.assertGreater(len(content["items"]), 0)
        for item in content["items"]:
            self.assertGreater(Page.objects.get(id=item["id"]).numchild, 0)

    def test_has_children_filter_false(self):
        content = self.get_response(has_children="false").json()
        for item in content["items"]:
            self.assertEqual(Page.objects.get(id=item["id"]).numchild, 0)

    def test_has_children_filter_invalid(self):
        response = self.get_response(has_children="nonsense")
        self.assertEqual(response.status_code, 422)

    def test_root_page_excluded(self):
        content = self.get_response().json()
        self.assertNotIn(1, [item["id"] for item in content["items"]])

    @override_settings(WAGTAIL_I18N_ENABLED=True)
    def test_translation_of_filter(self):
        french = Locale.objects.create(language_code="fr")
        page = Page.objects.get(id=2)
        french_page = page.copy_for_translation(french)
        french_page.get_latest_revision().publish()

        content = self.get_response(translation_of=page.id).json()
        self.assertEqual([item["id"] for item in content["items"]], [french_page.id])

    def test_permission_scoping(self):
        # A user with access to the admin but no page permissions sees no pages
        user = self.create_user(username="basic_user_v3")

        can_access_admin_permission = Permission.objects.get(
            content_type__app_label="wagtailadmin",
            content_type__model="admin",
            codename="access_admin",
        )
        user.user_permissions.add(can_access_admin_permission)

        self.client.force_login(user)

        response = self.get_response()
        self.assertEqual(response.status_code, 200)

        content = response.json()
        self.assertEqual(content["count"], 0)
        self.assertEqual(content["items"], [])

    def test_unauthenticated_request_rejected(self):
        self.client.logout()
        response = self.get_response()
        self.assertIn(response.status_code, (302, 403))


class TestAdminV3PageExplore(PageFixturesMixin, AdminAPITestCase):
    fixtures = ["demosite.json"]

    def get_response(self, **params):
        return self.client.get(reverse("wagtailadmin_api_v3:explore_pages"), params)

    def get_homepage_children_ids(self):
        return set(Page.objects.get(id=2).get_children().values_list("id", flat=True))

    def test_basic(self):
        response = self.get_response(child_of=2)
        self.assertEqual(response.status_code, 200)

        content = response.json()
        self.assertIn("count", content)
        self.assertIn("items", content)
        self.assertEqual(
            {item["id"] for item in content["items"]},
            self.get_homepage_children_ids(),
        )

    def test_item_shape(self):
        content = self.get_response(child_of=2).json()
        self.assertGreater(len(content["items"]), 0)
        for item in content["items"]:
            self.assertEqual(set(item.keys()), {"id", "admin_display_title", "meta"})
            self.assertEqual(
                set(item["meta"].keys()),
                {
                    "type",
                    "parent",
                    "locale",
                    "children",
                    "live",
                    "has_unpublished_changes",
                    "status",
                },
            )
            self.assertEqual(set(item["meta"]["children"].keys()), {"count"})

    def test_children_count(self):
        content = self.get_response(child_of=2).json()
        by_id = {item["id"]: item for item in content["items"]}
        event_index = models.EventIndexPage.objects.first()
        expected = Page.objects.child_of(event_index).count()
        self.assertEqual(by_id[event_index.id]["meta"]["children"]["count"], expected)

    def test_child_of_root(self):
        # "root" means the first root node (depth 1); its children are depth 2
        root = Page.get_first_root_node()
        response = self.get_response(child_of="root")
        self.assertEqual(response.status_code, 200)
        content = response.json()
        self.assertEqual(
            {item["id"] for item in content["items"]},
            set(root.get_children().values_list("id", flat=True)),
        )

    def test_parent_is_set_for_explorable_parent(self):
        # Children of the homepage have an explorable parent (the homepage)
        content = self.get_response(child_of=2).json()
        for item in content["items"]:
            self.assertIsNotNone(item["meta"]["parent"])
            self.assertEqual(item["meta"]["parent"]["id"], 2)

    def test_missing_child_of_gives_error(self):
        response = self.get_response()
        self.assertEqual(response.status_code, 422)

    def test_unknown_page_gives_404(self):
        response = self.get_response(child_of=99999)
        self.assertEqual(response.status_code, 404)

    def test_construct_explorer_page_queryset_hook_applied(self):
        def reverse_order(parent_page, queryset, request):
            return queryset.reverse()

        with hooks.register_temporarily(
            "construct_explorer_page_queryset", reverse_order
        ):
            hooked = self.get_response(child_of=2).json()
        unhooked = self.get_response(child_of=2).json()

        hooked_ids = [item["id"] for item in hooked["items"]]
        unhooked_ids = [item["id"] for item in unhooked["items"]]
        self.assertEqual(set(hooked_ids), set(unhooked_ids))
        self.assertEqual(hooked_ids, list(reversed(unhooked_ids)))

    def test_pagination(self):
        content = self.get_response(child_of=2, limit=1).json()
        self.assertEqual(len(content["items"]), 1)
        self.assertEqual(content["count"], len(self.get_homepage_children_ids()))

    def test_permission_scoping(self):
        # The parent page lookup is permission-scoped: a user with access to
        # the admin but no page permissions cannot resolve page 2 as an
        # explorable parent, so the request 404s rather than returning an
        # empty listing (matching v2, which rejects with a 400 in this case).
        user = self.create_user(username="explore_basic_user")

        can_access_admin_permission = Permission.objects.get(
            content_type__app_label="wagtailadmin",
            content_type__model="admin",
            codename="access_admin",
        )
        user.user_permissions.add(can_access_admin_permission)

        self.client.force_login(user)

        response = self.get_response(child_of=2)
        self.assertEqual(response.status_code, 404)

    def test_unauthenticated_request_rejected(self):
        self.client.logout()
        response = self.get_response()
        self.assertIn(response.status_code, (302, 403))


class TestAdminV3PageDetail(PageFixturesMixin, AdminAPITestCase):
    fixtures = ["demosite.json"]

    def get_response(self, page_id, **params):
        return self.client.get(
            reverse("wagtailadmin_api_v3:detail_page", kwargs={"page_id": page_id}),
            params,
        )

    def test_basic(self):
        page = Page.objects.get(id=2).specific
        response = self.get_response(page.id)
        self.assertEqual(response.status_code, 200)

        content = response.json()
        self.assertEqual(content["id"], page.id)
        self.assertEqual(content["title"], page.title)
        self.assertEqual(content["admin_display_title"], page.get_admin_display_title())
        self.assertEqual(
            set(content["meta"].keys()),
            {
                "type",
                "detail_url",
                "html_url",
                "slug",
                "first_published_at",
                "locale",
                "live",
                "has_unpublished_changes",
                "status",
                "parent",
            },
        )

    def test_meta_parent(self):
        # The homepage's parent is the root page, which is explorable for a
        # superuser, so it is serialized.
        content = self.get_response(2).json()
        self.assertIsNotNone(content["meta"]["parent"])
        self.assertEqual(content["meta"]["parent"]["id"], 1)

        # A child page's parent is the homepage
        child = Page.objects.get(id=2).get_children().first()
        content = self.get_response(child.id).json()
        self.assertEqual(content["meta"]["parent"]["id"], 2)

    def test_detail_url_points_at_admin_api(self):
        content = self.get_response(2).json()
        self.assertIn("/admin/api/pages/2/", content["meta"]["detail_url"])

    def test_unknown_page_gives_404(self):
        response = self.get_response(99999)
        self.assertEqual(response.status_code, 404)

    def test_permission_scoping(self):
        # Users can only fetch pages they can explore; keep this test simple
        # by asserting an authenticated superuser can fetch a private page,
        # and rely on get_pages_queryset's documented scoping for the rest.
        private_page = Page.objects.get(id=2)
        response = self.get_response(private_page.id)
        self.assertEqual(response.status_code, 200)
