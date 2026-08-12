import unittest
from io import StringIO

import swapper
from django.core import management
from django.test import TestCase, TransactionTestCase, override_settings, tag
from django.urls import reverse

from wagtail.api.v3.tests.base import TestV3Base
from wagtail.models import Locale, Site
from wagtail.models.view_restrictions import BaseViewRestriction
from wagtail.test.demosite import models
from wagtail.test.utils import Page, PageFixturesMixin, WagtailTestUtils


def get_total_page_count():
    return (
        Page.objects.descendant_of(
            Site.objects.get(is_default_site=True).root_page, inclusive=True
        )
        .live()
        .public()
        .count()
    )


class TestV3PageListingBase(PageFixturesMixin, TestV3Base, WagtailTestUtils):
    fixtures = ["demosite.json"]
    page_name = Page._meta.object_name

    def get_response(self, **params):
        return self.client.get(reverse("wagtailapi_v3:list_pages"), params)

    def get_page_id_list(self, content):
        return [page["id"] for page in content["items"]]

    def get_all_page_ids(self):
        with override_settings(WAGTAILAPI_LIMIT_MAX=None):
            content = self.get_response(limit=100_000).json()
        return self.get_page_id_list(content)


class TestV3PageListing(TestV3PageListingBase, TestCase):
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

    def test_unpublished_pages_included_when_logged_in(self):
        page = models.BlogEntryPage.objects.get(id=16)
        page.unpublish()

        self.login()
        self.assertIn(page.id, self.get_all_page_ids())

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

    @unittest.expectedFailure
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


class TestV3PageListingFilters(TestV3PageListingBase, TestCase):
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
            status_code=422,
            detail_contains="Validation failed",
            errors=[
                {
                    "type": "does_not_exist",
                    "loc": ["ancestor_of"],
                    "msg": f"No {self.page_name} matches the given ancestor_of value.",
                }
            ],
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
            status_code=422,
            detail_contains="Validation failed",
            errors=[
                {
                    "type": "does_not_exist",
                    "loc": ["child_of"],
                    "msg": f"No {self.page_name} matches the given child_of value.",
                }
            ],
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
            status_code=422,
            detail_contains="Validation failed",
            errors=[
                {
                    "type": "does_not_exist",
                    "loc": ["child_of"],
                    "msg": f"No {self.page_name} matches the given child_of value.",
                }
            ],
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
            status_code=422,
            detail_contains="Validation failed",
            errors=[
                {
                    "type": "does_not_exist",
                    "loc": ["descendant_of"],
                    "msg": f"No {self.page_name} matches the given descendant_of value.",
                }
            ],
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
            status_code=422,
            detail_contains="Validation failed",
            errors=[
                {
                    "type": "does_not_exist",
                    "loc": ["descendant_of"],
                    "msg": f"No {self.page_name} matches the given descendant_of value.",
                }
            ],
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
            status_code=422,
            detail_contains="Validation failed",
            errors=[
                {
                    "type": "does_not_exist",
                    "loc": ["translation_of"],
                    "msg": f"No {self.page_name} matches the given translation_of value.",
                }
            ],
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

    def test_site_filter_nonexistent_site_gives_error(self):
        response = self.get_response(site="not-a-site")
        self.assert_problem_response(
            response,
            status_code=404,
            detail_contains="No Site matches the given query.",
        )

    def test_site_filter_same_hostname_returns_error(self):
        response = self.get_response(site="localhost")
        self.assert_problem_response(
            response,
            status_code=400,
            detail_contains="Your query returned multiple sites. Try adding a port number to your site filter.",
        )

    def test_site_filter(self):
        response = self.get_response(site="localhost:8001")
        content = response.json()

        page_id_list = self.get_page_id_list(content)

        self.assertEqual(page_id_list, [24, 25])


class TestV3PageListingOrdering(TestV3PageListingBase, TestCase):
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
                    "msg": f"Value error, invalid fields for model {self.page_name}: ['-random'].",
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
                    "msg": f"Value error, invalid fields for model {self.page_name}: ['not_a_field'].",
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


class TestV3PageListingFieldFilter(TestV3PageListingBase, TestCase):
    def test_filtering_exact_filter(self):
        response = self.get_response(title="Home page")
        content = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.get_page_id_list(content), [2])

    def test_filtering_exact_filter_on_specific_field(self):
        response = self.get_response(type="demosite.BlogEntryPage", date="2013-12-02")
        content = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.get_page_id_list(content), [16])

    def test_filtering_on_id(self):
        response = self.get_response(id=16)
        content = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.get_page_id_list(content), [16])

    def test_filtering_on_foreign_key(self):
        response = self.get_response(type="demosite.ContactPage", feed_image=7)
        content = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.get_page_id_list(content), [12])

    @unittest.skipIf(
        swapper.is_swapped("wagtailcore", "Page"),
        "show_in_menus field is not available on custom base page models",
    )
    def test_filtering_on_boolean(self):
        response = self.get_response(show_in_menus="false")
        content = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.get_page_id_list(content), [8, 9, 16, 17, 18, 19])

    def test_filtering_doesnt_work_on_specific_fields_without_type(self):
        # Unlike v2, filtering by a field not recognised for the current
        # queryset's model is silently ignored rather than an error.
        response = self.get_response(date="2013-12-02")
        content = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(content["count"], get_total_page_count())

    def test_filtering_tags(self):
        response = self.get_response(type="demosite.BlogEntryPage", tags="wagtail")
        content = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(self.get_page_id_list(content)), {16, 18})

    def test_filtering_multiple_tags(self):
        response = self.get_response(
            type="demosite.BlogEntryPage", tags=["wagtail", "bird"]
        )
        content = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(self.get_page_id_list(content)), {16})

    def test_filtering_unknown_field_gives_error(self):
        # Unlike v2, an unrecognised query parameter is silently ignored
        # rather than an error.
        response = self.get_response(not_a_field="abc")
        content = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(content["count"], get_total_page_count())

    def test_filtering_id_int_validation(self):
        response = self.get_response(id="abc")
        self.assert_problem_response(
            response,
            status_code=422,
            detail_contains="Validation failed",
            errors=[
                {
                    "type": "value_error",
                    "loc": ["id"],
                    "msg": (
                        "Field filter error, 'abc' is not a valid value for id. "
                        "(Field 'id' expected a number but got 'abc'.)"
                    ),
                }
            ],
        )

    def test_filtering_foreign_key_int_validation(self):
        response = self.get_response(type="demosite.ContactPage", feed_image="abc")
        self.assert_problem_response(
            response,
            status_code=422,
            detail_contains="Validation failed",
            errors=[
                {
                    "type": "value_error",
                    "loc": ["feed_image"],
                    "msg": (
                        "Field filter error, 'abc' is not a valid value for feed_image. "
                        "(Field 'id' expected a number but got 'abc'.)"
                    ),
                }
            ],
        )

    @unittest.skipIf(
        swapper.is_swapped("wagtailcore", "Page"),
        "show_in_menus field is not available on custom base page models",
    )
    def test_filtering_boolean_validation(self):
        response = self.get_response(show_in_menus="abc")
        content = self.assert_problem_response(
            response,
            status_code=422,
            detail_contains="Validation failed",
            errors=[
                {
                    "type": "validation_error",
                    "loc": ["show_in_menus"],
                }
            ],
        )
        self.assertIn(
            "Field filter error, 'abc' is not a valid value for show_in_menus.",
            content["errors"][0]["msg"],
        )

    def test_slug_field_containing_null_bytes_gives_error(self):
        response = self.get_response(slug="\0")
        self.assert_problem_response(
            response,
            status_code=422,
            detail_contains="Validation failed",
            errors=[
                {
                    "type": "value_error",
                    "loc": ["slug"],
                    "msg": (
                        "Field filter error, '\x00' is not a valid value for "
                        "slug. (null characters are not allowed)"
                    ),
                }
            ],
        )


@tag("transaction")
class TestV3PageListingSearch(TestV3PageListingBase, TransactionTestCase):
    def setUp(self):
        super().setUp()
        management.call_command(
            "update_index",
            backend_name="default",
            stdout=StringIO(),
            chunk_size=50,
        )

    def get_homepage(self):
        return Page.objects.get(slug="home-page")

    @override_settings(WAGTAIL_I18N_ENABLED=True)
    def test_locale_filter_with_search(self):
        french = Locale.objects.create(language_code="fr")
        homepage = self.get_homepage()
        french_homepage = homepage.copy_for_translation(french)
        french_homepage.get_latest_revision().publish()
        events_index = Page.objects.get(url_path="/home-page/events-index/")
        french_events_index = events_index.copy_for_translation(french)
        french_events_index.get_latest_revision().publish()

        response = self.get_response(locale="fr", search="events")
        content = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.get_page_id_list(content), [french_events_index.id])

    @override_settings(WAGTAIL_I18N_ENABLED=True)
    def test_translation_of_filter_with_search(self):
        french = Locale.objects.create(language_code="fr")
        homepage = self.get_homepage()
        french_homepage = homepage.copy_for_translation(french)
        french_homepage.get_latest_revision().publish()

        response = self.get_response(translation_of=homepage.id, search="home")
        content = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.get_page_id_list(content), [french_homepage.id])

        response = self.get_response(translation_of=homepage.id, search="gnome")
        content = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.get_page_id_list(content), [])

    def test_search_for_blog(self):
        response = self.get_response(search="blog")
        content = response.json()

        self.assertEqual(response.status_code, 200)
        # Check that the items are the blog index and three blog pages
        self.assertEqual(set(self.get_page_id_list(content)), {5, 16, 18, 19})

    def test_search_with_type(self):
        response = self.get_response(type="demosite.BlogEntryPage", search="blog")
        content = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(self.get_page_id_list(content)), {16, 18, 19})

    def test_search_with_order(self):
        response = self.get_response(search="blog", order="title")
        content = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.get_page_id_list(content), [19, 5, 16, 18])

    def test_search_with_order_on_non_indexed_field_gives_error(self):
        response = self.get_response(
            type="demosite.BlogEntryPage", search="blog", order="body"
        )
        self.assert_problem_response(
            response,
            status_code=422,
            detail_contains="Validation failed",
            errors=[
                {
                    "type": "order_by_field_error",
                    "msg": "Cannot order by 'body' while searching "
                    "(field is not indexed).",
                }
            ],
        )

    @override_settings(WAGTAILAPI_SEARCH_ENABLED=False)
    def test_search_when_disabled_gives_error(self):
        response = self.get_response(search="blog")
        self.assert_problem_response(
            response,
            status_code=422,
            detail_contains="Validation failed",
            errors=[
                {
                    "type": "assertion_error",
                    "msg": "Assertion failed, search is disabled.",
                }
            ],
        )

    def test_search_operator_and(self):
        response = self.get_response(
            type="demosite.BlogEntryPage",
            search="blog elephants",
            search_operator="and",
        )
        content = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(self.get_page_id_list(content)), {18})

    def test_search_operator_or(self):
        response = self.get_response(
            type="demosite.BlogEntryPage",
            search="blog elephants",
            search_operator="or",
        )
        content = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(self.get_page_id_list(content)), {16, 18, 19})

    def test_empty_searches_work(self):
        response = self.get_response(search="")
        content = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(self.get_page_id_list(content)), set())
        self.assertEqual(content["count"], 0)

    def test_search_with_invalid_type(self):
        response = self.get_response(type="demosite.InvalidPageType", search="blog")
        self.assert_problem_response(
            response,
            status_code=422,
            detail_contains="Validation failed",
            errors=[{"type": "literal_error", "loc": ["query", "filters", "type", 0]}],
        )

    def test_search_with_filter(self):
        response = self.get_response(
            title="Another blog post",
            search="blog",
            order="title",
        )
        content = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.get_page_id_list(content), [19])

    def test_search_with_filter_on_non_filterable_field(self):
        response = self.get_response(
            type="demosite.BlogEntryPage",
            body="foo",
            search="blog",
            order="title",
        )
        self.assert_problem_response(
            response,
            status_code=422,
            detail_contains="Validation failed",
            errors=[
                {
                    "type": "filter_field_error",
                    "loc": ["body"],
                    "msg": (
                        "Cannot filter by 'body' while searching "
                        "(field is not indexed)."
                    ),
                }
            ],
        )

    def test_search_when_filtering_by_tag_gives_error(self):
        response = self.get_response(
            type="demosite.BlogEntryPage",
            search="blog",
            tags="wagtail",
        )
        self.assert_problem_response(
            response,
            status_code=422,
            detail_contains="Validation failed",
            errors=[
                {
                    "type": "filter_field_error",
                    "loc": ["name"],
                    "msg": (
                        "Cannot filter by 'name' while searching "
                        "(field is not indexed)."
                    ),
                }
            ],
        )


class TestV3PageDetail(PageFixturesMixin, TestV3Base, WagtailTestUtils, TestCase):
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
        blog_index = models.BlogIndexPage.objects.first()
        response = self.client.get(
            reverse("wagtailapi_v3:detail_page", kwargs={"page_id": blog_index.id})
        )
        content = response.json()

        extra_meta = set()
        if not swapper.is_swapped("wagtailcore", "Page"):
            extra_meta = {"show_in_menus", "seo_title", "search_description"}

        self.assertEqual(
            set(content["meta"].keys()),
            {
                "type",
                "detail_url",
                "html_url",
                "slug",
                "first_published_at",
                "locale",
                "parent",
                "alias_of",
            }
            | extra_meta,
        )
        self.assertEqual(content["meta"]["slug"], blog_index.slug)
        self.assertEqual(content["meta"]["type"], "demosite.BlogIndexPage")
        self.assertTrue(
            content["meta"]["detail_url"].startswith("https://api.example.com")
        )
        self.assertIn(f"/api/v3/pages/{blog_index.id}/", content["meta"]["detail_url"])
        self.assertIsNotNone(content["meta"]["html_url"])
        parent = blog_index.get_parent()
        self.assertEqual(
            content["meta"]["parent"],
            {
                "id": parent.id,
                "meta": {
                    "type": parent.specific_class._meta.label,
                    "detail_url": (
                        f"https://api.example.com/api/v3/pages/{parent.id}/"
                    ),
                    "html_url": "http://localhost/",
                },
                "title": parent.title,
            },
        )

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

    def test_draft_page_only_accessible_by_authenticated_user(self):
        page = models.BlogEntryPage.objects.get(id=16)
        page.unpublish()
        url = reverse("wagtailapi_v3:detail_page", kwargs={"page_id": page.id})

        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        self.login()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], page.id)

    def test_version_draft_returns_latest_revision_content_when_logged_in(self):
        page = models.BlogEntryPage.objects.get(id=16)
        user = self.login()
        page.title = "Updated title"
        page.save_revision(user=user)
        url = reverse("wagtailapi_v3:detail_page", kwargs={"page_id": page.id})

        response = self.client.get(url, {"version": "draft"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["title"], "Updated title")

    def test_version_draft_falls_back_to_live_when_anonymous(self):
        page = models.BlogEntryPage.objects.get(id=16)
        original_title = page.title
        user = self.login()
        page.title = "Updated title"
        page.save_revision(user=user)
        self.unauthorize()
        url = reverse("wagtailapi_v3:detail_page", kwargs={"page_id": page.id})

        response = self.client.get(url, {"version": "draft"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["title"], original_title)

    def test_version_defaults_to_live(self):
        page = models.BlogEntryPage.objects.get(id=16)
        original_title = page.title
        user = self.login()
        page.title = "Updated title"
        page.save_revision(user=user)
        url = reverse("wagtailapi_v3:detail_page", kwargs={"page_id": page.id})

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["title"], original_title)

    def test_version_invalid_value_gives_error(self):
        page = models.BlogEntryPage.objects.get(id=16)
        self.login()
        url = reverse("wagtailapi_v3:detail_page", kwargs={"page_id": page.id})

        response = self.client.get(url, {"version": "published"})
        self.assert_problem_response(
            response,
            status_code=422,
            detail_contains="Validation failed",
            errors=[
                {
                    "type": "literal_error",
                    "loc": ["query", "version"],
                    "msg": "Input should be 'live' or 'draft'",
                }
            ],
        )


class TestV3PageFind(PageFixturesMixin, TestV3Base, WagtailTestUtils, TestCase):
    fixtures = ["demosite.json"]
    page_name = Page._meta.object_name

    def get_response(self, **params):
        return self.client.get(reverse("wagtailapi_v3:find_page"), params)

    def test_without_parameters(self):
        response = self.get_response()
        self.assert_problem_response(
            response,
            status_code=404,
            detail_contains=f"No {self.page_name} matches the given query.",
        )

    def test_find_by_id(self):
        response = self.get_response(id=5)
        self.assertRedirects(
            response,
            reverse("wagtailapi_v3:detail_page", kwargs={"page_id": 5}),
            fetch_redirect_response=False,
        )

    def test_find_by_id_nonexistent(self):
        response = self.get_response(id=1234)
        self.assert_problem_response(
            response,
            status_code=404,
            detail_contains=f"No {self.page_name} matches the given query.",
        )

    def test_find_by_html_path(self):
        response = self.get_response(html_path="/events-index/event-1/")
        self.assertRedirects(
            response,
            reverse("wagtailapi_v3:detail_page", kwargs={"page_id": 8}),
            fetch_redirect_response=False,
        )

    def test_find_by_html_path_with_start_and_end_slashes_removed(self):
        response = self.get_response(html_path="events-index/event-1")
        self.assertRedirects(
            response,
            reverse("wagtailapi_v3:detail_page", kwargs={"page_id": 8}),
            fetch_redirect_response=False,
        )

    def test_find_by_html_path_nonexistent(self):
        response = self.get_response(html_path="/foo")
        self.assert_problem_response(
            response,
            status_code=404,
            detail_contains=f"No {self.page_name} matches the given query.",
        )

    def test_find_by_html_path_takes_precedence_over_id(self):
        response = self.get_response(id=1234, html_path="/events-index/event-1/")
        self.assertRedirects(
            response,
            reverse("wagtailapi_v3:detail_page", kwargs={"page_id": 8}),
            fetch_redirect_response=False,
        )

    def test_find_draft_page_by_id_requires_authentication(self):
        page = Page.objects.get(id=8)
        page.unpublish()

        response = self.get_response(id=8)
        self.assert_problem_response(
            response,
            status_code=404,
            detail_contains=f"No {self.page_name} matches the given query.",
        )

        self.login()
        response = self.get_response(id=8)
        self.assertRedirects(
            response,
            reverse("wagtailapi_v3:detail_page", kwargs={"page_id": 8}),
            fetch_redirect_response=False,
        )

    def test_find_draft_page_by_html_path_not_found_even_when_logged_in(self):
        # Routing by html_path only resolves live pages, regardless of the
        # authorization.
        page = Page.objects.get(id=8)
        page.unpublish()

        self.login()
        response = self.get_response(html_path="/events-index/event-1/")
        self.assert_problem_response(
            response,
            status_code=404,
            detail_contains=f"No {self.page_name} matches the given query.",
        )

    def test_find_by_id_with_page_in_default_site(self):
        # id=8 belongs to the default site's tree.
        # Without ?site=, it is found.
        response = self.get_response(id=8)
        self.assertRedirects(
            response,
            reverse("wagtailapi_v3:detail_page", kwargs={"page_id": 8}),
            fetch_redirect_response=False,
        )
        # With site= for the default site, it is found.
        response = self.get_response(id=8, site="localhost:80")
        self.assertRedirects(
            response,
            reverse("wagtailapi_v3:detail_page", kwargs={"page_id": 8})
            + "?site=localhost%3A80",
            fetch_redirect_response=False,
        )
        # With ?site= for a different site, it is not found.
        response = self.get_response(id=8, site="localhost:8001")
        self.assert_problem_response(
            response,
            status_code=404,
            detail_contains=f"No {self.page_name} matches the given query.",
        )

    def test_find_by_id_with_page_in_non_default_site(self):
        # id=24 is in a different (non-default) site tree.
        # Without ?site=, we look for it based on the request's site, 404.
        response = self.get_response(id=24)
        self.assert_problem_response(
            response,
            status_code=404,
            detail_contains=f"No {self.page_name} matches the given query.",
        )
        # With the correct ?site=, it is found.
        response = self.get_response(id=24, site="localhost:8001")
        self.assertRedirects(
            response,
            reverse("wagtailapi_v3:detail_page", kwargs={"page_id": 24})
            + "?site=localhost%3A8001",
            fetch_redirect_response=False,
        )

    def test_find_by_html_path_with_page_in_default_site(self):
        # /events-index/event-1/ belongs to the default site's tree.
        # Without ?site=, it is found.
        response = self.get_response(html_path="/events-index/event-1/")
        self.assertRedirects(
            response,
            reverse("wagtailapi_v3:detail_page", kwargs={"page_id": 8}),
            fetch_redirect_response=False,
        )
        # With site= for the default site, it is found.
        response = self.get_response(
            html_path="/events-index/event-1/",
            site="localhost:80",
        )
        self.assertRedirects(
            response,
            reverse("wagtailapi_v3:detail_page", kwargs={"page_id": 8})
            + "?site=localhost%3A80",
            fetch_redirect_response=False,
        )
        # With ?site= for a different site, it is not found.
        response = self.get_response(
            html_path="/events-index/event-1/",
            site="localhost:8001",
        )
        self.assert_problem_response(
            response,
            status_code=404,
            detail_contains=f"No {self.page_name} matches the given query.",
        )

    def test_find_by_html_path_matching_only_in_site_param_tree(self):
        # A fresh site+page whose html_path only exists in the new tree,
        # not in the tree of the site the request actually arrives on.
        root = Page.objects.get(pk=1)
        new_site_root = models.HomePage(title="New site root", slug="new-site-root")
        root.add_child(instance=new_site_root)
        new_site = Site.objects.create(
            hostname="othersite.new",
            port=80,
            root_page=new_site_root,
        )
        page_in_new_site = models.StandardIndexPage(
            title="Only on new site",
            slug="only-on-new-site",
            live=True,
        )
        new_site_root.add_child(instance=page_in_new_site)

        # Without ?site=, the page is not found.
        response = self.get_response(html_path="/only-on-new-site/")
        self.assert_problem_response(
            response,
            status_code=404,
            detail_contains=f"No {self.page_name} matches the given query.",
        )

        # With ?site= for the new site, the page is found.
        response = self.get_response(
            html_path="/only-on-new-site/",
            site=new_site.hostname,
        )
        self.assertRedirects(
            response,
            reverse(
                "wagtailapi_v3:detail_page",
                kwargs={"page_id": page_in_new_site.pk},
            )
            + "?site=othersite.new",
            fetch_redirect_response=False,
        )

    def test_find_by_html_with_no_sites(self):
        Site.objects.all().delete()
        response = self.get_response(html_path="/events-index/event-1/")
        self.assert_problem_response(
            response,
            status_code=404,
            detail_contains=f"No {self.page_name} matches the given query.",
        )
