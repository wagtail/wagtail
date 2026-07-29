from django.test import TestCase, override_settings
from django.urls import reverse

from wagtail.api.v3.tests.base import TestV3Base
from wagtail.models import Locale, Page, Site
from wagtail.models.view_restrictions import BaseViewRestriction
from wagtail.test.demosite import models
from wagtail.test.utils import WagtailTestUtils


def get_total_page_count():
    return (
        Page.objects.descendant_of(
            Site.objects.get(is_default_site=True).root_page, inclusive=True
        )
        .live()
        .public()
        .count()
    )


class TestV3PageListingBase(TestV3Base, WagtailTestUtils, TestCase):
    fixtures = ["demosite.json"]

    def get_response(self, **params):
        return self.client.get(reverse("wagtailapi_v3:list_pages"), params)

    def get_page_id_list(self, content):
        return [page["id"] for page in content["items"]]

    def get_all_page_ids(self):
        with override_settings(WAGTAILAPI_LIMIT_MAX=None):
            content = self.get_response(limit=100_000).json()
        return self.get_page_id_list(content)


class TestV3PageListing(TestV3PageListingBase):
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
                {
                    "type",
                    "detail_url",
                    "html_url",
                    "slug",
                    "first_published_at",
                    "locale",
                },
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


class TestV3PageListingFilters(TestV3PageListingBase):
    fixtures = ["demosite.json"]

    def test_type_filter_items_are_all_blog_entries(self):
        response = self.get_response(type="demosite.BlogEntryPage")
        content = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(content["items"]), 0)
        for page in content["items"]:
            self.assertEqual(page["meta"]["type"], "demosite.BlogEntryPage")

    def test_type_filter_total_count(self):
        expected_count = models.BlogEntryPage.objects.live().public().count()
        response = self.get_response(type="demosite.BlogEntryPage")
        content = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(content["count"], expected_count)

    def test_type_filter_multiple(self):
        response = self.client.get(
            reverse("wagtailapi_v3:list_pages"),
            {"type": ["demosite.BlogEntryPage", "demosite.EventPage"]},
        )
        content = response.json()

        expected_count = (
            models.BlogEntryPage.objects.live().public().count()
            + models.EventPage.objects.live().public().count()
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(content["count"], expected_count)

        seen_types = {page["meta"]["type"] for page in content["items"]}
        self.assertEqual(seen_types, {"demosite.BlogEntryPage", "demosite.EventPage"})

    def test_type_filter_base_page_type_matches_everything(self):
        response = self.get_response(type=Page._meta.label)
        content = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(content["count"], get_total_page_count())

    def test_non_existent_type_gives_error(self):
        response = self.get_response(type="demosite.IDontExist")
        self.assert_problem_response(
            response,
            status_code=422,
            detail_contains="Validation failed",
            errors=[{"type": "literal_error", "loc": ["query", "filters", "type", 0]}],
        )

    def test_non_page_type_gives_error(self):
        response = self.get_response(type="auth.User")
        self.assert_problem_response(
            response,
            status_code=422,
            detail_contains="Validation failed",
            errors=[{"type": "literal_error", "loc": ["query", "filters", "type", 0]}],
        )

    def test_ancestor_of_filter(self):
        response = self.get_response(ancestor_of=10)
        content = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.get_page_id_list(content), [2, 6])

    def test_ancestor_of_with_type(self):
        response = self.get_response(type="demosite.EventIndexPage", ancestor_of=8)
        content = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.get_page_id_list(content), [4])

    def test_ancestor_of_unknown_page_gives_error(self):
        response = self.get_response(ancestor_of=1000)
        self.assert_problem_response(
            response,
            status_code=404,
            detail_contains="No Page matches the given query.",
        )

    def test_ancestor_of_not_positive_integer_gives_error(self):
        response = self.get_response(ancestor_of="abc")
        self.assert_problem_response(
            response,
            status_code=422,
            detail_contains="Validation failed",
            errors=[
                {
                    "type": "int_parsing",
                    "loc": ["query", "ancestor_of"],
                    "msg": "Input should be a valid integer, unable to parse string as an integer",
                },
            ],
        )

    def test_ancestor_of_home_page_ignores_root(self):
        # Root page is not in any site, so pretend it doesn't exist
        response = self.get_response(ancestor_of=2)
        content = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.get_page_id_list(content), [])

    def test_child_of_filter(self):
        response = self.get_response(child_of=5)
        content = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.get_page_id_list(content), [16, 18, 19])

    def test_child_of_root(self):
        response = self.get_response(child_of="root")
        content = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.get_page_id_list(content), [4, 5, 6, 12, 20])

    def test_child_of_with_type(self):
        response = self.get_response(type="demosite.EventPage", child_of=5)
        content = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.get_page_id_list(content), [])

    def test_child_of_unknown_page_gives_error(self):
        response = self.get_response(child_of=1000)
        self.assert_problem_response(
            response,
            status_code=404,
            detail_contains="No Page matches the given query.",
        )

    def test_child_of_not_positive_integer_gives_error(self):
        response = self.get_response(child_of="abc")
        literal_error = {
            "type": "literal_error",
            "loc": ["query", "filters", "child_of", "literal['root']"],
        }
        self.assert_problem_response(
            response,
            status_code=422,
            detail_contains="Validation failed",
            errors=[
                {
                    "type": "int_parsing",
                    "loc": ["query", "filters", "child_of", "constrained-int"],
                    "msg": "Input should be a valid integer, unable to parse string as an integer",
                },
                literal_error,
            ],
        )

        response = self.get_response(child_of=-5)
        self.assert_problem_response(
            response,
            status_code=422,
            detail_contains="Validation failed",
            errors=[
                {
                    "type": "greater_than",
                    "loc": ["query", "filters", "child_of", "constrained-int"],
                    "msg": "Input should be greater than 0",
                    "ctx": {"gt": 0},
                },
                literal_error,
            ],
        )

    def test_child_of_page_thats_not_in_same_site_gives_error(self):
        # Root page is not in any site, so pretend it doesn't exist
        response = self.get_response(child_of=1)
        self.assert_problem_response(
            response,
            status_code=404,
            detail_contains="No Page matches the given query.",
        )

    def test_descendant_of_filter(self):
        response = self.get_response(descendant_of=6)
        content = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.get_page_id_list(content), [10, 15, 17, 21, 22, 23])

    def test_descendant_of_root(self):
        # "root" gets descendants of the homepage of the current site
        # Basically returns every page except the homepage
        response = self.get_response(descendant_of="root")
        content = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.get_page_id_list(content),
            [4, 5, 6, 8, 9, 10, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23],
        )

    def test_descendant_of_with_type(self):
        response = self.get_response(type="demosite.EventIndexPage", descendant_of=2)
        content = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.get_page_id_list(content), [4])

    def test_descendant_of_unknown_page_gives_error(self):
        response = self.get_response(descendant_of=1000)
        self.assert_problem_response(
            response,
            status_code=404,
            detail_contains="No Page matches the given query.",
        )

    def test_descendant_of_not_positive_integer_gives_error(self):
        response = self.get_response(descendant_of="abc")
        literal_error = {
            "type": "literal_error",
            "loc": ["query", "filters", "descendant_of", "literal['root']"],
        }
        self.assert_problem_response(
            response,
            status_code=422,
            detail_contains="Validation failed",
            errors=[
                {
                    "type": "int_parsing",
                    "loc": ["query", "filters", "descendant_of", "constrained-int"],
                    "msg": "Input should be a valid integer, unable to parse string as an integer",
                },
                literal_error,
            ],
        )

    def test_descendant_of_page_thats_not_in_same_site_gives_error(self):
        # Root page is not in any site, so pretend it doesn't exist
        response = self.get_response(descendant_of=1)
        self.assert_problem_response(
            response,
            status_code=404,
            detail_contains="No Page matches the given query.",
        )

    def test_descendant_of_when_filtering_by_child_of_gives_error(self):
        response = self.get_response(descendant_of=6, child_of=5)
        self.assert_problem_response(
            response,
            status_code=422,
            detail_contains="Validation failed",
            errors=[
                {
                    "type": "value_error",
                    "msg": "Value error, filtering by descendant_of with child_of is not supported.",
                }
            ],
        )

    @override_settings(WAGTAIL_I18N_ENABLED=True)
    def test_translation_of_filter(self):
        french = Locale.objects.create(language_code="fr")
        homepage = Page.objects.get(id=2)
        french_homepage = homepage.copy_for_translation(french)
        french_homepage.get_latest_revision().publish()

        response = self.get_response(translation_of=homepage.id)
        content = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.get_page_id_list(content), [french_homepage.id])

    def test_translation_of_root(self):
        response = self.get_response(translation_of="root")
        content = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.get_page_id_list(content), [])

    def test_translation_of_unknown_page_gives_error(self):
        response = self.get_response(translation_of=1000)
        self.assert_problem_response(
            response,
            status_code=404,
            detail_contains="No Page matches the given query.",
        )

    @override_settings(WAGTAIL_I18N_ENABLED=True)
    def test_locale_filter(self):
        french = Locale.objects.create(language_code="fr")
        homepage = Page.objects.get(id=2)
        french_homepage = homepage.copy_for_translation(french)
        french_homepage.get_latest_revision().publish()

        response = self.get_response(locale="fr")
        content = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.get_page_id_list(content), [french_homepage.id])


class TestV3PageListingOrdering(TestV3PageListingBase):
    def test_ordering_default(self):
        response = self.get_response()
        content = response.json()

        self.assertEqual(response.status_code, 200)
        # v3 orders by id rather than treebeard path (v2 parity does not
        # apply to ordering here).
        self.assertEqual(
            self.get_page_id_list(content),
            [2, 4, 5, 6, 8, 9, 10, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23],
        )

    def test_ordering_by_title(self):
        response = self.get_response(order="title")
        content = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.get_page_id_list(content),
            [21, 22, 19, 23, 5, 16, 18, 12, 14, 8, 9, 4, 2, 13, 20, 17, 6, 10, 15],
        )

    def test_ordering_by_title_backwards(self):
        response = self.get_response(order="-title")
        content = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.get_page_id_list(content),
            [15, 10, 6, 17, 20, 13, 2, 4, 9, 8, 14, 12, 18, 16, 5, 23, 19, 22, 21],
        )

    def test_ordering_by_random(self):
        content_1 = self.get_response(order="random").json()
        page_id_list_1 = self.get_page_id_list(content_1)

        content_2 = self.get_response(order="random").json()
        page_id_list_2 = self.get_page_id_list(content_2)

        self.assertNotEqual(page_id_list_1, page_id_list_2)

    def test_ordering_by_random_backwards_gives_error(self):
        response = self.get_response(order="-random")
        self.assert_problem_response(
            response,
            status_code=422,
            detail_contains="Validation failed",
            errors=[
                {
                    "type": "value_error",
                    "msg": "Value error, invalid fields for model Page: ['-random'].",
                }
            ],
        )

    def test_ordering_by_random_with_offset_gives_error(self):
        response = self.get_response(order="random", offset=10)
        self.assert_problem_response(
            response,
            status_code=422,
            detail_contains="Validation failed",
            errors=[
                {
                    "type": "value_error",
                    "msg": "Value error, random ordering with offset is not supported.",
                }
            ],
        )

    def test_ordering_default_with_type(self):
        response = self.get_response(type="demosite.BlogEntryPage")
        content = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.get_page_id_list(content), [16, 18, 19])

    def test_ordering_by_title_with_type(self):
        response = self.get_response(type="demosite.BlogEntryPage", order="title")
        content = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.get_page_id_list(content), [19, 16, 18])

    def test_ordering_by_specific_field_with_type(self):
        response = self.get_response(type="demosite.BlogEntryPage", order="date")
        content = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.get_page_id_list(content), [16, 18, 19])

    def test_ordering_by_unknown_field_gives_error(self):
        response = self.get_response(order="not_a_field")
        self.assert_problem_response(
            response,
            status_code=422,
            detail_contains="Validation failed",
            errors=[
                {
                    "type": "value_error",
                    "msg": "Value error, invalid fields for model Page: ['not_a_field'].",
                }
            ],
        )

    def test_random_ordering_with_unknown_field_gives_error(self):
        response = self.get_response(order=["random", "id"])
        self.assert_problem_response(
            response,
            status_code=422,
            detail_contains="Validation failed",
            errors=[
                {
                    "type": "value_error",
                    "msg": "Value error, random ordering cannot be combined with other fields.",
                }
            ],
        )

    def test_ordering_by_id_and_slug(self):
        response = self.get_response(order=["id", "slug"])
        content = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.get_page_id_list(content),
            [2, 4, 5, 6, 8, 9, 10, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23],
        )

    def test_ordering_by_title_and_id_backwards(self):
        response = self.get_response(order=["title", "-id"])
        content = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.get_page_id_list(content)[:5],
            [21, 22, 19, 23, 5],
        )


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
            {
                "type",
                "detail_url",
                "html_url",
                "slug",
                "first_published_at",
                "locale",
            },
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
