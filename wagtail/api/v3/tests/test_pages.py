import swapper
from django.test import TestCase, override_settings
from django.urls import reverse

from wagtail.api.v3.tests.base import TestV3Base
from wagtail.models import Locale, Site
from wagtail.models.view_restrictions import BaseViewRestriction
from wagtail.test.demosite import models
from wagtail.test.utils import WagtailTestUtils

if swapper.is_swapped("wagtailcore", "Page"):
    from wagtail.test.basepage.models import BasePage as Page
else:
    from wagtail.models import Page


def get_total_page_count():
    return (
        Page.objects.descendant_of(
            Site.objects.get(is_default_site=True).root_page, inclusive=True
        )
        .live()
        .public()
        .count()
    )


class TestV3PageListing(TestV3Base, WagtailTestUtils, TestCase):
    fixtures = ["demosite.json"]

    def get_response(self, **params):
        return self.client.get(reverse("wagtailapi_v3:list_pages"), params)

    def get_page_id_list(self, content):
        return [page["id"] for page in content["items"]]

    def get_all_page_ids(self):
        with override_settings(WAGTAILAPI_LIMIT_MAX=None):
            content = self.get_response(limit=100_000).json()
        return self.get_page_id_list(content)

    def test_basic(self):
        response = self.get_response()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response["Content-Type"].startswith("application/json"))

        content = response.json()
        self.assertIn("count", content)
        self.assertEqual(content["count"], get_total_page_count())
        self.assertIn("items", content)

        for page in content["items"]:
            self.assertIn("meta", page)
            self.assertEqual(
                set(page["meta"].keys()),
                {"type", "detail_url", "html_url", "slug", "first_published_at"},
            )

    @override_settings(WAGTAILAPI_BASE_URL="https://api.example.com")
    def test_listing_meta_values_for_homepage(self):
        homepage = Page.objects.get(id=2)
        content = self.get_response().json()
        page_json = next(item for item in content["items"] if item["id"] == homepage.id)

        self.assertEqual(page_json["title"], homepage.title)
        self.assertEqual(page_json["meta"]["slug"], homepage.slug)
        self.assertEqual(page_json["meta"]["type"], "demosite.HomePage")
        self.assertTrue(
            page_json["meta"]["detail_url"].startswith("https://api.example.com")
        )
        self.assertIn(f"/api/v3/pages/{homepage.id}/", page_json["meta"]["detail_url"])
        self.assertIsNotNone(page_json["meta"]["html_url"])

    def test_listing_meta_type_uses_specific_class(self):
        blog_entry = models.BlogEntryPage.objects.get(id=16)
        content = self.get_response().json()
        page_json = next(
            item for item in content["items"] if item["id"] == blog_entry.id
        )
        self.assertEqual(page_json["meta"]["type"], "demosite.BlogEntryPage")

    def test_default_limit_is_20(self):
        content = self.get_response().json()
        self.assertEqual(len(content["items"]), min(20, get_total_page_count()))

    def test_offset_and_limit_return_expected_slice(self):
        all_ids = self.get_all_page_ids()
        content = self.get_response(offset=3, limit=2).json()
        self.assertEqual(self.get_page_id_list(content), all_ids[3:5])

    def test_offset_beyond_count_returns_empty_items(self):
        total = get_total_page_count()
        content = self.get_response(offset=total + 100).json()
        self.assertEqual(content["count"], total)
        self.assertEqual(content["items"], [])

    def test_offset_does_not_change_count(self):
        content = self.get_response(offset=10).json()
        self.assertEqual(content["count"], get_total_page_count())

    def test_unpublished_pages_excluded(self):
        total_count = get_total_page_count()
        page = models.BlogEntryPage.objects.get(id=16)
        page.unpublish()

        content = self.get_response().json()
        self.assertEqual(content["count"], total_count - 1)

    def test_private_pages_excluded(self):
        total_count = get_total_page_count()
        page = models.BlogIndexPage.objects.get(id=5)
        page.view_restrictions.create(
            restriction_type=BaseViewRestriction.PASSWORD, password="test"
        )

        new_total_count = get_total_page_count()
        self.assertNotEqual(total_count, new_total_count)

        content = self.get_response().json()
        self.assertEqual(content["count"], new_total_count)

    def test_login_gated_pages_excluded_anonymously(self):
        page = models.BlogIndexPage.objects.get(id=5)
        page.view_restrictions.create(restriction_type=BaseViewRestriction.LOGIN)

        content = self.get_response().json()
        self.assertEqual(content["count"], get_total_page_count())

    def test_login_gated_pages_visible_when_logged_in(self):
        page = models.BlogIndexPage.objects.get(id=5)
        old_total_count = get_total_page_count()
        page.view_restrictions.create(restriction_type=BaseViewRestriction.LOGIN)

        self.create_user(username="alice", password="password")
        self.login(username="alice", password="password")
        content = self.get_response().json()
        self.assertEqual(content["count"], old_total_count)

    @override_settings(WAGTAIL_I18N_ENABLED=True)
    def test_i18n_translation_pages_included_in_listing(self):
        french = Locale.objects.create(language_code="fr")
        homepage = Page.objects.get(slug="home-page")
        french_homepage = homepage.copy_for_translation(french)
        french_homepage.get_latest_revision().publish()

        page_ids = self.get_all_page_ids()
        self.assertIn(french_homepage.id, page_ids)

    @override_settings(WAGTAILAPI_LIMIT_MAX=5)
    def test_limit_max_enforced(self):
        response = self.get_response(limit=10)
        self.assert_problem_response(response, status_code=400)

    @override_settings(WAGTAILAPI_LIMIT_MAX=5)
    def test_limit_within_max(self):
        content = self.get_response(limit=5).json()
        self.assertLessEqual(len(content["items"]), 5)


class TestV3PageDetail(WagtailTestUtils, TestCase):
    fixtures = ["demosite.json"]

    def test_detail(self):
        page = Page.objects.get(id=2)
        response = self.client.get(
            reverse("wagtailapi_v3:detail_page", kwargs={"page_id": page.id})
        )
        self.assertEqual(response.status_code, 200)
        content = response.json()
        self.assertEqual(content["id"], page.id)
        self.assertEqual(content["title"], page.title)

    @override_settings(WAGTAILAPI_BASE_URL="https://api.example.com")
    def test_detail_meta_values(self):
        homepage = Page.objects.get(id=2).specific
        response = self.client.get(
            reverse("wagtailapi_v3:detail_page", kwargs={"page_id": homepage.id})
        )
        content = response.json()

        self.assertEqual(
            set(content["meta"].keys()),
            {"type", "detail_url", "html_url", "slug", "first_published_at"},
        )
        self.assertEqual(content["meta"]["slug"], homepage.slug)
        self.assertEqual(content["meta"]["type"], "demosite.HomePage")
        self.assertTrue(
            content["meta"]["detail_url"].startswith("https://api.example.com")
        )
        self.assertIn(f"/api/v3/pages/{homepage.id}/", content["meta"]["detail_url"])
        self.assertIsNotNone(content["meta"]["html_url"])

    def test_detail_meta_type_uses_specific_class(self):
        blog_entry = models.BlogEntryPage.objects.get(id=16)
        response = self.client.get(
            reverse("wagtailapi_v3:detail_page", kwargs={"page_id": blog_entry.id})
        )
        content = response.json()
        self.assertEqual(content["meta"]["type"], "demosite.BlogEntryPage")

    def test_detail_not_found(self):
        response = self.client.get(
            reverse("wagtailapi_v3:detail_page", kwargs={"page_id": 999999})
        )
        self.assertEqual(response.status_code, 404)
