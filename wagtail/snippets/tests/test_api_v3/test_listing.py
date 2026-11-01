from django.contrib.auth.models import Permission
from django.core.management import call_command
from django.test import TestCase, TransactionTestCase, override_settings, tag
from django.urls import reverse

from wagtail.api.v3.tests.base import TestV3Base
from wagtail.models import Locale
from wagtail.test.testapp.models import (
    QUOTABLE_PK,
    Advert,
    AdvertWithCustomPrimaryKey,
    FullFeaturedSnippet,
    UUIDSnippetWithRelations,
)
from wagtail.test.utils import Page, WagtailTestUtils


class TestV3SnippetListingBase(TestV3Base, WagtailTestUtils):
    model = Advert

    def setUp(self):
        super().setUp()
        self.user = self.login()

    def get_response(self, **params):
        return self.client.get(
            reverse(
                "wagtailapi_v3:list_snippets",
                kwargs={"type": self.model._meta.label},
            ),
            params,
        )


class TestV3SnippetListing(TestV3SnippetListingBase, TestCase):
    def setUp(self):
        super().setUp()
        Advert.objects.create(text="Advert 1")
        Advert.objects.create(text="Advert 2")

    def test_anonymous_returns_401(self):
        self.unauthorize()
        response = self.get_response()
        self.assert_problem_response(
            response,
            status_code=401,
            detail_contains="Unauthorized",
        )

    def test_authenticated_returns_200(self):
        response = self.get_response()
        self.assertEqual(response.status_code, 200)

    def test_response_fields(self):
        content = self.get_response().json()
        self.assertIn("count", content)
        self.assertIn("items", content)
        for item in content["items"]:
            self.assertEqual(set(item.keys()), {"id", "url", "text", "tags", "meta"})

    def test_count_matches_database(self):
        content = self.get_response().json()
        self.assertEqual(content["count"], Advert.objects.count())

    def test_detail_url_resolves_for_quotable_pk(self):
        AdvertWithCustomPrimaryKey.objects.create(
            advert_id=QUOTABLE_PK, text="Advert 1"
        )
        response = self.client.get(
            reverse(
                "wagtailapi_v3:list_snippets",
                kwargs={"type": "tests.AdvertWithCustomPrimaryKey"},
            )
        )
        self.assertEqual(response.status_code, 200)
        detail_url = response.json()["items"][0]["meta"]["detail_url"]
        self.assertIsNotNone(detail_url)
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["advert_id"], QUOTABLE_PK)

    def test_user_with_any_permission_can_list(self):
        user = self.create_user(username="viewer", password="password")
        user.user_permissions.add(Permission.objects.get(codename="view_advert"))
        self.login(username="viewer", password="password")
        response = self.get_response()
        self.assertEqual(response.status_code, 200)

    def test_user_without_any_permission_gets_403(self):
        self.create_user(username="noperms", password="password")
        self.login(username="noperms", password="password")
        response = self.get_response()
        self.assert_problem_response(
            response,
            status_code=403,
            detail_contains="Permission denied",
        )

    def test_unknown_type_returns_422(self):
        response = self.client.get(
            reverse("wagtailapi_v3:list_snippets", kwargs={"type": "tests.NotASnippet"})
        )
        self.assert_problem_response(
            response,
            status_code=422,
            detail_contains="Validation failed",
            errors=[{"type": "literal_error", "loc": ["path", "type"]}],
        )


class TestV3SnippetListingPagination(TestV3SnippetListingBase, TestCase):
    def setUp(self):
        super().setUp()
        self.adverts = [Advert.objects.create(text=f"Advert {i}") for i in range(25)]

    def get_id_list(self, content):
        return [item["id"] for item in content["items"]]

    def test_default_limit_is_20(self):
        content = self.get_response().json()
        self.assertEqual(len(content["items"]), 20)
        self.assertEqual(content["count"], 25)

    def test_offset_and_limit_return_expected_slice(self):
        all_ids = [advert.pk for advert in self.adverts]
        content = self.get_response(offset=3, limit=2).json()
        self.assertEqual(self.get_id_list(content), all_ids[3:5])

    def test_offset_beyond_count_returns_empty_items(self):
        content = self.get_response(offset=100).json()
        self.assertEqual(content["count"], 25)
        self.assertEqual(content["items"], [])

    @override_settings(WAGTAILAPI_LIMIT_MAX=5)
    def test_limit_max_enforced(self):
        response = self.get_response(limit=10)
        self.assert_problem_response(response, status_code=400)

    @override_settings(WAGTAILAPI_LIMIT_MAX=5)
    def test_limit_within_max(self):
        content = self.get_response(limit=5).json()
        self.assertLessEqual(len(content["items"]), 5)


class TestV3SnippetListingFieldFilter(TestV3SnippetListingBase, TestCase):
    def setUp(self):
        super().setUp()
        self.zebra = Advert.objects.create(text="Zebra", url="https://a.example.com")
        self.apple = Advert.objects.create(text="Apple", url="https://b.example.com")
        self.mango = Advert.objects.create(text="Mango", url="https://a.example.com")

    def get_id_list(self, content):
        return [item["id"] for item in content["items"]]

    def test_filtering_exact_filter(self):
        content = self.get_response(text="Apple").json()
        self.assertEqual(self.get_id_list(content), [self.apple.pk])

    def test_filtering_on_pk(self):
        content = self.get_response(id=self.apple.pk).json()
        self.assertEqual(self.get_id_list(content), [self.apple.pk])

    def test_filtering_multiple_fields(self):
        content = self.get_response(url="https://a.example.com").json()
        self.assertEqual(set(self.get_id_list(content)), {self.zebra.pk, self.mango.pk})

    def test_filtering_unknown_field_ignored(self):
        # Unlike v2, an unrecognised query parameter is silently ignored
        # rather than an error.
        content = self.get_response(not_a_field="abc").json()
        self.assertEqual(content["count"], 3)

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

    def test_text_field_containing_null_bytes_gives_error(self):
        response = self.get_response(text="\0")
        self.assert_problem_response(
            response,
            status_code=422,
            detail_contains="Validation failed",
            errors=[
                {
                    "type": "value_error",
                    "loc": ["text"],
                    "msg": (
                        "Field filter error, '\x00' is not a valid value for "
                        "text. (null characters are not allowed)"
                    ),
                }
            ],
        )


class TestV3SnippetListingOrdering(TestV3SnippetListingBase, TestCase):
    def setUp(self):
        super().setUp()
        self.zebra = Advert.objects.create(text="Zebra")
        self.apple = Advert.objects.create(text="Apple")
        self.mango = Advert.objects.create(text="Mango")

    def get_id_list(self, content):
        return [item["id"] for item in content["items"]]

    def test_ordering_by_field(self):
        content = self.get_response(order="text").json()
        self.assertEqual(
            self.get_id_list(content),
            [self.apple.pk, self.mango.pk, self.zebra.pk],
        )

    def test_ordering_by_field_backwards(self):
        content = self.get_response(order="-text").json()
        self.assertEqual(
            self.get_id_list(content),
            [self.zebra.pk, self.mango.pk, self.apple.pk],
        )

    def test_ordering_by_unknown_field_gives_error(self):
        response = self.get_response(order="not_a_field")
        self.assert_problem_response(
            response,
            status_code=422,
            detail_contains="Validation failed",
            errors=[
                {
                    "type": "value_error",
                    "msg": "Value error, invalid fields for model Advert: ['not_a_field'].",
                }
            ],
        )

    def test_ordering_by_random(self):
        content_1 = self.get_response(order="random").json()
        content_2 = self.get_response(order="random").json()
        # Not a reliable assertion on its own, but combined with the fixed
        # seed data this at least exercises the "random" branch without error.
        self.assertEqual(content_1["count"], content_2["count"])

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

    def test_ordering_by_random_with_offset_gives_error(self):
        response = self.get_response(order="random", offset=1)
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


class TestV3SnippetListingTranslationFilter(TestV3SnippetListingBase, TestCase):
    model = FullFeaturedSnippet

    def setUp(self):
        super().setUp()
        self.en = Locale.objects.get_or_create(language_code="en")[0]
        self.fr = Locale.objects.get_or_create(language_code="fr")[0]

    def get_id_list(self, content):
        return [item["id"] for item in content["items"]]

    def test_locale_filter(self):
        english = FullFeaturedSnippet.objects.create(text="English", locale=self.en)
        french = FullFeaturedSnippet.objects.create(text="French", locale=self.fr)
        content = self.get_response(locale="fr").json()
        self.assertEqual(self.get_id_list(content), [french.pk])
        self.assertNotIn(english.pk, self.get_id_list(content))

    def test_locale_omitted_returns_all(self):
        FullFeaturedSnippet.objects.create(text="English", locale=self.en)
        FullFeaturedSnippet.objects.create(text="French", locale=self.fr)
        content = self.get_response().json()
        self.assertEqual(content["count"], 2)

    def test_unknown_locale_returns_404(self):
        FullFeaturedSnippet.objects.create(text="English", locale=self.en)
        response = self.get_response(locale="de")
        self.assert_problem_response(response, status_code=404)

    def test_locale_on_non_translatable_type_gives_error(self):
        Advert.objects.create(text="Hi")
        response = self.client.get(
            reverse("wagtailapi_v3:list_snippets", kwargs={"type": "tests.Advert"}),
            {"locale": "fr"},
        )
        self.assert_problem_response(
            response,
            status_code=422,
            detail_contains="Validation failed",
            errors=[
                {
                    "type": "assertion_error",
                    "loc": ["locale"],
                    "msg": "Advert is not translatable.",
                }
            ],
        )

    def test_translation_of_filter(self):
        english = FullFeaturedSnippet.objects.create(text="English", locale=self.en)
        french = FullFeaturedSnippet.objects.create(
            text="French",
            locale=self.fr,
            translation_key=english.translation_key,
        )
        content = self.get_response(translation_of=english.pk).json()
        self.assertEqual(self.get_id_list(content), [french.pk])
        self.assertNotIn(english.pk, self.get_id_list(content))

    def test_translation_of_unknown_snippet_gives_422(self):
        response = self.get_response(translation_of=100000)
        self.assert_problem_response(
            response,
            status_code=422,
            detail_contains="Validation failed",
            errors=[
                {
                    "type": "does_not_exist",
                    "loc": ["translation_of"],
                    "msg": "No FullFeaturedSnippet matches the given "
                    "translation_of value.",
                }
            ],
        )

    def test_translation_of_on_non_translatable_type_gives_error(self):
        advert = Advert.objects.create(text="Hi")
        response = self.client.get(
            reverse("wagtailapi_v3:list_snippets", kwargs={"type": "tests.Advert"}),
            {"translation_of": advert.pk},
        )
        self.assert_problem_response(
            response,
            status_code=422,
            detail_contains="Validation failed",
            errors=[
                {
                    "type": "assertion_error",
                    "loc": ["translation_of"],
                    "msg": "Advert is not translatable.",
                }
            ],
        )


@tag("transaction")
class TestV3SnippetListingSearch(TestV3SnippetListingBase, TransactionTestCase):
    model = FullFeaturedSnippet

    def setUp(self):
        super().setUp()
        Locale.objects.get_or_create(language_code="en")
        self.apple = FullFeaturedSnippet.objects.create(text="Apple pie", some_number=1)
        self.apple_tart = FullFeaturedSnippet.objects.create(
            text="Apple tart", some_number=2
        )
        self.zebra = FullFeaturedSnippet.objects.create(
            text="Zebra crossing", some_number=3
        )
        call_command("update_index", backend_name="default", verbosity=0, chunk_size=50)

    def get_id_list(self, content):
        return [item["id"] for item in content["items"]]

    def test_search_for_text(self):
        content = self.get_response(search="Apple").json()
        self.assertEqual(
            set(self.get_id_list(content)), {self.apple.pk, self.apple_tart.pk}
        )

    def test_empty_search_returns_no_results(self):
        content = self.get_response(search="").json()
        self.assertEqual(content["items"], [])
        self.assertEqual(content["count"], 0)

    def test_search_on_non_indexed_model_gives_error(self):
        Advert.objects.create(text="Apple")
        response = self.client.get(
            reverse("wagtailapi_v3:list_snippets", kwargs={"type": "tests.Advert"}),
            {"search": "Apple"},
        )
        self.assert_problem_response(
            response,
            status_code=422,
            detail_contains="Validation failed",
            errors=[
                {
                    "type": "assertion_error",
                    "msg": "Advert is not indexed for search.",
                }
            ],
        )

    @override_settings(WAGTAILAPI_SEARCH_ENABLED=False)
    def test_search_when_disabled_gives_error(self):
        response = self.get_response(search="Apple")
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
        content = self.get_response(search="Apple pie", search_operator="and").json()
        self.assertEqual(self.get_id_list(content), [self.apple.pk])

    def test_search_operator_or(self):
        content = self.get_response(search="Apple pie", search_operator="or").json()
        self.assertEqual(
            set(self.get_id_list(content)), {self.apple.pk, self.apple_tart.pk}
        )

    def test_search_with_order(self):
        content = self.get_response(search="Apple", order="text").json()
        self.assertEqual(self.get_id_list(content), [self.apple.pk, self.apple_tart.pk])

    def test_search_with_order_on_non_indexed_field_gives_error(self):
        response = self.get_response(search="Apple", order="some_number")
        self.assert_problem_response(
            response,
            status_code=422,
            detail_contains="Validation failed",
            errors=[
                {
                    "type": "order_by_field_error",
                    "loc": ["some_number"],
                    "msg": "Cannot order by 'some_number' while searching "
                    "(field is not indexed).",
                }
            ],
        )

    def test_search_with_filter(self):
        content = self.get_response(search="Apple", text="Apple pie").json()
        self.assertEqual(self.get_id_list(content), [self.apple.pk])

    def test_search_with_filter_on_non_indexed_field_gives_error(self):
        response = self.get_response(search="Apple", some_number=1)
        self.assert_problem_response(
            response,
            status_code=422,
            detail_contains="Validation failed",
            errors=[
                {
                    "type": "filter_field_error",
                    "loc": ["some_number"],
                    "msg": "Cannot filter by 'some_number' while searching "
                    "(field is not indexed).",
                }
            ],
        )

    def test_locale_filter_with_search(self):
        french = Locale.objects.create(language_code="fr")
        french_apple = FullFeaturedSnippet.objects.create(
            text="Apple baguette", locale=french
        )
        call_command("update_index", backend_name="default", verbosity=0)

        content = self.get_response(locale="fr", search="Apple").json()

        self.assertEqual(self.get_id_list(content), [french_apple.pk])

    def test_translation_of_filter_with_search(self):
        french = Locale.objects.create(language_code="fr")
        french_apple = FullFeaturedSnippet.objects.create(
            text="Apple baguette",
            locale=french,
            translation_key=self.apple.translation_key,
        )
        call_command("update_index", backend_name="default", verbosity=0)

        content = self.get_response(
            translation_of=self.apple.pk, search="baguette"
        ).json()
        self.assertEqual(self.get_id_list(content), [french_apple.pk])

        content = self.get_response(translation_of=self.apple.pk, search="zebra").json()
        self.assertEqual(self.get_id_list(content), [])


class TestV3SnippetListingWithRichText(TestV3SnippetListingBase, TestCase):
    # Unlike the pages listing, the snippets listing serialises the full
    # detail schema (including api_fields), so rich_text_format applies
    # here as well as on the detail endpoint.
    model = UUIDSnippetWithRelations

    @classmethod
    def setUpTestData(cls):
        cls.home_page = Page.objects.get(depth=2)
        cls.snippet = cls.model.objects.create(
            text="Hello",
            rich_body=f'<p><a linktype="page" id="{cls.home_page.pk}">home</a></p>',
        )

    def test_listing_applies_rich_text_format(self):
        response = self.get_response(rich_text_format="html")
        self.assertEqual(response.status_code, 200)
        body = response.json()["items"][0]["rich_body"]
        self.assertIn("<a href=", body)
        self.assertNotIn("linktype", body)

    def test_listing_invalid_rich_text_format_is_422(self):
        response = self.get_response(rich_text_format="nope")
        self.assert_problem_response(
            response,
            status_code=422,
            detail_contains="Validation failed",
            errors=[
                {
                    "type": "literal_error",
                    "loc": ["query", "rich_text_format"],
                    "msg": "Input should be 'db_html', 'html', 'db_markdown' or 'markdown'",
                }
            ],
        )
