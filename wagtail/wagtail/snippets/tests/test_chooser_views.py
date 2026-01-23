import json

from django.contrib.admin.utils import quote
from django.test import TestCase, TransactionTestCase
from django.test.utils import override_settings
from django.urls import reverse

from wagtail.models import Locale
from wagtail.test.snippets.models import (
    NonAutocompleteSearchableSnippet,
    SearchableSnippet,
    TranslatableSnippet,
)
from wagtail.test.testapp.models import (
    Advert,
    AdvertWithCustomPrimaryKey,
    AdvertWithCustomUUIDPrimaryKey,
    DraftStateModel,
)
from wagtail.test.utils import WagtailTestUtils


class TestSnippetChoose(WagtailTestUtils, TestCase):
    fixtures = ["test.json"]

    def setUp(self):
        self.login()
        self.url_args = ["tests", "advert"]

    def get(self, params=None):
        app_label, model_name = self.url_args
        return self.client.get(
            reverse(f"wagtailsnippetchoosers_{app_label}_{model_name}:choose"),
            params or {},
        )

    def test_simple(self):
        response = self.get()
        self.assertTemplateUsed(response, "wagtailadmin/generic/chooser/chooser.html")

        # Check locale filter doesn't exist normally
        self.assertNotIn(
            '<select data-chooser-modal-search-filter name="lang">',
            response.json()["html"],
        )

    def test_no_results(self):
        Advert.objects.all().delete()
        response = self.get()
        self.assertTemplateUsed(response, "wagtailadmin/generic/chooser/chooser.html")
        response_html = response.json()["html"]
        self.assertIn('href="/admin/snippets/tests/advert/add/"', response_html)

    def test_ordering(self):
        """
        Listing should be ordered by PK if no ordering has been set on the model
        """
        Advert.objects.all().delete()
        for i in range(10, 0, -1):
            Advert.objects.create(pk=i, text="advert %d" % i)
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["results"][0].text, "advert 1")

    def test_simple_pagination(self):
        # page numbers in range should be accepted
        response = self.get({"p": 1})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/generic/chooser/chooser.html")
        # page numbers out of range should return 404
        response = self.get({"p": 9999})
        self.assertEqual(response.status_code, 404)

    def test_not_searchable(self):
        # filter_form should not have a search field
        self.assertFalse(self.get().context["filter_form"].fields.get("q"))

    @override_settings(WAGTAIL_I18N_ENABLED=False)
    def test_locale_filter_requires_i18n_enabled(self):
        self.url_args = ["snippetstests", "translatablesnippet"]
        fr_locale = Locale.objects.create(language_code="fr")

        TranslatableSnippet.objects.create(text="English snippet")
        TranslatableSnippet.objects.create(text="French snippet", locale=fr_locale)

        response = self.get()

        # Check the filter is omitted
        response_html = response.json()["html"]
        self.assertNotIn("data-chooser-modal-search-filter", response_html)
        self.assertNotIn('name="locale"', response_html)

    @override_settings(WAGTAIL_I18N_ENABLED=True)
    def test_filter_by_locale(self):
        self.url_args = ["snippetstests", "translatablesnippet"]
        fr_locale = Locale.objects.create(language_code="fr")

        TranslatableSnippet.objects.create(text="English snippet")
        TranslatableSnippet.objects.create(text="French snippet", locale=fr_locale)

        response = self.get()

        # Check the filter is added
        response_html = response.json()["html"]
        self.assertIn("data-chooser-modal-search-filter", response_html)
        self.assertIn('name="locale"', response_html)

        # Check both snippets are shown
        self.assertEqual(len(response.context["results"]), 2)
        self.assertEqual(response.context["results"][0].text, "English snippet")
        self.assertEqual(response.context["results"][1].text, "French snippet")

        # Now test with a locale selected
        response = self.get({"locale": "en"})

        self.assertEqual(len(response.context["results"]), 1)
        self.assertEqual(response.context["results"][0].text, "English snippet")


class TestSnippetChooseResults(WagtailTestUtils, TestCase):
    fixtures = ["test.json"]

    def setUp(self):
        self.login()

    def get(self, params=None):
        return self.client.get(
            reverse("wagtailsnippetchoosers_tests_advert:choose_results"), params or {}
        )

    def test_simple(self):
        response = self.get()
        self.assertTemplateUsed(response, "wagtailsnippets/chooser/results.html")

    def test_no_results(self):
        Advert.objects.all().delete()
        response = self.get()
        self.assertTemplateUsed(response, "wagtailsnippets/chooser/results.html")
        self.assertContains(
            response,
            'href="/admin/snippets/tests/advert/add/"',
        )


class TestSnippetChooseStatus(WagtailTestUtils, TestCase):
    def setUp(self):
        self.login()

    @classmethod
    def setUpTestData(cls):
        cls.draft = DraftStateModel.objects.create(text="foo", live=False)
        cls.live = DraftStateModel.objects.create(text="bar", live=True)
        cls.live_draft = DraftStateModel.objects.create(text="baz", live=True)
        cls.live_draft.save_revision()

    def get(self, view_name, params=None):
        return self.client.get(
            reverse(f"wagtailsnippetchoosers_tests_draftstatemodel:{view_name}"),
            params or {},
        )

    def test_choose_view_shows_status_column(self):
        response = self.get("choose")
        html = response.json()["html"]
        self.assertTagInHTML("<th>Status</th>", html)
        self.assertTagInHTML('<span class="w-status">draft</span>', html)
        self.assertTagInHTML(
            '<span class="w-status w-status--primary">live</span>', html
        )
        self.assertTagInHTML(
            '<span class="w-status w-status--primary">live + draft</span>', html
        )

    def test_choose_results_view_shows_status_column(self):
        response = self.get("choose_results")
        self.assertContains(response, "<th>Status</th>", html=True)
        self.assertContains(response, '<span class="w-status">draft</span>', html=True)
        self.assertContains(
            response, '<span class="w-status w-status--primary">live</span>', html=True
        )
        self.assertContains(
            response,
            '<span class="w-status w-status--primary">live + draft</span>',
            html=True,
        )


class TestSnippetChooseWithSearchableSnippet(WagtailTestUtils, TransactionTestCase):
    def setUp(self):
        self.login()

        # Create some instances of the searchable snippet for testing
        self.snippet_a = SearchableSnippet.objects.create(text="Hello")
        self.snippet_b = SearchableSnippet.objects.create(text="World")
        self.snippet_c = SearchableSnippet.objects.create(text="Hello World")

    def get(self, params=None):
        return self.client.get(
            reverse("wagtailsnippetchoosers_snippetstests_searchablesnippet:choose"),
            params or {},
        )

    def test_simple(self):
        response = self.get()
        self.assertTemplateUsed(response, "wagtailadmin/generic/chooser/chooser.html")

        # All snippets should be in items
        items = list(response.context["results"].object_list)
        self.assertIn(self.snippet_a, items)
        self.assertIn(self.snippet_b, items)
        self.assertIn(self.snippet_c, items)

    def test_is_searchable(self):
        # filter_form should have a search field
        self.assertTrue(self.get().context["filter_form"].fields.get("q"))

    def test_search_hello(self):
        response = self.get({"q": "Hello"})

        # Just snippets with "Hello" should be in items
        items = list(response.context["results"].object_list)
        self.assertIn(self.snippet_a, items)
        self.assertNotIn(self.snippet_b, items)
        self.assertIn(self.snippet_c, items)

    def test_search_world(self):
        response = self.get({"q": "World"})

        # Just snippets with "World" should be in items
        items = list(response.context["results"].object_list)
        self.assertNotIn(self.snippet_a, items)
        self.assertIn(self.snippet_b, items)
        self.assertIn(self.snippet_c, items)

    def test_partial_match(self):
        response = self.get({"q": "hello wo"})

        # should perform partial matching and return "Hello World"
        items = list(response.context["results"].object_list)
        self.assertNotIn(self.snippet_a, items)
        self.assertNotIn(self.snippet_b, items)
        self.assertIn(self.snippet_c, items)


class TestSnippetChooseWithNonAutocompleteSearchableSnippet(
    WagtailTestUtils, TransactionTestCase
):
    """
    Test that searchable snippets with no AutocompleteFields defined can still be searched using
    full words
    """

    def setUp(self):
        self.login()

        # Create some instances of the searchable snippet for testing
        self.snippet_a = NonAutocompleteSearchableSnippet.objects.create(text="Hello")
        self.snippet_b = NonAutocompleteSearchableSnippet.objects.create(text="World")
        self.snippet_c = NonAutocompleteSearchableSnippet.objects.create(
            text="Hello World"
        )

    def get(self, params=None):
        return self.client.get(
            reverse(
                "wagtailsnippetchoosers_snippetstests_nonautocompletesearchablesnippet:choose"
            ),
            params or {},
        )

    def test_search_hello(self):
        with self.assertWarnsRegex(
            RuntimeWarning, "does not specify any AutocompleteFields"
        ):
            response = self.get({"q": "Hello"})

        # Just snippets with "Hello" should be in items
        items = list(response.context["results"].object_list)
        self.assertIn(self.snippet_a, items)
        self.assertNotIn(self.snippet_b, items)
        self.assertIn(self.snippet_c, items)


class TestSnippetChosen(WagtailTestUtils, TestCase):
    fixtures = ["test.json"]

    def setUp(self):
        self.login()

    def get(self, pk, params=None):
        return self.client.get(
            reverse("wagtailsnippetchoosers_tests_advert:chosen", args=(pk,)),
            params or {},
        )

    def test_choose_a_page(self):
        response = self.get(pk=Advert.objects.all()[0].pk)
        response_json = json.loads(response.content.decode())
        self.assertEqual(response_json["step"], "chosen")

    def test_choose_a_non_existing_page(self):
        response = self.get(999999)
        self.assertEqual(response.status_code, 404)


class TestSnippetChooseWithCustomPrimaryKey(WagtailTestUtils, TestCase):
    fixtures = ["test.json"]

    def setUp(self):
        self.login()

    def get(self, params=None):
        return self.client.get(
            reverse("wagtailsnippetchoosers_tests_advertwithcustomprimarykey:choose"),
            params or {},
        )

    def test_simple(self):
        response = self.get()
        self.assertTemplateUsed(response, "wagtailadmin/generic/chooser/chooser.html")
        self.assertEqual(response.context["header_icon"], "snippet")
        self.assertEqual(response.context["icon"], "snippet")

    def test_ordering(self):
        """
        Listing should be ordered by PK if no ordering has been set on the model
        """
        AdvertWithCustomPrimaryKey.objects.all().delete()
        for i in range(10, 0, -1):
            AdvertWithCustomPrimaryKey.objects.create(pk=i, text="advert %d" % i)
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["results"][0].text, "advert 1")


class TestSnippetChosenWithCustomPrimaryKey(WagtailTestUtils, TestCase):
    fixtures = ["test.json"]

    def setUp(self):
        self.login()

    def get(self, pk, params=None):
        return self.client.get(
            reverse(
                "wagtailsnippetchoosers_tests_advertwithcustomprimarykey:chosen",
                args=(quote(pk),),
            ),
            params or {},
        )

    def test_choose_a_page(self):
        response = self.get(pk=AdvertWithCustomPrimaryKey.objects.all()[0].pk)
        response_json = json.loads(response.content.decode())
        self.assertEqual(response_json["step"], "chosen")


class TestSnippetChosenWithCustomUUIDPrimaryKey(WagtailTestUtils, TestCase):
    fixtures = ["test.json"]

    def setUp(self):
        self.login()

    def get(self, pk, params=None):
        return self.client.get(
            reverse(
                "wagtailsnippetchoosers_tests_advertwithcustomuuidprimarykey:chosen",
                args=(quote(pk),),
            ),
            params or {},
        )

    def test_choose_a_page(self):
        response = self.get(pk=AdvertWithCustomUUIDPrimaryKey.objects.all()[0].pk)
        response_json = json.loads(response.content.decode())
        self.assertEqual(response_json["step"], "chosen")
