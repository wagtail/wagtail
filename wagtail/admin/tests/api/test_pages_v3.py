from django.contrib.auth.models import Permission
from django.test import override_settings
from django.urls import reverse

from wagtail.models import Locale
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
