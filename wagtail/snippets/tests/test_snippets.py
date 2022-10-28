import datetime
import json
from io import StringIO
from unittest import mock

from django.contrib.admin.utils import quote
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser, Permission
from django.contrib.contenttypes.models import ContentType
from django.core import checks, management
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpRequest, HttpResponse
from django.test import RequestFactory, TestCase
from django.test.utils import override_settings
from django.urls import reverse
from django.utils.timezone import make_aware, now
from freezegun import freeze_time
from taggit.models import Tag

from wagtail import hooks
from wagtail.admin.admin_url_finder import AdminURLFinder
from wagtail.admin.forms import WagtailAdminModelForm
from wagtail.admin.panels import FieldPanel, ObjectList, Panel, get_edit_handler
from wagtail.blocks.field_block import FieldBlockAdapter
from wagtail.models import Locale, ModelLogEntry, Page, ReferenceIndex, Revision
from wagtail.signals import published, unpublished
from wagtail.snippets.action_menu import (
    ActionMenuItem,
    get_base_snippet_action_menu_items,
)
from wagtail.snippets.blocks import SnippetChooserBlock
from wagtail.snippets.models import SNIPPET_MODELS, register_snippet
from wagtail.snippets.views.snippets import get_snippet_edit_handler
from wagtail.snippets.widgets import (
    AdminSnippetChooser,
    SnippetChooserAdapter,
    SnippetListingButton,
)
from wagtail.test.snippets.forms import FancySnippetForm
from wagtail.test.snippets.models import (
    AlphaSnippet,
    FancySnippet,
    FileUploadSnippet,
    FilterableSnippet,
    RegisterDecorator,
    RegisterFunction,
    SearchableSnippet,
    StandardSnippet,
    StandardSnippetWithCustomPrimaryKey,
    TranslatableSnippet,
    ZuluSnippet,
)
from wagtail.test.testapp.models import (
    Advert,
    AdvertWithCustomPrimaryKey,
    AdvertWithCustomUUIDPrimaryKey,
    AdvertWithTabbedInterface,
    DraftStateCustomPrimaryKeyModel,
    DraftStateModel,
    RevisableChildModel,
    RevisableModel,
    SnippetChooserModel,
    SnippetChooserModelWithCustomPrimaryKey,
)
from wagtail.test.utils import WagtailTestUtils
from wagtail.test.utils.timestamps import rendered_timestamp, submittable_timestamp
from wagtail.utils.deprecation import RemovedInWagtail50Warning


class TestSnippetIndexView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.user = self.login()

    def get(self, params={}):
        return self.client.get(reverse("wagtailsnippets:index"), params)

    def test_get_with_limited_permissions(self):
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            )
        )
        self.user.save()

        response = self.get()
        self.assertEqual(response.status_code, 302)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/generic/index.html")

    def test_displays_snippet(self):
        self.assertContains(self.get(), "Adverts")


class TestSnippetListView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()
        user_model = get_user_model()
        self.user = user_model.objects.get()

    def get(self, params={}):
        return self.client.get(reverse("wagtailsnippets_tests_advert:list"), params)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailsnippets/snippets/type_index.html")

    def get_with_limited_permissions(self):
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            )
        )
        self.user.save()

        response = self.get()
        self.assertEqual(response.status_code, 302)

    def test_ordering(self):
        """
        Listing should be ordered descending by PK if no ordering has been set on the model
        """
        for i in range(1, 11):
            Advert.objects.create(pk=i, text="advert %d" % i)
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["page_obj"][0].text, "advert 10")

    def test_simple_pagination(self):

        pages = ["0", "1", "-1", "9999", "Not a page"]
        for page in pages:
            response = self.get({"p": page})
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(
                response, "wagtailsnippets/snippets/type_index.html"
            )

    def test_displays_add_button(self):
        self.assertContains(self.get(), "Add advert")

    def test_not_searchable(self):
        self.assertFalse(self.get().context["is_searchable"])

    def test_register_snippet_listing_buttons_hook(self):
        advert = Advert.objects.create(text="My Lovely advert")

        def page_listing_buttons(snippet, user, next_url=None):
            self.assertEqual(snippet, advert)
            self.assertEqual(user, self.user)
            self.assertEqual(next_url, reverse("wagtailsnippets_tests_advert:list"))

            yield SnippetListingButton(
                "Another useless snippet listing button", "/custom-url", priority=10
            )

        with hooks.register_temporarily(
            "register_snippet_listing_buttons", page_listing_buttons
        ):
            response = self.get()

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "wagtailsnippets/snippets/listing_buttons.html"
        )

        self.assertContains(response, "Another useless snippet listing button")

    def test_construct_snippet_listing_buttons_hook(self):
        Advert.objects.create(text="My Lovely advert")

        # testapp implements a construct_snippetlisting_buttons hook
        # that add's an dummy button with the label 'Dummy Button' which points
        # to '/dummy-button'
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "wagtailsnippets/snippets/listing_buttons.html"
        )
        self.assertContains(response, "Dummy Button")
        self.assertContains(response, "/dummy-button")

    def test_use_latest_draft_as_title(self):
        snippet = DraftStateModel.objects.create(text="Draft-enabled Foo, Published")
        snippet.save_revision().publish()
        snippet.text = "Draft-enabled Bar, In Draft"
        snippet.save_revision()

        response = self.client.get(
            reverse("wagtailsnippets_tests_draftstatemodel:list"),
        )

        edit_url = reverse(
            "wagtailsnippets_tests_draftstatemodel:edit",
            args=[quote(snippet.pk)],
        )

        # Should use the latest draft title in the listing
        self.assertContains(
            response,
            f'<a href="{edit_url}">Draft-enabled Bar, In Draft</a>',
            html=True,
        )


@override_settings(WAGTAIL_I18N_ENABLED=True)
class TestLocaleSelectorOnList(TestCase, WagtailTestUtils):
    def setUp(self):
        self.fr_locale = Locale.objects.create(language_code="fr")
        self.user = self.login()

    def test_locale_selector(self):
        response = self.client.get(
            reverse("wagtailsnippets_snippetstests_translatablesnippet:list")
        )

        switch_to_french_url = (
            reverse("wagtailsnippets_snippetstests_translatablesnippet:list")
            + "?locale=fr"
        )
        self.assertContains(
            response,
            f'<a href="{switch_to_french_url}" aria-label="French" class="u-link is-live w-no-underline">',
        )

        # Check that the add URLs include the locale
        add_url = (
            reverse("wagtailsnippets_snippetstests_translatablesnippet:add")
            + "?locale=en"
        )
        self.assertContains(
            response, f'<a href="{add_url}" class="button bicolor button--icon">'
        )
        self.assertContains(
            response,
            f'No translatable snippets have been created. Why not <a href="{add_url}">add one</a>',
        )

    @override_settings(WAGTAIL_I18N_ENABLED=False)
    def test_locale_selector_not_present_when_i18n_disabled(self):
        response = self.client.get(
            reverse("wagtailsnippets_snippetstests_translatablesnippet:list")
        )

        switch_to_french_url = (
            reverse("wagtailsnippets_snippetstests_translatablesnippet:list")
            + "?locale=fr"
        )
        self.assertNotContains(
            response,
            f'<a href="{switch_to_french_url}" aria-label="French" class="u-link is-live w-no-underline">',
        )

        # Check that the add URLs don't include the locale
        add_url = reverse("wagtailsnippets_snippetstests_translatablesnippet:add")
        self.assertContains(
            response, f'<a href="{add_url}" class="button bicolor button--icon">'
        )
        self.assertContains(
            response,
            f'No translatable snippets have been created. Why not <a href="{add_url}">add one</a>',
        )

    def test_locale_selector_not_present_on_non_translatable_snippet(self):
        response = self.client.get(reverse("wagtailsnippets_tests_advert:list"))

        self.assertNotContains(
            response, 'aria-label="French" class="u-link is-live w-no-underline">'
        )

        # Check that the add URLs don't include the locale
        add_url = reverse("wagtailsnippets_tests_advert:add")
        self.assertContains(
            response, f'<a href="{add_url}" class="button bicolor button--icon">'
        )
        self.assertContains(
            response,
            f'No adverts have been created. Why not <a href="{add_url}">add one</a>',
        )


class TestModelOrdering(TestCase, WagtailTestUtils):
    def setUp(self):
        for i in range(1, 10):
            AdvertWithTabbedInterface.objects.create(text="advert %d" % i)
        AdvertWithTabbedInterface.objects.create(text="aaaadvert")
        self.login()

    def test_listing_respects_model_ordering(self):
        response = self.client.get(
            reverse("wagtailsnippets_tests_advertwithtabbedinterface:list")
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["page_obj"][0].text, "aaaadvert")

    def test_chooser_respects_model_ordering(self):
        response = self.client.get(
            reverse("wagtailsnippetchoosers_tests_advertwithtabbedinterface:choose")
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["items"][0].text, "aaaadvert")


class TestListViewOrdering(TestCase, WagtailTestUtils):
    @classmethod
    def setUpTestData(cls):
        for i in range(1, 10):
            advert = Advert.objects.create(text=f"{i*'a'}dvert {i}")
            draft = DraftStateModel.objects.create(text=f"{i*'d'}raft {i}", live=False)
            if i % 2 == 0:
                ModelLogEntry.objects.create(
                    content_type=ContentType.objects.get_for_model(Advert),
                    label="Test Advert",
                    action="wagtail.create",
                    timestamp=now(),
                    object_id=advert.pk,
                )
                draft.save_revision().publish()

    def setUp(self):
        self.login()

    def test_listing_orderable_columns_with_no_mixin(self):
        list_url = reverse("wagtailsnippets_tests_advert:list")
        response = self.client.get(list_url)
        sort_updated_url = list_url + "?ordering=_updated_at"
        sort_live_url = list_url + "?ordering=live"

        self.assertEqual(response.status_code, 200)
        # Should use the tables framework
        self.assertTemplateUsed(response, "wagtailadmin/tables/table.html")
        # The Updated column header should be a link with the correct query param
        self.assertContains(
            response,
            f'<th><a href="{sort_updated_url}" class="icon icon-arrow-down-after">Updated</a></th>',
            html=True,
        )
        # Should not contain the Status column header
        self.assertNotContains(
            response,
            f'<th><a href="{sort_live_url}" class="icon icon-arrow-down-after">Status</a></th>',
            html=True,
        )

    def test_listing_orderable_columns_with_draft_state_mixin(self):
        list_url = reverse("wagtailsnippets_tests_draftstatemodel:list")
        response = self.client.get(list_url)
        sort_updated_url = list_url + "?ordering=_updated_at"
        sort_live_url = list_url + "?ordering=live"

        self.assertEqual(response.status_code, 200)
        # Should use the tables framework
        self.assertTemplateUsed(response, "wagtailadmin/tables/table.html")
        # The Updated column header should be a link with the correct query param
        self.assertContains(
            response,
            f'<th><a href="{sort_updated_url}" class="icon icon-arrow-down-after">Updated</a></th>',
            html=True,
        )
        # The Status column header should be a link with the correct query param
        self.assertContains(
            response,
            f'<th><a href="{sort_live_url}" class="icon icon-arrow-down-after">Status</a></th>',
            html=True,
        )

    def test_order_by_updated_at_with_no_mixin(self):
        list_url = reverse("wagtailsnippets_tests_advert:list")
        response = self.client.get(list_url + "?ordering=_updated_at")

        self.assertEqual(response.status_code, 200)

        # With ascending order, empty updated_at information should be shown first
        self.assertIsNone(response.context["page_obj"][0]._updated_at)
        # The most recently updated should be at the bottom
        self.assertEqual(response.context["page_obj"][-1].text, "aaaaaaaadvert 8")
        self.assertIsNotNone(response.context["page_obj"][-1]._updated_at)

        # Should contain a link to reverse the order
        self.assertContains(response, list_url + "?ordering=-_updated_at")

        response = self.client.get(list_url + "?ordering=-_updated_at")

        self.assertEqual(response.status_code, 200)

        # With descending order, the first object should be the one that was last updated
        self.assertEqual(response.context["page_obj"][0].text, "aaaaaaaadvert 8")
        self.assertIsNotNone(response.context["page_obj"][0]._updated_at)

        # Should contain a link to reverse the order
        self.assertContains(response, list_url + "?ordering=_updated_at")

    def test_order_by_updated_at_with_draft_state_mixin(self):
        list_url = reverse("wagtailsnippets_tests_draftstatemodel:list")
        response = self.client.get(list_url + "?ordering=_updated_at")

        self.assertEqual(response.status_code, 200)

        # With ascending order, empty updated_at information should be shown first
        self.assertIsNone(response.context["page_obj"][0]._updated_at)
        # The most recently updated should be at the bottom
        self.assertEqual(response.context["page_obj"][-1].text, "ddddddddraft 8")
        self.assertIsNotNone(response.context["page_obj"][-1]._updated_at)

        # Should contain a link to reverse the order
        self.assertContains(response, list_url + "?ordering=-_updated_at")

        response = self.client.get(list_url + "?ordering=-_updated_at")

        self.assertEqual(response.status_code, 200)

        # With descending order, the first object should be the one that was last updated
        self.assertEqual(response.context["page_obj"][0].text, "ddddddddraft 8")
        self.assertIsNotNone(response.context["page_obj"][0]._updated_at)

        # Should contain a link to reverse the order
        self.assertContains(response, list_url + "?ordering=_updated_at")

    def test_order_by_live(self):
        list_url = reverse("wagtailsnippets_tests_draftstatemodel:list")
        response = self.client.get(list_url + "?ordering=live")

        self.assertEqual(response.status_code, 200)

        # With ascending order, live=False should be shown first
        self.assertFalse(response.context["page_obj"][0].live)
        # The last one should be live=True
        self.assertTrue(response.context["page_obj"][-1].live)

        # Should contain a link to reverse the order
        self.assertContains(response, list_url + "?ordering=-live")

        response = self.client.get(list_url + "?ordering=-live")

        self.assertEqual(response.status_code, 200)

        # With descending order, live=True should be shown first
        self.assertTrue(response.context["page_obj"][0].live)
        # The last one should be live=False
        self.assertFalse(response.context["page_obj"][-1].live)

        # Should contain a link to reverse the order
        self.assertContains(response, list_url + "?ordering=live")


class TestSnippetListViewWithSearchableSnippet(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

        # Create some instances of the searchable snippet for testing
        self.snippet_a = SearchableSnippet.objects.create(text="Hello")
        self.snippet_b = SearchableSnippet.objects.create(text="World")
        self.snippet_c = SearchableSnippet.objects.create(text="Hello World")

    def get(self, params={}):
        return self.client.get(
            reverse("wagtailsnippets_snippetstests_searchablesnippet:list"),
            params,
        )

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailsnippets/snippets/type_index.html")

        # All snippets should be in items
        items = list(response.context["page_obj"].object_list)
        self.assertIn(self.snippet_a, items)
        self.assertIn(self.snippet_b, items)
        self.assertIn(self.snippet_c, items)

    def test_is_searchable(self):
        self.assertTrue(self.get().context["is_searchable"])

    def test_search_hello(self):
        response = self.get({"q": "Hello"})

        # Just snippets with "Hello" should be in items
        items = list(response.context["page_obj"].object_list)
        self.assertIn(self.snippet_a, items)
        self.assertNotIn(self.snippet_b, items)
        self.assertIn(self.snippet_c, items)

    def test_search_world(self):
        response = self.get({"q": "World"})

        # Just snippets with "World" should be in items
        items = list(response.context["page_obj"].object_list)
        self.assertNotIn(self.snippet_a, items)
        self.assertIn(self.snippet_b, items)
        self.assertIn(self.snippet_c, items)


class TestSnippetListViewWithFilterSet(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

    def get(self, params={}):
        return self.client.get(
            reverse("wagtailsnippets_snippetstests_filterablesnippet:list"),
            params,
        )

    def create_test_snippets(self):
        FilterableSnippet.objects.create(text="From Indonesia", country_code="ID")
        FilterableSnippet.objects.create(text="From the UK", country_code="UK")

    def test_unfiltered_no_results(self):
        response = self.get()
        add_url = reverse("wagtailsnippets_snippetstests_filterablesnippet:add")
        self.assertContains(
            response,
            f'No filterable snippets have been created. Why not <a href="{add_url}">add one</a>',
        )
        self.assertContains(
            response,
            '<button class="button button-select__option button-select__option--selected" value="">All</button>',
            html=True,
        )
        self.assertTemplateUsed(response, "wagtailadmin/shared/filters.html")

    def test_unfiltered_with_results(self):
        self.create_test_snippets()
        response = self.get()
        self.assertTemplateUsed(response, "wagtailadmin/shared/filters.html")
        self.assertContains(response, "From Indonesia")
        self.assertContains(response, "From the UK")
        self.assertNotContains(response, "There are 2 matches")
        self.assertContains(
            response,
            '<button class="button button-select__option button-select__option--selected" value="">All</button>',
            html=True,
        )

    def test_empty_filter_with_results(self):
        self.create_test_snippets()
        response = self.get({"country_code": ""})
        self.assertTemplateUsed(response, "wagtailadmin/shared/filters.html")
        self.assertContains(response, "From Indonesia")
        self.assertContains(response, "From the UK")
        self.assertNotContains(response, "There are 2 matches")
        self.assertContains(
            response,
            '<button class="button button-select__option button-select__option--selected" value="">All</button>',
            html=True,
        )

    def test_filtered_no_results(self):
        self.create_test_snippets()
        response = self.get({"country_code": "PH"})
        self.assertTemplateUsed(response, "wagtailadmin/shared/filters.html")
        self.assertContains(response, "Sorry, no filterable snippets match your query")
        self.assertContains(
            response,
            '<button class="button button-select__option button-select__option--selected" value="PH">Philippines</button>',
            html=True,
        )

    def test_filtered_with_results(self):
        self.create_test_snippets()
        response = self.get({"country_code": "ID"})
        self.assertTemplateUsed(response, "wagtailadmin/shared/filters.html")
        self.assertContains(response, "From Indonesia")
        self.assertContains(response, "There is 1 match")
        self.assertContains(
            response,
            '<button class="button button-select__option button-select__option--selected" value="ID">Indonesia</button>',
            html=True,
        )

    def test_filtered_searched_no_results(self):
        self.create_test_snippets()
        response = self.get({"country_code": "ID", "q": "the"})
        self.assertTemplateUsed(response, "wagtailadmin/shared/filters.html")
        self.assertContains(response, "Sorry, no filterable snippets match your query")
        self.assertContains(
            response,
            '<button class="button button-select__option button-select__option--selected" value="ID">Indonesia</button>',
            html=True,
        )

    def test_filtered_searched_with_results(self):
        self.create_test_snippets()
        response = self.get({"country_code": "UK", "q": "the"})
        self.assertTemplateUsed(response, "wagtailadmin/shared/filters.html")
        self.assertContains(response, "From the UK")
        self.assertContains(response, "There is 1 match")
        self.assertContains(
            response,
            '<button class="button button-select__option button-select__option--selected" value="UK">United Kingdom</button>',
            html=True,
        )


class TestListViewWithCustomColumns(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

    @classmethod
    def setUpTestData(cls):
        FilterableSnippet.objects.create(text="From Indonesia", country_code="ID")
        FilterableSnippet.objects.create(text="From the UK", country_code="UK")

    def get(self, params={}):
        return self.client.get(
            reverse("wagtailsnippets_snippetstests_filterablesnippet:list"),
            params,
        )

    def test_custom_columns(self):
        response = self.get()
        self.assertContains(response, "Text")
        self.assertContains(response, "Country Code")
        self.assertContains(response, "Custom Foo Column")
        self.assertContains(response, "Updated")

        self.assertContains(response, "Foo UK")

        list_url = reverse("wagtailsnippets_snippetstests_filterablesnippet:list")
        sort_country_code_url = list_url + "?ordering=country_code"

        # One from the country code column, another from the custom foo column
        self.assertContains(response, sort_country_code_url, count=2)

        html = response.content.decode()

        # The bulk actions column plus 4 columns defined in FilterableSnippetViewSet
        self.assertTagInHTML("<th>", html, count=5, allow_extra_attrs=True)


class TestSnippetCreateView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.user = self.login()

    def get(self, params={}, model=Advert):
        app_label = model._meta.app_label
        model_name = model._meta.model_name
        return self.client.get(
            reverse(f"wagtailsnippets_{app_label}_{model_name}:add"), params
        )

    def post(self, post_data={}, model=Advert):
        app_label = model._meta.app_label
        model_name = model._meta.model_name
        return self.client.post(
            reverse(f"wagtailsnippets_{app_label}_{model_name}:add"), post_data
        )

    def test_get_with_limited_permissions(self):
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            )
        )
        self.user.save()

        response = self.get()
        self.assertEqual(response.status_code, 302)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailsnippets/snippets/create.html")
        self.assertNotContains(response, 'role="tablist"', html=True)

    def test_snippet_with_tabbed_interface(self):
        response = self.client.get(
            reverse("wagtailsnippets_tests_advertwithtabbedinterface:add")
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailsnippets/snippets/create.html")
        self.assertContains(response, 'role="tablist"')
        self.assertContains(
            response,
            '<a id="tab-label-advert" href="#tab-advert" class="w-tabs__tab " role="tab" aria-selected="false" tabindex="-1">',
        )
        self.assertContains(
            response,
            '<a id="tab-label-other" href="#tab-other" class="w-tabs__tab " role="tab" aria-selected="false" tabindex="-1">',
        )
        self.assertContains(response, "Other panels help text")
        self.assertContains(response, "Top-level help text")

    def test_create_with_limited_permissions(self):
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            )
        )
        self.user.save()

        response = self.post(
            post_data={"text": "test text", "url": "http://www.example.com/"}
        )
        self.assertEqual(response.status_code, 302)

    def test_create_invalid(self):
        response = self.post(post_data={"foo": "bar"})
        self.assertContains(response, "The snippet could not be created due to errors.")
        self.assertContains(response, "error-message", count=1)
        self.assertContains(response, "This field is required", count=1)

    def test_create(self):
        response = self.post(
            post_data={"text": "test_advert", "url": "http://www.example.com/"}
        )
        self.assertRedirects(response, reverse("wagtailsnippets_tests_advert:list"))

        snippets = Advert.objects.filter(text="test_advert")
        self.assertEqual(snippets.count(), 1)
        self.assertEqual(snippets.first().url, "http://www.example.com/")

    def test_create_with_tags(self):
        tags = ["hello", "world"]
        response = self.post(
            post_data={
                "text": "test_advert",
                "url": "http://example.com/",
                "tags": ", ".join(tags),
            }
        )

        self.assertRedirects(response, reverse("wagtailsnippets_tests_advert:list"))

        snippet = Advert.objects.get(text="test_advert")

        expected_tags = list(Tag.objects.order_by("name").filter(name__in=tags))
        self.assertEqual(len(expected_tags), 2)
        self.assertEqual(list(snippet.tags.order_by("name")), expected_tags)

    def test_create_file_upload_multipart(self):
        response = self.get(model=FileUploadSnippet)
        self.assertContains(response, 'enctype="multipart/form-data"')

        response = self.post(
            model=FileUploadSnippet,
            post_data={"file": SimpleUploadedFile("test.txt", b"Uploaded file")},
        )
        self.assertRedirects(
            response,
            reverse("wagtailsnippets_snippetstests_fileuploadsnippet:list"),
        )
        snippet = FileUploadSnippet.objects.get()
        self.assertEqual(snippet.file.read(), b"Uploaded file")

    def test_create_with_revision(self):
        response = self.post(
            model=RevisableModel, post_data={"text": "create_revisable"}
        )
        self.assertRedirects(
            response, reverse("wagtailsnippets_tests_revisablemodel:list")
        )

        snippets = RevisableModel.objects.filter(text="create_revisable")
        snippet = snippets.first()
        self.assertEqual(snippets.count(), 1)

        # The revision should be created
        revisions = snippet.revisions
        revision = revisions.first()
        self.assertEqual(revisions.count(), 1)
        self.assertEqual(revision.content["text"], "create_revisable")

        # The log entry should have the revision attached
        log_entries = ModelLogEntry.objects.for_instance(snippet).filter(
            action="wagtail.create"
        )
        self.assertEqual(log_entries.count(), 1)
        self.assertEqual(log_entries.first().revision, revision)

    def test_before_create_snippet_hook_get(self):
        def hook_func(request, model):
            self.assertIsInstance(request, HttpRequest)
            self.assertEqual(model, Advert)
            return HttpResponse("Overridden!")

        with self.register_hook("before_create_snippet", hook_func):
            response = self.get()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")

    def test_before_create_snippet_hook_post(self):
        def hook_func(request, model):
            self.assertIsInstance(request, HttpRequest)
            self.assertEqual(model, Advert)
            return HttpResponse("Overridden!")

        with self.register_hook("before_create_snippet", hook_func):
            post_data = {"text": "Hook test", "url": "http://www.example.com/"}
            response = self.post(post_data=post_data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")

        # Request intercepted before advert was created
        self.assertFalse(Advert.objects.exists())

    def test_after_create_snippet_hook(self):
        def hook_func(request, instance):
            self.assertIsInstance(request, HttpRequest)
            self.assertEqual(instance.text, "Hook test")
            self.assertEqual(instance.url, "http://www.example.com/")
            return HttpResponse("Overridden!")

        with self.register_hook("after_create_snippet", hook_func):
            post_data = {"text": "Hook test", "url": "http://www.example.com/"}
            response = self.post(post_data=post_data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")

        # Request intercepted after advert was created
        self.assertTrue(Advert.objects.exists())

    def test_register_snippet_action_menu_item(self):
        class TestSnippetActionMenuItem(ActionMenuItem):
            label = "Test"
            name = "test"
            icon_name = "undo"
            classname = "action-secondary"

            def is_shown(self, context):
                return True

        def hook_func(model):
            return TestSnippetActionMenuItem(order=0)

        with self.register_hook("register_snippet_action_menu_item", hook_func):
            get_base_snippet_action_menu_items.cache_clear()

            response = self.get()

        get_base_snippet_action_menu_items.cache_clear()

        self.assertContains(
            response,
            '<button type="submit" name="test" value="Test" class="button action-secondary"><svg class="icon icon-undo icon" aria-hidden="true"><use href="#icon-undo"></use></svg>Test</button>',
            html=True,
        )

    def test_register_snippet_action_menu_item_as_none(self):
        def hook_func(model):
            return None

        with self.register_hook("register_snippet_action_menu_item", hook_func):
            get_base_snippet_action_menu_items.cache_clear()

            response = self.get()

        get_base_snippet_action_menu_items.cache_clear()
        self.assertEqual(response.status_code, 200)

    def test_construct_snippet_action_menu(self):
        class TestSnippetActionMenuItem(ActionMenuItem):
            label = "Test"
            name = "test"
            icon_name = "undo"
            classname = "action-secondary"

            def is_shown(self, context):
                return True

        def hook_func(menu_items, request, context):
            self.assertIsInstance(menu_items, list)
            self.assertIsInstance(request, WSGIRequest)
            self.assertEqual(context["view"], "create")
            self.assertEqual(context["model"], Advert)

            # Replace save menu item
            menu_items[:] = [TestSnippetActionMenuItem(order=0)]

        with self.register_hook("construct_snippet_action_menu", hook_func):
            response = self.get()

        self.assertContains(
            response,
            '<button type="submit" name="test" value="Test" class="button action-secondary"><svg class="icon icon-undo icon" aria-hidden="true"><use href="#icon-undo"></use></svg>Test</button>',
            html=True,
        )
        self.assertNotContains(response, "<em>'Save'</em>")


@override_settings(WAGTAIL_I18N_ENABLED=True)
class TestLocaleSelectorOnCreate(TestCase, WagtailTestUtils):
    fixtures = ["test.json"]

    def setUp(self):
        self.fr_locale = Locale.objects.create(language_code="fr")
        self.user = self.login()

    def test_locale_selector(self):
        response = self.client.get(
            reverse("wagtailsnippets_snippetstests_translatablesnippet:add")
        )

        self.assertContains(response, "Switch locales")

    @override_settings(WAGTAIL_I18N_ENABLED=False)
    def test_locale_selector_not_present_when_i18n_disabled(self):
        response = self.client.get(
            reverse("wagtailsnippets_snippetstests_translatablesnippet:add")
        )

        self.assertNotContains(response, "Switch locales")

    def test_locale_selector_not_present_on_non_translatable_snippet(self):
        response = self.client.get(reverse("wagtailsnippets_tests_advert:add"))

        self.assertNotContains(response, "Switch locales")


class TestCreateDraftStateSnippet(TestCase, WagtailTestUtils):
    def setUp(self):
        self.user = self.login()

    def get(self):
        return self.client.get(reverse("wagtailsnippets_tests_draftstatemodel:add"))

    def post(self, post_data={}):
        return self.client.post(
            reverse("wagtailsnippets_tests_draftstatemodel:add"),
            post_data,
        )

    def test_get(self):
        response = self.get()

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailsnippets/snippets/create.html")

        # The save button should be labelled "Save draft"
        self.assertContains(response, "Save draft")
        # The publish button should exist
        self.assertContains(response, "Publish")
        # The publish button should have name="action-publish"
        self.assertContains(
            response,
            '<button type="submit" name="action-publish" value="action-publish" class="button action-save button-longrunning" data-clicked-text="Publishing…">',
        )
        # The status side panel should not be shown
        self.assertNotContains(
            response,
            '<div class="form-side__panel" data-side-panel="status">',
        )

        # Should not show the Unpublish action menu item
        unpublish_url = "/admin/snippets/tests/draftstatemodel/unpublish/"
        self.assertNotContains(response, unpublish_url)
        self.assertNotContains(response, "Unpublish")

    def test_save_draft(self):
        response = self.post(post_data={"text": "Draft-enabled Foo"})
        snippet = DraftStateModel.objects.get(text="Draft-enabled Foo")

        self.assertRedirects(
            response, reverse("wagtailsnippets_tests_draftstatemodel:list")
        )

        # The instance should be created
        self.assertEqual(snippet.text, "Draft-enabled Foo")

        # The instance should be a draft
        self.assertFalse(snippet.live)
        self.assertTrue(snippet.has_unpublished_changes)
        self.assertIsNone(snippet.first_published_at)
        self.assertIsNone(snippet.last_published_at)
        self.assertIsNone(snippet.live_revision)

        # A revision should be created and set as latest_revision
        self.assertIsNotNone(snippet.latest_revision)

        # The revision content should contain the data
        self.assertEqual(snippet.latest_revision.content["text"], "Draft-enabled Foo")

    def test_publish(self):
        # Connect a mock signal handler to published signal
        mock_handler = mock.MagicMock()
        published.connect(mock_handler)

        timestamp = now()
        with freeze_time(timestamp):
            response = self.post(
                post_data={
                    "text": "Draft-enabled Foo, Published",
                    "action-publish": "action-publish",
                }
            )
        snippet = DraftStateModel.objects.get(text="Draft-enabled Foo, Published")

        self.assertRedirects(
            response, reverse("wagtailsnippets_tests_draftstatemodel:list")
        )

        # The instance should be created
        self.assertEqual(snippet.text, "Draft-enabled Foo, Published")

        # The instance should be live
        self.assertTrue(snippet.live)
        self.assertFalse(snippet.has_unpublished_changes)
        self.assertEqual(snippet.first_published_at, timestamp)
        self.assertEqual(snippet.last_published_at, timestamp)

        # A revision should be created and set as both latest_revision and live_revision
        self.assertIsNotNone(snippet.live_revision)
        self.assertEqual(snippet.live_revision, snippet.latest_revision)

        # The revision content should contain the new data
        self.assertEqual(
            snippet.live_revision.content["text"],
            "Draft-enabled Foo, Published",
        )

        # Check that the published signal was fired
        self.assertEqual(mock_handler.call_count, 1)
        mock_call = mock_handler.mock_calls[0][2]

        self.assertEqual(mock_call["sender"], DraftStateModel)
        self.assertEqual(mock_call["instance"], snippet)
        self.assertIsInstance(mock_call["instance"], DraftStateModel)

    def test_create_scheduled(self):
        go_live_at = now() + datetime.timedelta(days=1)
        expire_at = now() + datetime.timedelta(days=2)
        response = self.post(
            post_data={
                "text": "Some content",
                "go_live_at": submittable_timestamp(go_live_at),
                "expire_at": submittable_timestamp(expire_at),
            }
        )

        # Should be redirected to the listing page
        self.assertEqual(response.status_code, 302)

        snippet = DraftStateModel.objects.get(text="Some content")
        self.assertEqual(snippet.go_live_at.date(), go_live_at.date())
        self.assertEqual(snippet.expire_at.date(), expire_at.date())
        self.assertIs(snippet.expired, False)
        self.assertTrue(snippet.status_string, "draft")

        # No revisions with approved_go_live_at
        self.assertFalse(
            Revision.objects.for_instance(snippet)
            .exclude(approved_go_live_at__isnull=True)
            .exists()
        )

    def test_create_scheduled_go_live_before_expiry(self):
        response = self.post(
            post_data={
                "text": "Some content",
                "go_live_at": submittable_timestamp(now() + datetime.timedelta(days=2)),
                "expire_at": submittable_timestamp(now() + datetime.timedelta(days=1)),
            }
        )

        self.assertEqual(response.status_code, 200)

        # Check that a form error was raised
        self.assertFormError(
            response,
            "form",
            "go_live_at",
            "Go live date/time must be before expiry date/time",
        )
        self.assertFormError(
            response,
            "form",
            "expire_at",
            "Go live date/time must be before expiry date/time",
        )

    def test_create_scheduled_expire_in_the_past(self):
        response = self.post(
            post_data={
                "text": "Some content",
                "expire_at": submittable_timestamp(now() + datetime.timedelta(days=-1)),
            }
        )

        self.assertEqual(response.status_code, 200)

        # Check that a form error was raised
        self.assertFormError(
            response, "form", "expire_at", "Expiry date/time must be in the future"
        )

    def test_create_post_publish_scheduled(self):
        go_live_at = now() + datetime.timedelta(days=1)
        expire_at = now() + datetime.timedelta(days=2)
        response = self.post(
            post_data={
                "text": "Some content",
                "action-publish": "Publish",
                "go_live_at": submittable_timestamp(go_live_at),
                "expire_at": submittable_timestamp(expire_at),
            }
        )

        # Should be redirected to the listing page
        self.assertEqual(response.status_code, 302)

        # Find the object and check it
        snippet = DraftStateModel.objects.get(text="Some content")
        self.assertEqual(snippet.go_live_at.date(), go_live_at.date())
        self.assertEqual(snippet.expire_at.date(), expire_at.date())
        self.assertIs(snippet.expired, False)

        # A revision with approved_go_live_at should exist now
        self.assertTrue(
            Revision.objects.for_instance(snippet)
            .exclude(approved_go_live_at__isnull=True)
            .exists()
        )
        # But snippet won't be live
        self.assertFalse(snippet.live)
        self.assertFalse(snippet.first_published_at)
        self.assertTrue(snippet.status_string, "scheduled")


class BaseTestSnippetEditView(TestCase, WagtailTestUtils):
    def get(self, params={}):
        snippet = self.test_snippet
        app_label = snippet._meta.app_label
        model_name = snippet._meta.model_name
        args = [quote(snippet.pk)]
        return self.client.get(
            reverse(f"wagtailsnippets_{app_label}_{model_name}:edit", args=args), params
        )

    def post(self, post_data={}):
        snippet = self.test_snippet
        app_label = snippet._meta.app_label
        model_name = snippet._meta.model_name
        args = [quote(snippet.pk)]
        return self.client.post(
            reverse(f"wagtailsnippets_{app_label}_{model_name}:edit", args=args),
            post_data,
        )

    def setUp(self):
        self.user = self.login()


class TestSnippetEditView(BaseTestSnippetEditView):
    fixtures = ["test.json"]

    def setUp(self):
        super().setUp()
        self.test_snippet = Advert.objects.get(pk=1)
        ModelLogEntry.objects.create(
            content_type=ContentType.objects.get_for_model(Advert),
            label="Test Advert",
            action="wagtail.create",
            timestamp=now() - datetime.timedelta(weeks=3),
            user=self.user,
            object_id="1",
        )

    def test_get_with_limited_permissions(self):
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            )
        )
        self.user.save()

        response = self.get()
        self.assertEqual(response.status_code, 302)

    def test_simple(self):
        response = self.get()
        html = response.content.decode()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailsnippets/snippets/edit.html")
        self.assertNotContains(response, 'role="tablist"')

        # Without DraftStateMixin, there should be no "No publishing schedule set" info
        self.assertNotContains(response, "No publishing schedule set")

        history_url = reverse(
            "wagtailsnippets_tests_advert:history", args=[quote(self.test_snippet.pk)]
        )
        # History link should be present, one in the header and one in the status side panel
        self.assertContains(response, history_url, count=2)

        # Live status and last updated info should be shown, with a link to the history page
        self.assertContains(response, "3\xa0weeks ago")
        self.assertTagInHTML(
            f'<a href="{history_url}" aria-describedby="status-sidebar-live">View history</a>',
            html,
            allow_extra_attrs=True,
        )

        url_finder = AdminURLFinder(self.user)
        expected_url = "/admin/snippets/tests/advert/edit/%d/" % self.test_snippet.pk
        self.assertEqual(url_finder.get_edit_url(self.test_snippet), expected_url)

    def test_non_existant_model(self):
        response = self.client.get(
            f"/admin/snippets/tests/foo/edit/{quote(self.test_snippet.pk)}/"
        )
        self.assertEqual(response.status_code, 404)

    def test_nonexistant_id(self):
        response = self.client.get(
            reverse("wagtailsnippets_tests_advert:edit", args=[999999])
        )
        self.assertEqual(response.status_code, 404)

    def test_edit_with_limited_permissions(self):
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            )
        )
        self.user.save()

        response = self.post(
            post_data={"text": "test text", "url": "http://www.example.com/"}
        )
        self.assertEqual(response.status_code, 302)

        url_finder = AdminURLFinder(self.user)
        self.assertIsNone(url_finder.get_edit_url(self.test_snippet))

    def test_edit_invalid(self):
        response = self.post(post_data={"foo": "bar"})
        self.assertContains(response, "The snippet could not be saved due to errors.")
        self.assertContains(response, "error-message", count=1)
        self.assertContains(response, "This field is required", count=1)

    def test_edit(self):
        response = self.post(
            post_data={
                "text": "edited_test_advert",
                "url": "http://www.example.com/edited",
            }
        )
        self.assertRedirects(response, reverse("wagtailsnippets_tests_advert:list"))

        snippets = Advert.objects.filter(text="edited_test_advert")
        self.assertEqual(snippets.count(), 1)
        self.assertEqual(snippets.first().url, "http://www.example.com/edited")

    def test_edit_with_tags(self):
        tags = ["hello", "world"]
        response = self.post(
            post_data={
                "text": "edited_test_advert",
                "url": "http://www.example.com/edited",
                "tags": ", ".join(tags),
            }
        )

        self.assertRedirects(response, reverse("wagtailsnippets_tests_advert:list"))

        snippet = Advert.objects.get(text="edited_test_advert")

        expected_tags = list(Tag.objects.order_by("name").filter(name__in=tags))
        self.assertEqual(len(expected_tags), 2)
        self.assertEqual(list(snippet.tags.order_by("name")), expected_tags)

    def test_before_edit_snippet_hook_get(self):
        def hook_func(request, instance):
            self.assertIsInstance(request, HttpRequest)
            self.assertEqual(instance.text, "test_advert")
            self.assertEqual(instance.url, "http://www.example.com")
            return HttpResponse("Overridden!")

        with self.register_hook("before_edit_snippet", hook_func):
            response = self.get()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")

    def test_before_edit_snippet_hook_post(self):
        def hook_func(request, instance):
            self.assertIsInstance(request, HttpRequest)
            self.assertEqual(instance.text, "test_advert")
            self.assertEqual(instance.url, "http://www.example.com")
            return HttpResponse("Overridden!")

        with self.register_hook("before_edit_snippet", hook_func):
            response = self.post(
                post_data={
                    "text": "Edited and runs hook",
                    "url": "http://www.example.com/hook-enabled-edited",
                }
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")

        # Request intercepted before advert was updated
        self.assertEqual(Advert.objects.get().text, "test_advert")

    def test_after_edit_snippet_hook(self):
        def hook_func(request, instance):
            self.assertIsInstance(request, HttpRequest)
            self.assertEqual(instance.text, "Edited and runs hook")
            self.assertEqual(instance.url, "http://www.example.com/hook-enabled-edited")
            return HttpResponse("Overridden!")

        with self.register_hook("after_edit_snippet", hook_func):
            response = self.post(
                post_data={
                    "text": "Edited and runs hook",
                    "url": "http://www.example.com/hook-enabled-edited",
                }
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")

        # Request intercepted after advert was updated
        self.assertEqual(Advert.objects.get().text, "Edited and runs hook")

    def test_register_snippet_action_menu_item(self):
        class TestSnippetActionMenuItem(ActionMenuItem):
            label = "Test"
            name = "test"
            icon_name = "undo"
            classname = "action-secondary"

            def is_shown(self, context):
                return True

        def hook_func(model):
            return TestSnippetActionMenuItem(order=0)

        with self.register_hook("register_snippet_action_menu_item", hook_func):
            get_base_snippet_action_menu_items.cache_clear()

            response = self.get()

        get_base_snippet_action_menu_items.cache_clear()

        self.assertContains(
            response,
            '<button type="submit" name="test" value="Test" class="button action-secondary"><svg class="icon icon-undo icon" aria-hidden="true"><use href="#icon-undo"></use></svg>Test</button>',
            html=True,
        )

    def test_construct_snippet_action_menu(self):
        def hook_func(menu_items, request, context):
            self.assertIsInstance(menu_items, list)
            self.assertIsInstance(request, WSGIRequest)
            self.assertEqual(context["view"], "edit")
            self.assertEqual(context["instance"], self.test_snippet)
            self.assertEqual(context["model"], Advert)

            # Remove the save item
            del menu_items[0]

        with self.register_hook("construct_snippet_action_menu", hook_func):
            response = self.get()

        self.assertNotContains(response, "<em>Save</em>")


class TestEditTabbedSnippet(BaseTestSnippetEditView):
    def setUp(self):
        super().setUp()
        self.test_snippet = AdvertWithTabbedInterface.objects.create(
            text="test_advert",
            url="http://www.example.com",
            something_else="Model with tabbed interface",
        )

    def test_snippet_with_tabbed_interface(self):
        response = self.get()

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailsnippets/snippets/edit.html")
        self.assertContains(response, 'role="tablist"')
        self.assertContains(
            response,
            '<a id="tab-label-advert" href="#tab-advert" class="w-tabs__tab " role="tab" aria-selected="false" tabindex="-1">',
        )
        self.assertContains(
            response,
            '<a id="tab-label-other" href="#tab-other" class="w-tabs__tab " role="tab" aria-selected="false" tabindex="-1">',
        )


class TestEditFileUploadSnippet(BaseTestSnippetEditView):
    def setUp(self):
        super().setUp()
        self.test_snippet = FileUploadSnippet.objects.create(
            file=ContentFile(b"Simple text document", "test.txt")
        )

    def test_edit_file_upload_multipart(self):
        response = self.get()
        self.assertContains(response, 'enctype="multipart/form-data"')

        response = self.post(
            post_data={
                "file": SimpleUploadedFile("replacement.txt", b"Replacement document")
            }
        )
        self.assertRedirects(
            response,
            reverse("wagtailsnippets_snippetstests_fileuploadsnippet:list"),
        )
        snippet = FileUploadSnippet.objects.get()
        self.assertEqual(snippet.file.read(), b"Replacement document")


@override_settings(WAGTAIL_I18N_ENABLED=True)
class TestLocaleSelectorOnEdit(BaseTestSnippetEditView):
    fixtures = ["test.json"]

    LOCALE_SELECTOR_LABEL = "Switch locales"
    LOCALE_INDICATOR_HTML = '<h3 id="status-sidebar-english"'

    def setUp(self):
        super().setUp()
        self.test_snippet = TranslatableSnippet.objects.create(text="This is a test")
        self.fr_locale = Locale.objects.create(language_code="fr")
        self.test_snippet_fr = self.test_snippet.copy_for_translation(self.fr_locale)
        self.test_snippet_fr.save()

    def test_locale_selector(self):
        response = self.get()
        self.assertContains(response, self.LOCALE_SELECTOR_LABEL)
        self.assertContains(response, self.LOCALE_INDICATOR_HTML)

    def test_locale_selector_without_translation(self):
        self.test_snippet_fr.delete()
        response = self.get()
        # The "Switch locale" button should not be shown
        self.assertNotContains(response, self.LOCALE_SELECTOR_LABEL)
        # Locale status still available and says "No other translations"
        self.assertContains(response, self.LOCALE_INDICATOR_HTML)
        self.assertContains(response, "No other translations")

    @override_settings(WAGTAIL_I18N_ENABLED=False)
    def test_locale_selector_not_present_when_i18n_disabled(self):
        response = self.get()
        self.assertNotContains(response, self.LOCALE_SELECTOR_LABEL)
        self.assertNotContains(response, self.LOCALE_INDICATOR_HTML)

    def test_locale_selector_not_present_on_non_translatable_snippet(self):
        self.test_snippet = Advert.objects.get(pk=1)
        response = self.get()
        self.assertNotContains(response, self.LOCALE_SELECTOR_LABEL)
        self.assertNotContains(response, self.LOCALE_INDICATOR_HTML)


class TestEditRevisionSnippet(BaseTestSnippetEditView):
    def setUp(self):
        super().setUp()
        self.test_snippet = RevisableModel.objects.create(text="foo")

    def test_edit_snippet_with_revision(self):
        response = self.post(post_data={"text": "bar"})
        self.assertRedirects(
            response, reverse("wagtailsnippets_tests_revisablemodel:list")
        )

        # The instance should be updated
        snippets = RevisableModel.objects.filter(text="bar")
        self.assertEqual(snippets.count(), 1)

        # The revision should be created
        revisions = self.test_snippet.revisions
        revision = revisions.first()
        self.assertEqual(revisions.count(), 1)
        self.assertEqual(revision.content["text"], "bar")

        # The log entry should have the revision attached
        log_entries = ModelLogEntry.objects.for_instance(self.test_snippet).filter(
            action="wagtail.edit"
        )
        self.assertEqual(log_entries.count(), 1)
        self.assertEqual(log_entries.first().revision, revision)


class TestEditDraftStateSnippet(BaseTestSnippetEditView):
    def setUp(self):
        super().setUp()
        self.test_snippet = DraftStateCustomPrimaryKeyModel.objects.create(
            custom_id="custom/1", text="Draft-enabled Foo", live=False
        )

    def test_get(self):
        response = self.get()

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailsnippets/snippets/edit.html")

        # The save button should be labelled "Save draft"
        self.assertContains(response, "Save draft")
        # The publish button should exist
        self.assertContains(response, "Publish")
        # The publish button should have name="action-publish"
        self.assertContains(
            response,
            '<button type="submit" name="action-publish" value="action-publish" class="button action-save button-longrunning" data-clicked-text="Publishing…">',
        )

        # The status side panel should show "No publishing schedule set" info
        self.assertContains(response, "No publishing schedule set")

        # Should not show the Unpublish action menu item
        unpublish_url = reverse(
            "wagtailsnippets_tests_draftstatecustomprimarykeymodel:unpublish",
            args=(quote(self.test_snippet.pk),),
        )
        self.assertNotContains(
            response,
            f'<a class="button action-secondary" href="{unpublish_url}">',
        )
        self.assertNotContains(response, "Unpublish")

    def test_save_draft(self):
        response = self.post(post_data={"text": "Draft-enabled Bar"})
        self.test_snippet.refresh_from_db()
        revisions = Revision.objects.for_instance(self.test_snippet)
        latest_revision = self.test_snippet.latest_revision

        self.assertRedirects(
            response,
            reverse("wagtailsnippets_tests_draftstatecustomprimarykeymodel:list"),
        )

        # The instance should not be updated
        self.assertEqual(self.test_snippet.text, "Draft-enabled Foo")

        # The instance should be a draft
        self.assertFalse(self.test_snippet.live)
        self.assertTrue(self.test_snippet.has_unpublished_changes)
        self.assertIsNone(self.test_snippet.first_published_at)
        self.assertIsNone(self.test_snippet.last_published_at)
        self.assertIsNone(self.test_snippet.live_revision)

        # The revision should be created and set as latest_revision
        self.assertEqual(revisions.count(), 1)
        self.assertEqual(latest_revision, revisions.first())

        # The revision content should contain the new data
        self.assertEqual(latest_revision.content["text"], "Draft-enabled Bar")

    def test_publish(self):
        # Connect a mock signal handler to published signal
        mock_handler = mock.MagicMock()
        published.connect(mock_handler)

        timestamp = now()
        with freeze_time(timestamp):
            response = self.post(
                post_data={
                    "text": "Draft-enabled Bar, Published",
                    "action-publish": "action-publish",
                }
            )

        self.test_snippet.refresh_from_db()
        revisions = Revision.objects.for_instance(self.test_snippet)
        latest_revision = self.test_snippet.latest_revision

        log_entries = ModelLogEntry.objects.filter(
            content_type=ContentType.objects.get_for_model(
                DraftStateCustomPrimaryKeyModel
            ),
            action="wagtail.publish",
            object_id=self.test_snippet.pk,
        )
        log_entry = log_entries.first()

        self.assertRedirects(
            response,
            reverse("wagtailsnippets_tests_draftstatecustomprimarykeymodel:list"),
        )

        # The instance should be updated
        self.assertEqual(self.test_snippet.text, "Draft-enabled Bar, Published")

        # The instance should be live
        self.assertTrue(self.test_snippet.live)
        self.assertFalse(self.test_snippet.has_unpublished_changes)
        self.assertEqual(self.test_snippet.first_published_at, timestamp)
        self.assertEqual(self.test_snippet.last_published_at, timestamp)
        self.assertEqual(self.test_snippet.live_revision, latest_revision)

        # The revision should be created and set as latest_revision
        self.assertEqual(revisions.count(), 1)
        self.assertEqual(latest_revision, revisions.first())

        # The revision content should contain the new data
        self.assertEqual(
            latest_revision.content["text"],
            "Draft-enabled Bar, Published",
        )

        # A log entry with wagtail.publish action should be created
        self.assertEqual(log_entries.count(), 1)
        self.assertEqual(log_entry.timestamp, timestamp)

        # Check that the published signal was fired
        self.assertEqual(mock_handler.call_count, 1)
        mock_call = mock_handler.mock_calls[0][2]

        self.assertEqual(mock_call["sender"], DraftStateCustomPrimaryKeyModel)
        self.assertEqual(mock_call["instance"], self.test_snippet)
        self.assertIsInstance(mock_call["instance"], DraftStateCustomPrimaryKeyModel)

    def test_save_draft_then_publish(self):
        save_timestamp = now()
        with freeze_time(save_timestamp):
            self.test_snippet.text = "Draft-enabled Bar, In Draft"
            self.test_snippet.save_revision()

        publish_timestamp = now()
        with freeze_time(publish_timestamp):
            response = self.post(
                post_data={
                    "text": "Draft-enabled Bar, Now Published",
                    "action-publish": "action-publish",
                }
            )

        self.test_snippet.refresh_from_db()
        revisions = Revision.objects.for_instance(self.test_snippet).order_by("pk")
        latest_revision = self.test_snippet.latest_revision

        self.assertRedirects(
            response,
            reverse("wagtailsnippets_tests_draftstatecustomprimarykeymodel:list"),
        )

        # The instance should be updated
        self.assertEqual(self.test_snippet.text, "Draft-enabled Bar, Now Published")

        # The instance should be live
        self.assertTrue(self.test_snippet.live)
        self.assertFalse(self.test_snippet.has_unpublished_changes)
        self.assertEqual(self.test_snippet.first_published_at, publish_timestamp)
        self.assertEqual(self.test_snippet.last_published_at, publish_timestamp)
        self.assertEqual(self.test_snippet.live_revision, latest_revision)

        # The revision should be created and set as latest_revision
        self.assertEqual(revisions.count(), 2)
        self.assertEqual(latest_revision, revisions.last())

        # The revision content should contain the new data
        self.assertEqual(
            latest_revision.content["text"],
            "Draft-enabled Bar, Now Published",
        )

    def test_publish_then_save_draft(self):
        publish_timestamp = now()
        with freeze_time(publish_timestamp):
            self.test_snippet.text = "Draft-enabled Bar, Published"
            self.test_snippet.save_revision().publish()

        save_timestamp = now()
        with freeze_time(save_timestamp):
            response = self.post(
                post_data={"text": "Draft-enabled Bar, Published and In Draft"}
            )

        self.test_snippet.refresh_from_db()
        revisions = Revision.objects.for_instance(self.test_snippet).order_by("pk")
        latest_revision = self.test_snippet.latest_revision

        self.assertRedirects(
            response,
            reverse("wagtailsnippets_tests_draftstatecustomprimarykeymodel:list"),
        )

        # The instance should be updated with the last published changes
        self.assertEqual(self.test_snippet.text, "Draft-enabled Bar, Published")

        # The instance should be live
        self.assertTrue(self.test_snippet.live)
        # The instance should have unpublished changes
        self.assertTrue(self.test_snippet.has_unpublished_changes)

        self.assertEqual(self.test_snippet.first_published_at, publish_timestamp)
        self.assertEqual(self.test_snippet.last_published_at, publish_timestamp)

        # The live revision should be the first revision
        self.assertEqual(self.test_snippet.live_revision, revisions.first())

        # The second revision should be created and set as latest_revision
        self.assertEqual(revisions.count(), 2)
        self.assertEqual(latest_revision, revisions.last())

        # The revision content should contain the new data
        self.assertEqual(
            latest_revision.content["text"],
            "Draft-enabled Bar, Published and In Draft",
        )

    def test_publish_twice(self):
        first_timestamp = now()
        with freeze_time(first_timestamp):
            self.test_snippet.text = "Draft-enabled Bar, Published Once"
            self.test_snippet.save_revision().publish()

        second_timestamp = now() + datetime.timedelta(days=1)
        with freeze_time(second_timestamp):
            response = self.post(
                post_data={
                    "text": "Draft-enabled Bar, Published Twice",
                    "action-publish": "action-publish",
                }
            )

        self.test_snippet.refresh_from_db()

        revisions = Revision.objects.for_instance(self.test_snippet).order_by("pk")
        latest_revision = self.test_snippet.latest_revision

        self.assertRedirects(
            response,
            reverse("wagtailsnippets_tests_draftstatecustomprimarykeymodel:list"),
        )

        # The instance should be updated with the last published changes
        self.assertEqual(self.test_snippet.text, "Draft-enabled Bar, Published Twice")

        # The instance should be live
        self.assertTrue(self.test_snippet.live)
        self.assertFalse(self.test_snippet.has_unpublished_changes)

        # The first_published_at and last_published_at should be set correctly
        self.assertEqual(self.test_snippet.first_published_at, first_timestamp)
        self.assertEqual(self.test_snippet.last_published_at, second_timestamp)

        # The live revision should be the second revision
        self.assertEqual(self.test_snippet.live_revision, revisions.last())

        # The second revision should be created and set as latest_revision
        self.assertEqual(revisions.count(), 2)
        self.assertEqual(latest_revision, revisions.last())

        # The revision content should contain the new data
        self.assertEqual(
            latest_revision.content["text"],
            "Draft-enabled Bar, Published Twice",
        )

    def test_get_after_save_draft(self):
        self.post(post_data={"text": "Draft-enabled Bar"})
        response = self.get()

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailsnippets/snippets/edit.html")

        # Should not show the Live status
        self.assertNotContains(
            response,
            '<h3 id="status-sidebar-live" class="w-label-1 !w-mt-0 w-mb-1"><span class="w-sr-only">Status: </span>Live</h3>',
            html=True,
        )
        # Should show the Draft status
        self.assertContains(
            response,
            '<h3 id="status-sidebar-draft" class="w-label-1 !w-mt-0 w-mb-1"><span class="w-sr-only">Status: </span>Draft</h3>',
            html=True,
        )

        # Should not show the Unpublish action menu item
        unpublish_url = reverse(
            "wagtailsnippets_tests_draftstatecustomprimarykeymodel:unpublish",
            args=(quote(self.test_snippet.pk),),
        )
        self.assertNotContains(
            response,
            f'<a class="button action-secondary" href="{unpublish_url}">',
        )
        self.assertNotContains(response, "Unpublish")

    def test_get_after_publish(self):
        self.post(
            post_data={
                "text": "Draft-enabled Bar, Published",
                "action-publish": "action-publish",
            }
        )
        response = self.get()

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailsnippets/snippets/edit.html")

        # Should show the Live status
        self.assertContains(
            response,
            '<h3 id="status-sidebar-live" class="w-label-1 !w-mt-0 w-mb-1"><span class="w-sr-only">Status: </span>Live</h3>',
            html=True,
        )
        # Should not show the Draft status
        self.assertNotContains(
            response,
            '<h3 id="status-sidebar-draft" class="w-label-1 !w-mt-0 w-mb-1"><span class="w-sr-only">Status: </span>Draft</h3>',
            html=True,
        )

        # Should show the Unpublish action menu item
        unpublish_url = reverse(
            "wagtailsnippets_tests_draftstatecustomprimarykeymodel:unpublish",
            args=(quote(self.test_snippet.pk),),
        )
        self.assertContains(
            response,
            f'<a class="button action-secondary" href="{unpublish_url}">',
        )
        self.assertContains(response, "Unpublish")

    def test_get_after_publish_and_save_draft(self):
        self.post(
            post_data={
                "text": "Draft-enabled Bar, Published",
                "action-publish": "action-publish",
            }
        )
        self.post(post_data={"text": "Draft-enabled Bar, In Draft"})
        response = self.get()
        html = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailsnippets/snippets/edit.html")

        # Should show the Live status
        self.assertContains(
            response,
            '<h3 id="status-sidebar-live" class="w-label-1 !w-mt-0 w-mb-1"><span class="w-sr-only">Status: </span>Live</h3>',
            html=True,
        )
        # Should show the Draft status
        self.assertContains(
            response,
            '<h3 id="status-sidebar-draft" class="w-label-1 !w-mt-0 w-mb-1"><span class="w-sr-only">Status: </span>Draft</h3>',
            html=True,
        )

        # Should show the Unpublish action menu item
        unpublish_url = reverse(
            "wagtailsnippets_tests_draftstatecustomprimarykeymodel:unpublish",
            args=(quote(self.test_snippet.pk),),
        )
        self.assertContains(
            response,
            f'<a class="button action-secondary" href="{unpublish_url}">',
        )
        self.assertContains(response, "Unpublish")

        # Should use the latest draft content for the title
        self.assertContains(
            response,
            '<h1 class="w-header__title" id="header-title"><svg class="icon icon-snippet w-header__glyph" aria-hidden="true"><use href="#icon-snippet"></use></svg>Draft-enabled Bar, In Draft</h1>',
            html=True,
        )

        # Should use the latest draft content for the form
        self.assertTagInHTML(
            '<textarea name="text">Draft-enabled Bar, In Draft</textarea>',
            html,
            allow_extra_attrs=True,
        )

    def test_edit_post_scheduled(self):
        self.test_snippet.save_revision().publish()

        # put go_live_at and expire_at several days away from the current date, to avoid
        # false matches in content__ tests
        go_live_at = now() + datetime.timedelta(days=10)
        expire_at = now() + datetime.timedelta(days=20)
        response = self.post(
            post_data={
                "text": "Some content",
                "go_live_at": submittable_timestamp(go_live_at),
                "expire_at": submittable_timestamp(expire_at),
            }
        )

        # Should be redirected to the listing page
        self.assertEqual(response.status_code, 302)

        self.test_snippet.refresh_from_db()

        # The object will still be live
        self.assertTrue(self.test_snippet.live)

        # A revision with approved_go_live_at should not exist
        self.assertFalse(
            Revision.objects.for_instance(self.test_snippet)
            .exclude(approved_go_live_at__isnull=True)
            .exists()
        )

        # But a revision with go_live_at and expire_at in their content json *should* exist
        self.assertTrue(
            Revision.objects.for_instance(self.test_snippet)
            .filter(
                content__go_live_at__startswith=str(go_live_at.date()),
            )
            .exists()
        )
        self.assertTrue(
            Revision.objects.for_instance(self.test_snippet)
            .filter(
                content__expire_at__startswith=str(expire_at.date()),
            )
            .exists()
        )

        # Get the edit page again
        response = self.get()

        # Should show the draft go_live_at and expire_at under the "Once published" label
        self.assertContains(
            response,
            '<div class="w-label-3">Once published:</div>',
            html=True,
            count=1,
        )
        self.assertContains(
            response,
            f'<span class="w-text-primary">Go-live:</span> {rendered_timestamp(go_live_at)}',
            html=True,
            count=1,
        )
        self.assertContains(
            response,
            f'<span class="w-text-primary">Expiry:</span> {rendered_timestamp(expire_at)}',
            html=True,
            count=1,
        )

        # Should show the "Edit schedule" button
        html = response.content.decode()
        self.assertTagInHTML(
            '<button type="button" data-a11y-dialog-show="schedule-publishing-dialog">Edit schedule</button>',
            html,
            count=1,
            allow_extra_attrs=True,
        )

        # Should show the dialog template pointing to the [data-edit-form] selector as the root
        self.assertTagInHTML(
            '<div id="schedule-publishing-dialog" class="w-dialog publishing" data-dialog-root-selector="[data-edit-form]">',
            html,
            count=1,
            allow_extra_attrs=True,
        )

    def test_edit_scheduled_go_live_before_expiry(self):
        response = self.post(
            post_data={
                "text": "Some content",
                "go_live_at": submittable_timestamp(now() + datetime.timedelta(days=2)),
                "expire_at": submittable_timestamp(now() + datetime.timedelta(days=1)),
            }
        )

        self.assertEqual(response.status_code, 200)

        # Check that a form error was raised
        self.assertFormError(
            response,
            "form",
            "go_live_at",
            "Go live date/time must be before expiry date/time",
        )
        self.assertFormError(
            response,
            "form",
            "expire_at",
            "Go live date/time must be before expiry date/time",
        )

    def test_edit_scheduled_expire_in_the_past(self):
        response = self.post(
            post_data={
                "text": "Some content",
                "expire_at": submittable_timestamp(now() + datetime.timedelta(days=-1)),
            }
        )

        self.assertEqual(response.status_code, 200)

        # Check that a form error was raised
        self.assertFormError(
            response, "form", "expire_at", "Expiry date/time must be in the future"
        )

    def test_first_published_at_editable(self):
        """Test that we can update the first_published_at via the edit form,
        for models that expose it."""

        self.test_snippet.save_revision().publish()
        self.test_snippet.refresh_from_db()

        initial_delta = self.test_snippet.first_published_at - now()

        first_published_at = now() - datetime.timedelta(days=2)

        self.post(
            post_data={
                "text": "I've been edited!",
                "action-publish": "action-publish",
                "first_published_at": submittable_timestamp(first_published_at),
            }
        )

        self.test_snippet.refresh_from_db()

        # first_published_at should have changed.
        new_delta = self.test_snippet.first_published_at - now()
        self.assertNotEqual(new_delta.days, initial_delta.days)
        # first_published_at should be 3 days ago.
        self.assertEqual(new_delta.days, -3)

    def test_edit_post_publish_scheduled_unpublished(self):
        go_live_at = now() + datetime.timedelta(days=1)
        expire_at = now() + datetime.timedelta(days=2)
        response = self.post(
            post_data={
                "text": "Some content",
                "action-publish": "Publish",
                "go_live_at": submittable_timestamp(go_live_at),
                "expire_at": submittable_timestamp(expire_at),
            }
        )

        # Should be redirected to the listing page
        self.assertEqual(response.status_code, 302)

        self.test_snippet.refresh_from_db()

        # The object should not be live
        self.assertFalse(self.test_snippet.live)

        # Instead a revision with approved_go_live_at should now exist
        self.assertTrue(
            Revision.objects.for_instance(self.test_snippet)
            .exclude(approved_go_live_at__isnull=True)
            .exists()
        )

        # The object SHOULD have the "has_unpublished_changes" flag set,
        # because the changes are not visible as a live object yet
        self.assertTrue(
            self.test_snippet.has_unpublished_changes,
            "An object scheduled for future publishing should have has_unpublished_changes=True",
        )

        self.assertEqual(self.test_snippet.status_string, "scheduled")

        response = self.get()

        # Should show the go_live_at and expire_at without the "Once published" label
        self.assertNotContains(
            response,
            '<div class="w-label-3">Once published:</div>',
            html=True,
        )
        self.assertContains(
            response,
            f'<span class="w-text-primary">Go-live:</span> {rendered_timestamp(go_live_at)}',
            html=True,
            count=1,
        )
        self.assertContains(
            response,
            f'<span class="w-text-primary">Expiry:</span> {rendered_timestamp(expire_at)}',
            html=True,
            count=1,
        )

        # Should still show the "Edit schedule" button
        html = response.content.decode()
        self.assertTagInHTML(
            '<button type="button" data-a11y-dialog-show="schedule-publishing-dialog">Edit schedule</button>',
            html,
            count=1,
            allow_extra_attrs=True,
        )

        # Should show the dialog template pointing to the [data-edit-form] selector as the root
        self.assertTagInHTML(
            '<div id="schedule-publishing-dialog" class="w-dialog publishing" data-dialog-root-selector="[data-edit-form]">',
            html,
            count=1,
            allow_extra_attrs=True,
        )

    def test_edit_post_publish_now_an_already_scheduled_unpublished(self):
        # First let's publish an object with a go_live_at in the future
        go_live_at = now() + datetime.timedelta(days=1)
        expire_at = now() + datetime.timedelta(days=2)
        response = self.post(
            post_data={
                "text": "Some content",
                "action-publish": "Publish",
                "go_live_at": submittable_timestamp(go_live_at),
                "expire_at": submittable_timestamp(expire_at),
            }
        )

        # Should be redirected to the listing page
        self.assertEqual(response.status_code, 302)

        self.test_snippet.refresh_from_db()

        # The object should not be live
        self.assertFalse(self.test_snippet.live)

        self.assertEqual(self.test_snippet.status_string, "scheduled")

        # Instead a revision with approved_go_live_at should now exist
        self.assertTrue(
            Revision.objects.for_instance(self.test_snippet)
            .exclude(approved_go_live_at__isnull=True)
            .exists()
        )

        # Now, let's edit it and publish it right now
        response = self.post(
            post_data={
                "text": "Some content",
                "action-publish": "Publish",
                "go_live_at": "",
            }
        )

        # Should be redirected to the listing page
        self.assertEqual(response.status_code, 302)

        self.test_snippet.refresh_from_db()

        # The object should be live
        self.assertTrue(self.test_snippet.live)

        # The revision with approved_go_live_at should no longer exist
        self.assertFalse(
            Revision.objects.for_instance(self.test_snippet)
            .exclude(approved_go_live_at__isnull=True)
            .exists()
        )

        response = self.get()

        # Should show the "Edit schedule" button
        html = response.content.decode()
        self.assertTagInHTML(
            '<button type="button" data-a11y-dialog-show="schedule-publishing-dialog">Edit schedule</button>',
            html,
            count=1,
            allow_extra_attrs=True,
        )

        # Should show the dialog template pointing to the [data-edit-form] selector as the root
        self.assertTagInHTML(
            '<div id="schedule-publishing-dialog" class="w-dialog publishing" data-dialog-root-selector="[data-edit-form]">',
            html,
            count=1,
            allow_extra_attrs=True,
        )

    def test_edit_post_publish_scheduled_published(self):
        self.test_snippet.save_revision().publish()
        self.test_snippet.refresh_from_db()

        live_revision = self.test_snippet.live_revision

        go_live_at = now() + datetime.timedelta(days=1)
        expire_at = now() + datetime.timedelta(days=2)
        response = self.post(
            post_data={
                "text": "I've been edited!",
                "action-publish": "Publish",
                "go_live_at": submittable_timestamp(go_live_at),
                "expire_at": submittable_timestamp(expire_at),
            }
        )

        # Should be redirected to the listing page
        self.assertEqual(response.status_code, 302)

        self.test_snippet = DraftStateCustomPrimaryKeyModel.objects.get(
            pk=self.test_snippet.pk
        )

        # The object should still be live
        self.assertTrue(self.test_snippet.live)

        self.assertEqual(self.test_snippet.status_string, "live + scheduled")

        # A revision with approved_go_live_at should now exist
        self.assertTrue(
            Revision.objects.for_instance(self.test_snippet)
            .exclude(approved_go_live_at__isnull=True)
            .exists()
        )

        # The object SHOULD have the "has_unpublished_changes" flag set,
        # because the changes are not visible as a live object yet
        self.assertTrue(
            self.test_snippet.has_unpublished_changes,
            "An object scheduled for future publishing should have has_unpublished_changes=True",
        )

        self.assertNotEqual(
            self.test_snippet.get_latest_revision(),
            live_revision,
            "An object scheduled for future publishing should have a new revision, that is not the live revision",
        )

        self.assertEqual(
            self.test_snippet.text,
            "Draft-enabled Foo",
            "A live object with a scheduled revision should still have the original content",
        )

        response = self.get()

        # Should show the go_live_at and expire_at without the "Once published" label
        self.assertNotContains(
            response,
            '<div class="w-label-3">Once published:</div>',
            html=True,
        )
        self.assertContains(
            response,
            f'<span class="w-text-primary">Go-live:</span> {rendered_timestamp(go_live_at)}',
            html=True,
            count=1,
        )
        self.assertContains(
            response,
            f'<span class="w-text-primary">Expiry:</span> {rendered_timestamp(expire_at)}',
            html=True,
            count=1,
        )

        # Should still show the "Edit schedule" button
        html = response.content.decode()
        self.assertTagInHTML(
            '<button type="button" data-a11y-dialog-show="schedule-publishing-dialog">Edit schedule</button>',
            html,
            count=1,
            allow_extra_attrs=True,
        )

        # Should show the dialog template pointing to the [data-edit-form] selector as the root
        self.assertTagInHTML(
            '<div id="schedule-publishing-dialog" class="w-dialog publishing" data-dialog-root-selector="[data-edit-form]">',
            html,
            count=1,
            allow_extra_attrs=True,
        )

    def test_edit_post_publish_now_an_already_scheduled_published(self):
        self.test_snippet.save_revision().publish()

        # First let's publish an object with a go_live_at in the future
        go_live_at = now() + datetime.timedelta(days=1)
        expire_at = now() + datetime.timedelta(days=2)
        response = self.post(
            post_data={
                "text": "Some content",
                "action-publish": "Publish",
                "go_live_at": submittable_timestamp(go_live_at),
                "expire_at": submittable_timestamp(expire_at),
            }
        )

        # Should be redirected to the listing page
        self.assertEqual(response.status_code, 302)

        self.test_snippet.refresh_from_db()

        # The object should still be live
        self.assertTrue(self.test_snippet.live)

        # A revision with approved_go_live_at should now exist
        self.assertTrue(
            Revision.objects.for_instance(self.test_snippet)
            .exclude(approved_go_live_at__isnull=True)
            .exists()
        )

        self.assertEqual(
            self.test_snippet.text,
            "Draft-enabled Foo",
            "A live object with scheduled revisions should still have original content",
        )

        # Now, let's edit it and publish it right now
        response = self.post(
            post_data={
                "text": "I've been updated!",
                "action-publish": "Publish",
                "go_live_at": "",
            }
        )

        # Should be redirected to the listing page
        self.assertEqual(response.status_code, 302)

        self.test_snippet.refresh_from_db()

        # The object should be live
        self.assertTrue(self.test_snippet.live)

        # The scheduled revision should no longer exist
        self.assertFalse(
            Revision.objects.for_instance(self.test_snippet)
            .exclude(approved_go_live_at__isnull=True)
            .exists()
        )

        # The content should be updated
        self.assertEqual(self.test_snippet.text, "I've been updated!")

    def test_edit_post_save_schedule_before_a_scheduled_expire(self):
        # First let's publish an object with *just* an expire_at in the future
        expire_at = now() + datetime.timedelta(days=20)
        response = self.post(
            post_data={
                "text": "Some content",
                "action-publish": "Publish",
                "expire_at": submittable_timestamp(expire_at),
            }
        )

        # Should be redirected to the listing page
        self.assertEqual(response.status_code, 302)

        self.test_snippet.refresh_from_db()

        # The object should still be live
        self.assertTrue(self.test_snippet.live)

        self.assertEqual(self.test_snippet.status_string, "live")

        # The live object should have the expire_at field set
        self.assertEqual(
            self.test_snippet.expire_at,
            expire_at.replace(second=0, microsecond=0),
        )

        # Now, let's save an object with a go_live_at in the future,
        # but before the existing expire_at
        go_live_at = now() + datetime.timedelta(days=10)
        new_expire_at = now() + datetime.timedelta(days=15)
        response = self.post(
            post_data={
                "text": "Some content",
                "go_live_at": submittable_timestamp(go_live_at),
                "expire_at": submittable_timestamp(new_expire_at),
            }
        )

        # Should be redirected to the listing page
        self.assertEqual(response.status_code, 302)

        self.test_snippet.refresh_from_db()

        # The object will still be live
        self.assertTrue(self.test_snippet.live)

        # A revision with approved_go_live_at should not exist
        self.assertFalse(
            Revision.objects.for_instance(self.test_snippet)
            .exclude(approved_go_live_at__isnull=True)
            .exists()
        )

        # But a revision with go_live_at and expire_at in their content json *should* exist
        self.assertTrue(
            Revision.objects.for_instance(self.test_snippet)
            .filter(content__go_live_at__startswith=str(go_live_at.date()))
            .exists()
        )
        self.assertTrue(
            Revision.objects.for_instance(self.test_snippet)
            .filter(content__expire_at__startswith=str(expire_at.date()))
            .exists()
        )

        response = self.get()

        # Should still show the active expire_at in the live object
        self.assertContains(
            response,
            f'<span class="w-text-primary">Expiry:</span> {rendered_timestamp(expire_at)}',
            html=True,
            count=1,
        )

        # Should also show the draft go_live_at and expire_at under the "Once published" label
        self.assertContains(
            response,
            '<div class="w-label-3">Once published:</div>',
            html=True,
            count=1,
        )
        self.assertContains(
            response,
            f'<span class="w-text-primary">Go-live:</span> {rendered_timestamp(go_live_at)}',
            html=True,
            count=1,
        )
        self.assertContains(
            response,
            f'<span class="w-text-primary">Expiry:</span> {rendered_timestamp(new_expire_at)}',
            html=True,
            count=1,
        )

        # Should still show the "Edit schedule" button
        html = response.content.decode()
        self.assertTagInHTML(
            '<button type="button" data-a11y-dialog-show="schedule-publishing-dialog">Edit schedule</button>',
            html,
            count=1,
            allow_extra_attrs=True,
        )

        # Should show the dialog template pointing to the [data-edit-form] selector as the root
        self.assertTagInHTML(
            '<div id="schedule-publishing-dialog" class="w-dialog publishing" data-dialog-root-selector="[data-edit-form]">',
            html,
            count=1,
            allow_extra_attrs=True,
        )

    def test_edit_post_publish_schedule_before_a_scheduled_expire(self):
        # First let's publish an object with *just* an expire_at in the future
        expire_at = now() + datetime.timedelta(days=20)
        response = self.post(
            post_data={
                "text": "Some content",
                "action-publish": "Publish",
                "expire_at": submittable_timestamp(expire_at),
            }
        )

        # Should be redirected to the listing page
        self.assertEqual(response.status_code, 302)

        self.test_snippet.refresh_from_db()

        # The object should still be live
        self.assertTrue(self.test_snippet.live)

        self.assertEqual(self.test_snippet.status_string, "live")

        # The live object should have the expire_at field set
        self.assertEqual(
            self.test_snippet.expire_at,
            expire_at.replace(second=0, microsecond=0),
        )

        # Now, let's publish an object with a go_live_at in the future,
        # but before the existing expire_at
        go_live_at = now() + datetime.timedelta(days=10)
        new_expire_at = now() + datetime.timedelta(days=15)
        response = self.post(
            post_data={
                "text": "Some content",
                "action-publish": "Publish",
                "go_live_at": submittable_timestamp(go_live_at),
                "expire_at": submittable_timestamp(new_expire_at),
            }
        )

        # Should be redirected to the listing page
        self.assertEqual(response.status_code, 302)

        self.test_snippet = DraftStateCustomPrimaryKeyModel.objects.get(
            pk=self.test_snippet.pk
        )

        # The object should still be live
        self.assertTrue(self.test_snippet.live)

        self.assertEqual(self.test_snippet.status_string, "live + scheduled")

        # A revision with approved_go_live_at should now exist
        self.assertTrue(
            Revision.objects.for_instance(self.test_snippet)
            .exclude(approved_go_live_at__isnull=True)
            .exists()
        )

        response = self.get()

        # Should not show the active expire_at in the live object because the
        # scheduled revision is before the existing expire_at, which means it will
        # override the existing expire_at when it goes live
        self.assertNotContains(
            response,
            f'<span class="w-text-primary">Expiry:</span> {rendered_timestamp(expire_at)}',
            html=True,
        )

        # Should show the go_live_at and expire_at without the "Once published" label
        self.assertNotContains(
            response,
            '<div class="w-label-3">Once published:</div>',
            html=True,
        )
        self.assertContains(
            response,
            f'<span class="w-text-primary">Go-live:</span> {rendered_timestamp(go_live_at)}',
            html=True,
            count=1,
        )
        self.assertContains(
            response,
            f'<span class="w-text-primary">Expiry:</span> {rendered_timestamp(new_expire_at)}',
            html=True,
            count=1,
        )

        # Should still show the "Edit schedule" button
        html = response.content.decode()
        self.assertTagInHTML(
            '<button type="button" data-a11y-dialog-show="schedule-publishing-dialog">Edit schedule</button>',
            html,
            count=1,
            allow_extra_attrs=True,
        )

        # Should show the dialog template pointing to the [data-edit-form] selector as the root
        self.assertTagInHTML(
            '<div id="schedule-publishing-dialog" class="w-dialog publishing" data-dialog-root-selector="[data-edit-form]">',
            html,
            count=1,
            allow_extra_attrs=True,
        )

    def test_edit_post_publish_schedule_after_a_scheduled_expire(self):
        # First let's publish an object with *just* an expire_at in the future
        expire_at = now() + datetime.timedelta(days=20)
        response = self.post(
            post_data={
                "text": "Some content",
                "action-publish": "Publish",
                "expire_at": submittable_timestamp(expire_at),
            }
        )

        # Should be redirected to the listing page
        self.assertEqual(response.status_code, 302)

        self.test_snippet.refresh_from_db()

        # The object should still be live
        self.assertTrue(self.test_snippet.live)

        self.assertEqual(self.test_snippet.status_string, "live")

        # The live object should have the expire_at field set
        self.assertEqual(
            self.test_snippet.expire_at,
            expire_at.replace(second=0, microsecond=0),
        )

        # Now, let's publish an object with a go_live_at in the future,
        # but after the existing expire_at
        go_live_at = now() + datetime.timedelta(days=23)
        new_expire_at = now() + datetime.timedelta(days=25)
        response = self.post(
            post_data={
                "text": "Some content",
                "action-publish": "Publish",
                "go_live_at": submittable_timestamp(go_live_at),
                "expire_at": submittable_timestamp(new_expire_at),
            }
        )

        # Should be redirected to the listing page
        self.assertEqual(response.status_code, 302)

        self.test_snippet = DraftStateCustomPrimaryKeyModel.objects.get(
            pk=self.test_snippet.pk
        )

        # The object should still be live
        self.assertTrue(self.test_snippet.live)

        self.assertEqual(self.test_snippet.status_string, "live + scheduled")

        # Instead a revision with approved_go_live_at should now exist
        self.assertTrue(
            Revision.objects.for_instance(self.test_snippet)
            .exclude(approved_go_live_at__isnull=True)
            .exists()
        )

        response = self.get()

        # Should still show the active expire_at in the live object because the
        # scheduled revision is after the existing expire_at, which means the
        # new expire_at won't take effect until the revision goes live.
        # This means the object will be:
        # unpublished (expired) -> published (scheduled) -> unpublished (expired again)
        self.assertContains(
            response,
            f'<span class="w-text-primary">Expiry:</span> {rendered_timestamp(expire_at)}',
            html=True,
            count=1,
        )

        # Should show the go_live_at and expire_at without the "Once published" label
        self.assertNotContains(
            response,
            '<div class="w-label-3">Once published:</div>',
            html=True,
        )
        self.assertContains(
            response,
            f'<span class="w-text-primary">Go-live:</span> {rendered_timestamp(go_live_at)}',
            html=True,
            count=1,
        )
        self.assertContains(
            response,
            f'<span class="w-text-primary">Expiry:</span> {rendered_timestamp(new_expire_at)}',
            html=True,
            count=1,
        )

        # Should still show the "Edit schedule" button
        html = response.content.decode()
        self.assertTagInHTML(
            '<button type="button" data-a11y-dialog-show="schedule-publishing-dialog">Edit schedule</button>',
            html,
            count=1,
            allow_extra_attrs=True,
        )

        # Should show the dialog template pointing to the [data-edit-form] selector as the root
        self.assertTagInHTML(
            '<div id="schedule-publishing-dialog" class="w-dialog publishing" data-dialog-root-selector="[data-edit-form]">',
            html,
            count=1,
            allow_extra_attrs=True,
        )


class TestSnippetUnpublish(TestCase, WagtailTestUtils):
    def setUp(self):
        self.user = self.login()
        self.snippet = DraftStateCustomPrimaryKeyModel.objects.create(
            custom_id="custom/1", text="to be unpublished"
        )
        self.unpublish_url = reverse(
            "wagtailsnippets_tests_draftstatecustomprimarykeymodel:unpublish",
            args=(quote(self.snippet.pk),),
        )

    def test_unpublish_view(self):
        """
        This tests that the unpublish view responds with an unpublish confirm page
        """
        # Get unpublish page
        response = self.client.get(self.unpublish_url)

        # Check that the user received an unpublish confirm page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/shared/confirm_unpublish.html")

    def test_unpublish_view_invalid_pk(self):
        """
        This tests that the unpublish view returns an error if the object pk is invalid
        """
        # Get unpublish page
        response = self.client.get(
            reverse(
                "wagtailsnippets_tests_draftstatecustomprimarykeymodel:unpublish",
                args=(quote(12345),),
            )
        )

        # Check that the user received a 404 response
        self.assertEqual(response.status_code, 404)

    def test_unpublish_view_bad_permissions(self):
        """
        This tests that the unpublish view doesn't allow users without unpublish permissions
        """
        # Remove privileges from user
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            )
        )
        self.user.save()

        # Get unpublish page
        response = self.client.get(self.unpublish_url)

        # Check that the user received a 302 redirected response
        self.assertEqual(response.status_code, 302)

    def test_unpublish_view_post(self):
        """
        This posts to the unpublish view and checks that the object was unpublished
        """
        # Connect a mock signal handler to unpublished signal
        mock_handler = mock.MagicMock()
        unpublished.connect(mock_handler)

        # Post to the unpublish view
        response = self.client.post(self.unpublish_url)

        # Should be redirected to the listing page
        self.assertRedirects(
            response,
            reverse("wagtailsnippets_tests_draftstatecustomprimarykeymodel:list"),
        )

        # Check that the object was unpublished
        self.assertFalse(
            DraftStateCustomPrimaryKeyModel.objects.get(pk=self.snippet.pk).live
        )

        # Check that the unpublished signal was fired
        self.assertEqual(mock_handler.call_count, 1)
        mock_call = mock_handler.mock_calls[0][2]

        self.assertEqual(mock_call["sender"], DraftStateCustomPrimaryKeyModel)
        self.assertEqual(mock_call["instance"], self.snippet)
        self.assertIsInstance(mock_call["instance"], DraftStateCustomPrimaryKeyModel)

    def test_after_unpublish_hook(self):
        def hook_func(request, snippet):
            self.assertIsInstance(request, HttpRequest)
            self.assertEqual(snippet.pk, self.snippet.pk)

            return HttpResponse("Overridden!")

        with self.register_hook("after_unpublish", hook_func):
            post_data = {}
            response = self.client.post(self.unpublish_url, post_data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")

        self.snippet.refresh_from_db()
        self.assertEqual(self.snippet.status_string, "draft")

    def test_before_unpublish(self):
        def hook_func(request, snippet):
            self.assertIsInstance(request, HttpRequest)
            self.assertEqual(snippet.pk, self.snippet.pk)

            return HttpResponse("Overridden!")

        with self.register_hook("before_unpublish", hook_func):
            post_data = {}
            response = self.client.post(self.unpublish_url, post_data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")

        # The hook response is served before unpublish is called.
        self.snippet.refresh_from_db()
        self.assertEqual(self.snippet.status_string, "live")


class TestSnippetDelete(TestCase, WagtailTestUtils):
    fixtures = ["test.json"]

    def setUp(self):
        self.test_snippet = Advert.objects.get(pk=1)
        self.user = self.login()

    def test_delete_get_with_limited_permissions(self):
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            )
        )
        self.user.save()

        response = self.client.get(
            reverse(
                "wagtailsnippets_tests_advert:delete",
                args=[quote(self.test_snippet.pk)],
            )
        )
        self.assertEqual(response.status_code, 302)

    def test_delete_get(self):
        response = self.client.get(
            reverse(
                "wagtailsnippets_tests_advert:delete",
                args=[quote(self.test_snippet.pk)],
            )
        )
        self.assertEqual(response.status_code, 200)

    @override_settings(WAGTAIL_I18N_ENABLED=True)
    def test_delete_get_with_i18n_enabled(self):
        response = self.client.get(
            reverse(
                "wagtailsnippets_tests_advert:delete",
                args=[quote(self.test_snippet.pk)],
            )
        )
        self.assertEqual(response.status_code, 200)

    def test_delete_post_with_limited_permissions(self):
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            )
        )
        self.user.save()

        response = self.client.post(
            reverse(
                "wagtailsnippets_tests_advert:delete",
                args=[quote(self.test_snippet.pk)],
            )
        )
        self.assertEqual(response.status_code, 302)

    def test_delete_post(self):
        response = self.client.post(
            reverse(
                "wagtailsnippets_tests_advert:delete",
                args=[quote(self.test_snippet.pk)],
            )
        )

        # Should be redirected to the listing page
        self.assertRedirects(response, reverse("wagtailsnippets_tests_advert:list"))

        # Check that the page is gone
        self.assertEqual(Advert.objects.filter(text="test_advert").count(), 0)

    def test_usage_link(self):
        output = StringIO()
        management.call_command("rebuild_references_index", stdout=output)

        response = self.client.get(
            reverse(
                "wagtailsnippets_tests_advert:delete",
                args=[quote(self.test_snippet.pk)],
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "wagtailsnippets/snippets/confirm_delete.html"
        )
        self.assertContains(response, "Used 2 times")
        self.assertContains(response, self.test_snippet.usage_url())

    def test_before_delete_snippet_hook_get(self):
        advert = Advert.objects.create(
            url="http://www.example.com/",
            text="Test hook",
        )

        def hook_func(request, instances):
            self.assertIsInstance(request, HttpRequest)
            self.assertQuerysetEqual(instances, ["<Advert: Test hook>"], transform=repr)
            return HttpResponse("Overridden!")

        with self.register_hook("before_delete_snippet", hook_func):
            response = self.client.get(
                reverse("wagtailsnippets_tests_advert:delete", args=[quote(advert.pk)])
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")

    def test_before_delete_snippet_hook_post(self):
        advert = Advert.objects.create(
            url="http://www.example.com/",
            text="Test hook",
        )

        def hook_func(request, instances):
            self.assertIsInstance(request, HttpRequest)
            self.assertQuerysetEqual(instances, ["<Advert: Test hook>"], transform=repr)
            return HttpResponse("Overridden!")

        with self.register_hook("before_delete_snippet", hook_func):
            response = self.client.post(
                reverse(
                    "wagtailsnippets_tests_advert:delete",
                    args=[quote(advert.pk)],
                )
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")

        # Request intercepted before advert was deleted
        self.assertTrue(Advert.objects.filter(pk=advert.pk).exists())

    def test_after_delete_snippet_hook(self):
        advert = Advert.objects.create(
            url="http://www.example.com/",
            text="Test hook",
        )

        def hook_func(request, instances):
            self.assertIsInstance(request, HttpRequest)
            self.assertQuerysetEqual(instances, ["<Advert: Test hook>"], transform=repr)
            return HttpResponse("Overridden!")

        with self.register_hook("after_delete_snippet", hook_func):
            response = self.client.post(
                reverse(
                    "wagtailsnippets_tests_advert:delete",
                    args=[quote(advert.pk)],
                )
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")

        # Request intercepted after advert was deleted
        self.assertFalse(Advert.objects.filter(pk=advert.pk).exists())


class TestSnippetDeleteMultipleWithOne(TestCase, WagtailTestUtils):
    # test deletion of one snippet using the delete-multiple URL
    # behaviour should mimic the TestSnippetDelete but with different URl structure
    fixtures = ["test.json"]

    def setUp(self):
        self.snippet = Advert.objects.get(id=1)
        self.login()

    def test_delete_get(self):
        url = reverse("wagtailsnippets_tests_advert:delete-multiple")
        url += "?id=%s" % (self.snippet.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_delete_post(self):
        url = reverse("wagtailsnippets_tests_advert:delete-multiple")
        url += "?id=%s" % (self.snippet.id)
        response = self.client.post(url)

        # Should be redirected to the listing page
        self.assertRedirects(response, reverse("wagtailsnippets_tests_advert:list"))

        # Check that the page is gone
        self.assertEqual(Advert.objects.filter(text="test_advert").count(), 0)


class TestSnippetDeleteMultipleWithThree(TestCase, WagtailTestUtils):
    # test deletion of three snippets using the delete-multiple URL
    fixtures = ["test.json"]

    def setUp(self):
        # first advert is in the fixtures
        Advert.objects.create(text="Boreas").save()
        Advert.objects.create(text="Cloud 9").save()
        self.snippets = Advert.objects.all()
        self.login()

    def test_delete_get(self):
        # tests that the URL is available on get
        url = reverse("wagtailsnippets_tests_advert:delete-multiple")
        url += "?id=%s" % (
            "&id=".join(["%s" % snippet.id for snippet in self.snippets])
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_delete_post(self):
        # tests that the URL is available on post and deletes snippets
        url = reverse("wagtailsnippets_tests_advert:delete-multiple")
        url += "?id=%s" % (
            "&id=".join(["%s" % snippet.id for snippet in self.snippets])
        )
        response = self.client.post(url)

        # Should be redirected to the listing page
        self.assertRedirects(response, reverse("wagtailsnippets_tests_advert:list"))

        # Check that the page is gone
        self.assertEqual(Advert.objects.filter(text="test_advert").count(), 0)


class TestSnippetChooserPanel(TestCase, WagtailTestUtils):
    fixtures = ["test.json"]

    def setUp(self):
        self.request = RequestFactory().get("/")
        user = AnonymousUser()  # technically, Anonymous users cannot access the admin
        self.request.user = user

        model = SnippetChooserModel
        self.advert_text = "Test advert text"
        test_snippet = model.objects.create(
            advert=Advert.objects.create(text=self.advert_text)
        )

        self.edit_handler = get_edit_handler(model)
        self.form_class = self.edit_handler.get_form_class()
        form = self.form_class(instance=test_snippet)
        edit_handler = self.edit_handler.get_bound_panel(
            instance=test_snippet, form=form, request=self.request
        )

        self.snippet_chooser_panel = [
            panel
            for panel in edit_handler.children
            if getattr(panel, "field_name", None) == "advert"
        ][0]

    def test_render_html(self):
        field_html = self.snippet_chooser_panel.render_html()
        self.assertIn(self.advert_text, field_html)
        self.assertIn("Choose advert", field_html)
        self.assertIn("Choose another advert", field_html)

    def test_render_as_empty_field(self):
        test_snippet = SnippetChooserModel()
        form = self.form_class(instance=test_snippet)
        edit_handler = self.edit_handler.get_bound_panel(
            instance=test_snippet, form=form, request=self.request
        )

        snippet_chooser_panel = [
            panel
            for panel in edit_handler.children
            if getattr(panel, "field_name", None) == "advert"
        ][0]

        field_html = snippet_chooser_panel.render_html()
        self.assertIn("Choose advert", field_html)
        self.assertIn("Choose another advert", field_html)

    def test_render_js(self):
        self.assertIn(
            'new SnippetChooser("id_advert");',
            self.snippet_chooser_panel.render_html(),
        )

    def test_target_model_autodetected(self):
        edit_handler = ObjectList([FieldPanel("advert")]).bind_to_model(
            SnippetChooserModel
        )
        form_class = edit_handler.get_form_class()
        form = form_class()
        widget = form.fields["advert"].widget
        self.assertIsInstance(widget, AdminSnippetChooser)
        self.assertEqual(widget.model, Advert)


class TestSnippetRegistering(TestCase):
    def test_register_function(self):
        self.assertIn(RegisterFunction, SNIPPET_MODELS)

    def test_register_decorator(self):
        # Misbehaving decorators often return None
        self.assertIsNotNone(RegisterDecorator)
        self.assertIn(RegisterDecorator, SNIPPET_MODELS)


class TestSnippetOrdering(TestCase):
    def setUp(self):
        register_snippet(ZuluSnippet)
        register_snippet(AlphaSnippet)

    def test_snippets_ordering(self):
        # Ensure AlphaSnippet is before ZuluSnippet
        # Cannot check first and last position as other snippets
        # may get registered elsewhere during test
        self.assertLess(
            SNIPPET_MODELS.index(AlphaSnippet), SNIPPET_MODELS.index(ZuluSnippet)
        )


class TestUsageCount(TestCase):
    fixtures = ["test.json"]

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        output = StringIO()
        management.call_command("rebuild_references_index", stdout=output)

    def test_snippet_usage_count(self):
        advert = Advert.objects.get(pk=1)
        self.assertEqual(advert.get_usage().count(), 2)


class TestUsedBy(TestCase):
    fixtures = ["test.json"]

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        output = StringIO()
        management.call_command("rebuild_references_index", stdout=output)

    def test_snippet_used_by(self):
        advert = Advert.objects.get(pk=1)

        self.assertIsInstance(advert.get_usage()[0], tuple)
        self.assertIsInstance(advert.get_usage()[0][0], Page)
        self.assertIsInstance(advert.get_usage()[0][1], list)
        self.assertIsInstance(advert.get_usage()[0][1][0], ReferenceIndex)


class TestSnippetUsageView(TestCase, WagtailTestUtils):
    fixtures = ["test.json"]

    def setUp(self):
        self.user = self.login()

    def test_use_latest_draft_as_title(self):
        snippet = DraftStateModel.objects.create(text="Draft-enabled Foo, Published")
        snippet.save_revision().publish()
        snippet.text = "Draft-enabled Bar, In Draft"
        snippet.save_revision()

        response = self.client.get(
            reverse(
                "wagtailsnippets_tests_draftstatemodel:usage",
                args=[quote(snippet.pk)],
            )
        )

        # Should use the latest draft title in the header subtitle
        self.assertContains(
            response,
            '<span class="w-header__subtitle">Draft-enabled Bar, In Draft</span>',
        )

    def test_usage(self):
        # resave so that usage count gets updated
        page = Page.objects.get(pk=2)
        page.save()

        response = self.client.get(
            reverse(
                "wagtailsnippets_tests_advert:usage",
                args=["1"],
            )
        )
        self.assertContains(response, "Welcome to the Wagtail test site!")

    def test_usage_without_edit_permission_on_snippet(self):
        # Create a user with basic admin backend access
        user = self.create_user(
            username="basicadmin", email="basicadmin@example.com", password="password"
        )
        admin_permission = Permission.objects.get(
            content_type__app_label="wagtailadmin", codename="access_admin"
        )
        user.user_permissions.add(admin_permission)
        self.login(username="basicadmin", password="password")

        response = self.client.get(
            reverse(
                "wagtailsnippets_tests_advert:usage",
                args=["1"],
            )
        )
        self.assertEqual(response.status_code, 302)

    def test_usage_without_edit_permission_on_page(self):
        # resave so that usage count gets updated
        page = Page.objects.get(pk=2)
        page.save()

        # Create a user with edit access to snippets but not pages
        user = self.create_user(
            username="basicadmin", email="basicadmin@example.com", password="password"
        )
        admin_permission = Permission.objects.get(
            content_type__app_label="wagtailadmin", codename="access_admin"
        )
        advert_permission = Permission.objects.get(
            content_type__app_label="tests", codename="change_advert"
        )
        user.user_permissions.add(admin_permission)
        user.user_permissions.add(advert_permission)
        self.login(username="basicadmin", password="password")

        response = self.client.get(
            reverse(
                "wagtailsnippets_tests_advert:usage",
                args=["1"],
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Welcome to the Wagtail test site!")
        self.assertContains(response, "(Private page)")


class TestSnippetHistory(TestCase, WagtailTestUtils):
    fixtures = ["test.json"]

    def get(self, snippet, params={}):
        return self.client.get(self.get_url(snippet, "history"), params)

    def get_url(self, snippet, url_name, args=None):
        app_label = snippet._meta.app_label
        model_name = snippet._meta.model_name
        view_name = f"wagtailsnippets_{app_label}_{model_name}:{url_name}"
        if args is None:
            args = [quote(snippet.pk)]
        return reverse(view_name, args=args)

    def setUp(self):
        self.user = self.login()
        self.non_revisable_snippet = Advert.objects.get(pk=1)
        ModelLogEntry.objects.create(
            content_type=ContentType.objects.get_for_model(Advert),
            label="Test Advert",
            action="wagtail.create",
            timestamp=make_aware(datetime.datetime(2021, 9, 30, 10, 1, 0)),
            object_id="1",
        )
        ModelLogEntry.objects.create(
            content_type=ContentType.objects.get_for_model(Advert),
            label="Test Advert Updated",
            action="wagtail.edit",
            timestamp=make_aware(datetime.datetime(2022, 5, 10, 12, 34, 0)),
            object_id="1",
        )
        self.revisable_snippet = RevisableModel.objects.create(text="Foo")
        self.initial_revision = self.revisable_snippet.save_revision(user=self.user)
        ModelLogEntry.objects.create(
            content_type=ContentType.objects.get_for_model(RevisableModel),
            label="Foo",
            action="wagtail.create",
            timestamp=make_aware(datetime.datetime(2022, 5, 10, 20, 22, 0)),
            object_id=self.revisable_snippet.pk,
            revision=self.initial_revision,
            content_changed=True,
        )
        self.revisable_snippet.text = "Bar"
        self.edit_revision = self.revisable_snippet.save_revision(
            user=self.user, log_action=True
        )

    def test_simple(self):
        response = self.get(self.non_revisable_snippet)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<td class="title">Created</td>', html=True)
        self.assertContains(
            response,
            'data-tippy-content="Sept. 30, 2021, 10:01 a.m."',
        )

    def test_filters(self):
        # Should work on both non-revisable and revisable snippets
        snippets = [self.non_revisable_snippet, self.revisable_snippet]
        for snippet in snippets:
            with self.subTest(snippet=snippet):
                response = self.get(snippet, {"action": "wagtail.edit"})
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "Edited", count=1)
                self.assertNotContains(response, "Created")

    def test_should_not_show_actions_on_non_revisable_snippet(self):
        response = self.get(self.non_revisable_snippet)
        edit_url = self.get_url(self.non_revisable_snippet, "edit")
        self.assertNotContains(
            response,
            f'<a href="{edit_url}" class="button button-small button-secondary">Edit</a>',
        )

    def test_should_show_actions_on_revisable_snippet(self):
        response = self.get(self.revisable_snippet)
        edit_url = self.get_url(self.revisable_snippet, "edit")
        revert_url = self.get_url(
            self.revisable_snippet,
            "revisions_revert",
            args=[self.revisable_snippet.pk, self.initial_revision.pk],
        )

        # Should not show the "live version" or "current draft" status tags
        self.assertNotContains(
            response, '<span class="status-tag primary">Live version</span>'
        )
        self.assertNotContains(
            response, '<span class="status-tag primary">Current draft</span>'
        )

        # The latest revision should have an "Edit" action instead of "Review"
        self.assertContains(
            response,
            f'<a href="{edit_url}" class="button button-small button-secondary">Edit</a>',
            count=1,
        )

        # Any other revision should have a "Review" action
        self.assertContains(
            response,
            f'<a href="{revert_url}" class="button button-small button-secondary">Review this version</a>',
            count=1,
        )

    def test_with_live_and_draft_status(self):
        snippet = DraftStateModel.objects.create(text="Draft-enabled Foo, Published")
        snippet.save_revision().publish()
        snippet.refresh_from_db()

        snippet.text = "Draft-enabled Bar, In Draft"
        snippet.save_revision(log_action=True)

        response = self.get(snippet)

        # Should show the "live version" status tag for the published revision
        self.assertContains(
            response, '<span class="status-tag primary">Live version</span>', count=1
        )

        # Should show the "current draft" status tag for the draft revision
        self.assertContains(
            response, '<span class="status-tag primary">Current draft</span>', count=1
        )

        # Should use the latest draft title in the header subtitle
        self.assertContains(
            response,
            '<span class="w-header__subtitle">Draft-enabled Bar, In Draft</span>',
        )

    @override_settings(WAGTAIL_I18N_ENABLED=True)
    def test_get_with_i18n_enabled(self):
        response = self.get(self.non_revisable_snippet)
        self.assertEqual(response.status_code, 200)


class TestSnippetRevisions(TestCase, WagtailTestUtils):
    @property
    def revert_url(self):
        return self.get_url(
            "revisions_revert", args=[quote(self.snippet.pk), self.initial_revision.pk]
        )

    def get(self):
        return self.client.get(self.revert_url)

    def post(self, post_data={}):
        return self.client.post(self.revert_url, post_data)

    def get_url(self, url_name, args=None):
        app_label = self.snippet._meta.app_label
        model_name = self.snippet._meta.model_name
        view_name = f"wagtailsnippets_{app_label}_{model_name}:{url_name}"
        if args is None:
            args = [quote(self.snippet.pk)]
        return reverse(view_name, args=args)

    def setUp(self):
        self.user = self.login()

        with freeze_time("2022-05-10 11:00:00"):
            self.snippet = RevisableModel.objects.create(text="The original text")
            self.initial_revision = self.snippet.save_revision(user=self.user)
            ModelLogEntry.objects.create(
                content_type=ContentType.objects.get_for_model(RevisableModel),
                label="The original text",
                action="wagtail.create",
                timestamp=now(),
                object_id=self.snippet.pk,
                revision=self.initial_revision,
                content_changed=True,
            )

        self.snippet.text = "The edited text"
        self.snippet.save()
        self.edit_revision = self.snippet.save_revision(user=self.user, log_action=True)

    def test_get_revert_revision(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)

        # Message should be shown
        self.assertContains(
            response,
            "You are viewing a previous version of this Revisable model from <b>10 May 2022 11:00</b> by",
            count=1,
        )

        # Form should show the content of the revision, not the current draft
        self.assertContains(response, "The original text", count=1)

        # Form action url should point to the revisions_revert view
        form_tag = f'<form action="{self.revert_url}" method="POST">'
        html = response.content.decode()
        self.assertTagInHTML(form_tag, html, count=1, allow_extra_attrs=True)

        # Buttons should be relabelled
        self.assertContains(response, "Replace current revision", count=1)

    def test_get_revert_revision_with_non_revisable_snippet(self):
        snippet = Advert.objects.create(text="foo")
        response = self.client.get(
            f"/admin/snippets/tests/advert/history/{snippet.pk}/revisions/1/revert/"
        )
        self.assertEqual(response.status_code, 404)

    def test_get_with_limited_permissions(self):
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            )
        )
        self.user.save()

        response = self.get()
        self.assertEqual(response.status_code, 302)

    def test_get_with_draft_state_snippet(self):
        self.snippet = DraftStateModel.objects.create(text="Draft-enabled Foo")
        self.initial_revision = self.snippet.save_revision()
        response = self.get()

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailsnippets/snippets/edit.html")

        # The save button should be labelled "Replace current draft"
        self.assertContains(response, "Replace current draft")
        # The publish button should exist
        self.assertContains(response, "Publish this version")
        # The publish button should have name="action-publish"
        self.assertContains(
            response,
            '<button type="submit" name="action-publish" value="action-publish" class="button action-save button-longrunning warning" data-clicked-text="Publishing…">',
        )

        # Should not show the Unpublish action menu item
        unpublish_url = reverse(
            "wagtailsnippets_tests_draftstatemodel:unpublish",
            args=(quote(self.snippet.pk),),
        )
        self.assertNotContains(
            response,
            f'<a class="button action-secondary" href="{unpublish_url}">',
        )
        self.assertNotContains(response, "Unpublish")

    def test_replace_revision(self):
        get_response = self.get()
        text_from_revision = get_response.context["form"].initial["text"]

        post_response = self.post(
            post_data={
                "text": text_from_revision + " reverted",
                "revision": self.initial_revision.pk,
            }
        )
        self.assertRedirects(post_response, self.get_url("list", args=[]))

        self.snippet.refresh_from_db()
        latest_revision = self.snippet.get_latest_revision()
        log_entry = ModelLogEntry.objects.filter(revision=latest_revision).first()

        # The instance should be updated
        self.assertEqual(self.snippet.text, "The original text reverted")
        # The initial revision, edited revision, and revert revision
        self.assertEqual(self.snippet.revisions.count(), 3)
        # The latest revision should be the revert revision
        self.assertEqual(latest_revision.content["text"], "The original text reverted")

        # A new log entry with "wagtail.revert" action should be created
        self.assertIsNotNone(log_entry)
        self.assertEqual(log_entry.action, "wagtail.revert")

    def test_replace_with_limited_permissions(self):
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            )
        )
        self.user.save()

        response = self.post(
            post_data={
                "text": "test text",
                "revision": self.initial_revision.pk,
            }
        )
        self.assertEqual(response.status_code, 302)

        self.snippet.refresh_from_db()
        self.assertNotEqual(self.snippet.text, "test text")

        # Only the initial revision and edited revision, no revert revision
        self.assertEqual(self.snippet.revisions.count(), 2)

    def test_replace_draft(self):
        self.snippet = DraftStateModel.objects.create(
            text="Draft-enabled Foo", live=False
        )
        self.initial_revision = self.snippet.save_revision()
        self.snippet.text = "Draft-enabled Foo edited"
        self.edit_revision = self.snippet.save_revision()
        get_response = self.get()
        text_from_revision = get_response.context["form"].initial["text"]

        post_response = self.post(
            post_data={
                "text": text_from_revision + " reverted",
                "revision": self.initial_revision.pk,
            }
        )
        self.assertRedirects(post_response, self.get_url("list", args=[]))

        self.snippet.refresh_from_db()
        latest_revision = self.snippet.get_latest_revision()
        log_entry = ModelLogEntry.objects.filter(revision=latest_revision).first()
        publish_log_entries = ModelLogEntry.objects.filter(
            content_type=ContentType.objects.get_for_model(DraftStateModel),
            action="wagtail.publish",
            object_id=self.snippet.pk,
        )

        # The instance should not be updated
        self.assertEqual(self.snippet.text, "Draft-enabled Foo")
        # The initial revision, edited revision, and revert revision
        self.assertEqual(self.snippet.revisions.count(), 3)
        # The latest revision should be the revert revision
        self.assertEqual(latest_revision.content["text"], "Draft-enabled Foo reverted")

        # A new log entry with "wagtail.revert" action should be created
        self.assertIsNotNone(log_entry)
        self.assertEqual(log_entry.action, "wagtail.revert")

        # There should be no log entries for the publish action
        self.assertEqual(publish_log_entries.count(), 0)

        # The instance should still be a draft
        self.assertFalse(self.snippet.live)
        self.assertTrue(self.snippet.has_unpublished_changes)
        self.assertIsNone(self.snippet.first_published_at)
        self.assertIsNone(self.snippet.last_published_at)
        self.assertIsNone(self.snippet.live_revision)

    def test_replace_publish(self):
        self.snippet = DraftStateModel.objects.create(text="Draft-enabled Foo")
        self.initial_revision = self.snippet.save_revision()
        self.snippet.text = "Draft-enabled Foo edited"
        self.edit_revision = self.snippet.save_revision()
        get_response = self.get()
        text_from_revision = get_response.context["form"].initial["text"]

        timestamp = now()
        with freeze_time(timestamp):
            post_response = self.post(
                post_data={
                    "text": text_from_revision + " reverted",
                    "revision": self.initial_revision.pk,
                    "action-publish": "action-publish",
                }
            )

        self.assertRedirects(post_response, self.get_url("list", args=[]))

        self.snippet.refresh_from_db()
        latest_revision = self.snippet.get_latest_revision()
        log_entry = ModelLogEntry.objects.filter(revision=latest_revision).first()
        revert_log_entries = ModelLogEntry.objects.filter(
            content_type=ContentType.objects.get_for_model(DraftStateModel),
            action="wagtail.revert",
            object_id=self.snippet.pk,
        )

        # The instance should be updated
        self.assertEqual(self.snippet.text, "Draft-enabled Foo reverted")
        # The initial revision, edited revision, and revert revision
        self.assertEqual(self.snippet.revisions.count(), 3)
        # The latest revision should be the revert revision
        self.assertEqual(latest_revision.content["text"], "Draft-enabled Foo reverted")

        # The latest log entry should use the "wagtail.publish" action
        self.assertIsNotNone(log_entry)
        self.assertEqual(log_entry.action, "wagtail.publish")

        # There should be a log entry for the revert action
        self.assertEqual(revert_log_entries.count(), 1)

        # The instance should be live
        self.assertTrue(self.snippet.live)
        self.assertFalse(self.snippet.has_unpublished_changes)
        self.assertEqual(self.snippet.first_published_at, timestamp)
        self.assertEqual(self.snippet.last_published_at, timestamp)
        self.assertEqual(self.snippet.live_revision, self.snippet.latest_revision)


class TestCompareRevisions(TestCase, WagtailTestUtils):
    # Actual tests for the comparison classes can be found in test_compare.py

    def setUp(self):
        self.snippet = RevisableModel.objects.create(text="Initial revision")
        self.initial_revision = self.snippet.save_revision()
        self.initial_revision.created_at = make_aware(datetime.datetime(2022, 5, 10))
        self.initial_revision.save()

        self.snippet.text = "First edit"
        self.edit_revision = self.snippet.save_revision()
        self.edit_revision.created_at = make_aware(datetime.datetime(2022, 5, 11))
        self.edit_revision.save()

        self.snippet.text = "Final revision"
        self.final_revision = self.snippet.save_revision()
        self.final_revision.created_at = make_aware(datetime.datetime(2022, 5, 12))
        self.final_revision.save()

        self.login()

    def get(self, revision_a_id, revision_b_id):
        compare_url = reverse(
            "wagtailsnippets_tests_revisablemodel:revisions_compare",
            args=(quote(self.snippet.pk), revision_a_id, revision_b_id),
        )
        return self.client.get(compare_url)

    def test_compare_revisions(self):
        response = self.get(self.initial_revision.pk, self.edit_revision.pk)
        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response,
            '<span class="deletion">Initial revision</span><span class="addition">First edit</span>',
            html=True,
        )

    def test_compare_revisions_earliest(self):
        response = self.get("earliest", self.edit_revision.pk)
        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response,
            '<span class="deletion">Initial revision</span><span class="addition">First edit</span>',
            html=True,
        )

    def test_compare_revisions_latest(self):
        response = self.get(self.edit_revision.id, "latest")
        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response,
            '<span class="deletion">First edit</span><span class="addition">Final revision</span>',
            html=True,
        )

    def test_compare_revisions_live(self):
        # Mess with the live version, bypassing revisions
        self.snippet.text = "Live edited"
        self.snippet.save(update_fields=["text"])

        response = self.get(self.final_revision.id, "live")
        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response,
            '<span class="deletion">Final revision</span><span class="addition">Live edited</span>',
            html=True,
        )


class TestCompareRevisionsWithPerUserPanels(TestCase, WagtailTestUtils):
    def setUp(self):
        self.snippet = RevisableChildModel.objects.create(
            text="Foo bar", secret_text="Secret text"
        )
        self.old_revision = self.snippet.save_revision()
        self.snippet.text = "Foo baz"
        self.snippet.secret_text = "Secret unseen note"
        self.new_revision = self.snippet.save_revision()
        self.compare_url = reverse(
            "wagtailsnippets_tests_revisablechildmodel:revisions_compare",
            args=(quote(self.snippet.pk), self.old_revision.pk, self.new_revision.pk),
        )

    def test_comparison_as_superuser(self):
        self.login()
        response = self.client.get(self.compare_url)
        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response,
            'Foo <span class="deletion">bar</span><span class="addition">baz</span>',
            html=True,
        )
        self.assertContains(
            response,
            'Secret <span class="deletion">text</span><span class="addition">unseen note</span>',
            html=True,
        )

    def test_comparison_as_ordinary_user(self):
        user = self.create_user(username="editor", password="password")
        add_permission = Permission.objects.get(
            content_type__app_label="tests", codename="change_revisablechildmodel"
        )
        admin_permission = Permission.objects.get(
            content_type__app_label="wagtailadmin", codename="access_admin"
        )
        user.user_permissions.add(add_permission, admin_permission)
        self.login(username="editor", password="password")

        response = self.client.get(self.compare_url)
        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response,
            'Foo <span class="deletion">bar</span><span class="addition">baz</span>',
            html=True,
        )
        self.assertNotContains(response, "unseen note")


class TestSnippetChoose(TestCase, WagtailTestUtils):
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
        self.assertEqual(response.context["items"][0].text, "advert 1")

    def test_simple_pagination(self):

        pages = ["0", "1", "-1", "9999", "Not a page"]
        for page in pages:
            response = self.get({"p": page})
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(
                response, "wagtailadmin/generic/chooser/chooser.html"
            )

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
        self.assertEqual(len(response.context["items"]), 2)
        self.assertEqual(response.context["items"][0].text, "English snippet")
        self.assertEqual(response.context["items"][1].text, "French snippet")

        # Now test with a locale selected
        response = self.get({"locale": "en"})

        self.assertEqual(len(response.context["items"]), 1)
        self.assertEqual(response.context["items"][0].text, "English snippet")


class TestSnippetChooseResults(TestCase, WagtailTestUtils):
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


class TestSnippetChooseStatus(TestCase, WagtailTestUtils):
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
        self.assertTagInHTML('<div class="status-tag ">draft</div>', html)
        self.assertTagInHTML('<div class="status-tag primary">live</div>', html)
        self.assertTagInHTML('<div class="status-tag primary">live + draft</div>', html)

    def test_choose_results_view_shows_status_column(self):
        response = self.get("choose_results")
        self.assertContains(response, "<th>Status</th>", html=True)
        self.assertContains(response, '<div class="status-tag ">draft</div>', html=True)
        self.assertContains(
            response, '<div class="status-tag primary">live</div>', html=True
        )
        self.assertContains(
            response, '<div class="status-tag primary">live + draft</div>', html=True
        )


class TestSnippetChooseWithSearchableSnippet(TestCase, WagtailTestUtils):
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
        items = list(response.context["items"].object_list)
        self.assertIn(self.snippet_a, items)
        self.assertIn(self.snippet_b, items)
        self.assertIn(self.snippet_c, items)

    def test_is_searchable(self):
        # filter_form should have a search field
        self.assertTrue(self.get().context["filter_form"].fields.get("q"))

    def test_search_hello(self):
        response = self.get({"q": "Hello"})

        # Just snippets with "Hello" should be in items
        items = list(response.context["items"].object_list)
        self.assertIn(self.snippet_a, items)
        self.assertNotIn(self.snippet_b, items)
        self.assertIn(self.snippet_c, items)

    def test_search_world(self):
        response = self.get({"q": "World"})

        # Just snippets with "World" should be in items
        items = list(response.context["items"].object_list)
        self.assertNotIn(self.snippet_a, items)
        self.assertIn(self.snippet_b, items)
        self.assertIn(self.snippet_c, items)


class TestSnippetChosen(TestCase, WagtailTestUtils):
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


class TestAddOnlyPermissions(TestCase, WagtailTestUtils):
    fixtures = ["test.json"]

    def setUp(self):
        self.test_snippet = Advert.objects.get(pk=1)

        # Create a user with add_advert permission but not change_advert
        user = self.create_user(
            username="addonly", email="addonly@example.com", password="password"
        )
        add_permission = Permission.objects.get(
            content_type__app_label="tests", codename="add_advert"
        )
        admin_permission = Permission.objects.get(
            content_type__app_label="wagtailadmin", codename="access_admin"
        )
        user.user_permissions.add(add_permission, admin_permission)
        self.login(username="addonly", password="password")

    def test_get_index(self):
        response = self.client.get(reverse("wagtailsnippets_tests_advert:list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailsnippets/snippets/type_index.html")

        # user should get an "Add advert" button
        self.assertContains(response, "Add advert")

    def test_get_add(self):
        response = self.client.get(reverse("wagtailsnippets_tests_advert:add"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailsnippets/snippets/create.html")

    def test_get_edit(self):
        response = self.client.get(
            reverse(
                "wagtailsnippets_tests_advert:edit",
                args=[quote(self.test_snippet.pk)],
            )
        )
        # permission should be denied
        self.assertRedirects(response, reverse("wagtailadmin_home"))

    def test_get_delete(self):
        response = self.client.get(
            reverse(
                "wagtailsnippets_tests_advert:delete",
                args=[quote(self.test_snippet.pk)],
            )
        )
        # permission should be denied
        self.assertRedirects(response, reverse("wagtailadmin_home"))

    def test_get_delete_mulitple(self):
        url = reverse("wagtailsnippets_tests_advert:delete-multiple")
        url += "?id=%s" % self.test_snippet.id
        response = self.client.get(url)
        # permission should be denied
        self.assertRedirects(response, reverse("wagtailadmin_home"))


class TestEditOnlyPermissions(TestCase, WagtailTestUtils):
    fixtures = ["test.json"]

    def setUp(self):
        self.test_snippet = Advert.objects.get(pk=1)

        # Create a user with change_advert permission but not add_advert
        user = self.create_user(
            username="changeonly", email="changeonly@example.com", password="password"
        )
        change_permission = Permission.objects.get(
            content_type__app_label="tests", codename="change_advert"
        )
        admin_permission = Permission.objects.get(
            content_type__app_label="wagtailadmin", codename="access_admin"
        )
        user.user_permissions.add(change_permission, admin_permission)
        self.login(username="changeonly", password="password")

    def test_get_index(self):
        response = self.client.get(reverse("wagtailsnippets_tests_advert:list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailsnippets/snippets/type_index.html")

        # user should not get an "Add advert" button
        self.assertNotContains(response, "Add advert")

    def test_get_add(self):
        response = self.client.get(reverse("wagtailsnippets_tests_advert:add"))
        # permission should be denied
        self.assertRedirects(response, reverse("wagtailadmin_home"))

    def test_get_edit(self):
        response = self.client.get(
            reverse(
                "wagtailsnippets_tests_advert:edit",
                args=[quote(self.test_snippet.pk)],
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailsnippets/snippets/edit.html")

    def test_get_delete(self):
        response = self.client.get(
            reverse(
                "wagtailsnippets_tests_advert:delete",
                args=[quote(self.test_snippet.pk)],
            )
        )
        # permission should be denied
        self.assertRedirects(response, reverse("wagtailadmin_home"))

    def test_get_delete_mulitple(self):
        url = reverse("wagtailsnippets_tests_advert:delete-multiple")
        url += "?id=%s" % self.test_snippet.id
        response = self.client.get(url)
        # permission should be denied
        self.assertRedirects(response, reverse("wagtailadmin_home"))


class TestDeleteOnlyPermissions(TestCase, WagtailTestUtils):
    fixtures = ["test.json"]

    def setUp(self):
        self.test_snippet = Advert.objects.get(pk=1)

        # Create a user with delete_advert permission
        user = self.create_user(username="deleteonly", password="password")
        change_permission = Permission.objects.get(
            content_type__app_label="tests", codename="delete_advert"
        )
        admin_permission = Permission.objects.get(
            content_type__app_label="wagtailadmin", codename="access_admin"
        )
        user.user_permissions.add(change_permission, admin_permission)
        self.login(username="deleteonly", password="password")

    def test_get_index(self):
        response = self.client.get(reverse("wagtailsnippets_tests_advert:list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailsnippets/snippets/type_index.html")

        # user should not get an "Add advert" button
        self.assertNotContains(response, "Add advert")

    def test_get_add(self):
        response = self.client.get(reverse("wagtailsnippets_tests_advert:add"))
        # permission should be denied
        self.assertRedirects(response, reverse("wagtailadmin_home"))

    def test_get_edit(self):
        response = self.client.get(
            reverse(
                "wagtailsnippets_tests_advert:edit",
                args=[quote(self.test_snippet.pk)],
            )
        )
        # permission should be denied
        self.assertRedirects(response, reverse("wagtailadmin_home"))

    def test_get_delete(self):
        response = self.client.get(
            reverse(
                "wagtailsnippets_tests_advert:delete",
                args=[quote(self.test_snippet.pk)],
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "wagtailsnippets/snippets/confirm_delete.html"
        )

    def test_get_delete_mulitple(self):
        url = reverse("wagtailsnippets_tests_advert:delete-multiple")
        url += "?id=%s" % self.test_snippet.id
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "wagtailsnippets/snippets/confirm_delete.html"
        )


class TestSnippetEditHandlers(TestCase, WagtailTestUtils):
    def test_standard_edit_handler(self):
        edit_handler = get_edit_handler(StandardSnippet)
        form_class = edit_handler.get_form_class()
        self.assertTrue(issubclass(form_class, WagtailAdminModelForm))
        self.assertFalse(issubclass(form_class, FancySnippetForm))

    def test_fancy_edit_handler(self):
        edit_handler = get_edit_handler(FancySnippet)
        form_class = edit_handler.get_form_class()
        self.assertTrue(issubclass(form_class, WagtailAdminModelForm))
        self.assertTrue(issubclass(form_class, FancySnippetForm))

    def test_get_snippet_edit_handler(self):
        # TODO: Remove in Wagtail 5.0
        with self.assertWarnsMessage(
            RemovedInWagtail50Warning,
            "The get_snippet_edit_handler function has been moved to wagtail.admin.panels.get_edit_handler",
        ):
            edit_handler = get_snippet_edit_handler(StandardSnippet)
        self.assertIsNotNone(edit_handler)
        self.assertIsInstance(edit_handler, Panel)


class TestInlinePanelMedia(TestCase, WagtailTestUtils):
    """
    Test that form media required by InlinePanels is correctly pulled in to the edit page
    """

    def test_inline_panel_media(self):
        self.login()

        response = self.client.get(
            reverse("wagtailsnippets_snippetstests_multisectionrichtextsnippet:add")
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "wagtailadmin/js/draftail.js")


class TestSnippetChooserBlock(TestCase):
    fixtures = ["test.json"]

    def test_serialize(self):
        """The value of a SnippetChooserBlock (a snippet instance) should serialize to an ID"""
        block = SnippetChooserBlock(Advert)
        test_advert = Advert.objects.get(text="test_advert")

        self.assertEqual(block.get_prep_value(test_advert), test_advert.id)

        # None should serialize to None
        self.assertIsNone(block.get_prep_value(None))

    def test_deserialize(self):
        """The serialized value of a SnippetChooserBlock (an ID) should deserialize to a snippet instance"""
        block = SnippetChooserBlock(Advert)
        test_advert = Advert.objects.get(text="test_advert")

        self.assertEqual(block.to_python(test_advert.id), test_advert)

        # None should deserialize to None
        self.assertIsNone(block.to_python(None))

    def test_reference_model_by_string(self):
        block = SnippetChooserBlock("tests.Advert")
        test_advert = Advert.objects.get(text="test_advert")
        self.assertEqual(block.to_python(test_advert.id), test_advert)

    def test_adapt(self):
        block = SnippetChooserBlock(Advert, help_text="pick an advert, any advert")

        block.set_name("test_snippetchooserblock")
        js_args = FieldBlockAdapter().js_args(block)

        self.assertEqual(js_args[0], "test_snippetchooserblock")
        self.assertIsInstance(js_args[1], AdminSnippetChooser)
        self.assertEqual(js_args[1].model, Advert)
        self.assertEqual(
            js_args[2],
            {
                "label": "Test snippetchooserblock",
                "required": True,
                "icon": "snippet",
                "helpText": "pick an advert, any advert",
                "classname": "w-field w-field--model_choice_field w-field--admin_snippet_chooser",
                "showAddCommentButton": True,
                "strings": {"ADD_COMMENT": "Add Comment"},
            },
        )

    def test_form_response(self):
        block = SnippetChooserBlock(Advert)
        test_advert = Advert.objects.get(text="test_advert")

        value = block.value_from_datadict({"advert": str(test_advert.id)}, {}, "advert")
        self.assertEqual(value, test_advert)

        empty_value = block.value_from_datadict({"advert": ""}, {}, "advert")
        self.assertIsNone(empty_value)

    def test_clean(self):
        required_block = SnippetChooserBlock(Advert)
        nonrequired_block = SnippetChooserBlock(Advert, required=False)
        test_advert = Advert.objects.get(text="test_advert")

        self.assertEqual(required_block.clean(test_advert), test_advert)
        with self.assertRaises(ValidationError):
            required_block.clean(None)

        self.assertEqual(nonrequired_block.clean(test_advert), test_advert)
        self.assertIsNone(nonrequired_block.clean(None))

    def test_deconstruct(self):
        block = SnippetChooserBlock(Advert, required=False)
        path, args, kwargs = block.deconstruct()
        self.assertEqual(path, "wagtail.snippets.blocks.SnippetChooserBlock")
        self.assertEqual(args, (Advert,))
        self.assertEqual(kwargs, {"required": False})

    def test_extract_references(self):
        block = SnippetChooserBlock(Advert)
        test_advert = Advert.objects.get(text="test_advert")

        self.assertListEqual(
            list(block.extract_references(test_advert)),
            [(Advert, str(test_advert.id), "", "")],
        )

        # None should not yield any references
        self.assertListEqual(list(block.extract_references(None)), [])


class TestAdminSnippetChooserWidget(TestCase, WagtailTestUtils):
    def test_adapt(self):
        widget = AdminSnippetChooser(Advert)

        js_args = SnippetChooserAdapter().js_args(widget)

        self.assertEqual(len(js_args), 2)
        self.assertInHTML(
            '<input type="hidden" name="__NAME__" id="__ID__">', js_args[0]
        )
        self.assertIn(">Choose advert<", js_args[0])
        self.assertEqual(js_args[1], "__ID__")


class TestSnippetListViewWithCustomPrimaryKey(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

        # Create some instances of the searchable snippet for testing
        self.snippet_a = StandardSnippetWithCustomPrimaryKey.objects.create(
            snippet_id="snippet/01", text="Hello"
        )
        self.snippet_b = StandardSnippetWithCustomPrimaryKey.objects.create(
            snippet_id="snippet/02", text="Hello"
        )
        self.snippet_c = StandardSnippetWithCustomPrimaryKey.objects.create(
            snippet_id="snippet/03", text="Hello"
        )

    def get(self, params={}):
        return self.client.get(
            reverse(
                "wagtailsnippets_snippetstests_standardsnippetwithcustomprimarykey:list"
            ),
            params,
        )

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailsnippets/snippets/type_index.html")

        # All snippets should be in items
        items = list(response.context["page_obj"].object_list)
        self.assertIn(self.snippet_a, items)
        self.assertIn(self.snippet_b, items)
        self.assertIn(self.snippet_c, items)


class TestSnippetViewWithCustomPrimaryKey(TestCase, WagtailTestUtils):
    fixtures = ["test.json"]

    def setUp(self):
        super(TestSnippetViewWithCustomPrimaryKey, self).setUp()
        self.login()
        self.snippet_a = StandardSnippetWithCustomPrimaryKey.objects.create(
            snippet_id="snippet/01", text="Hello"
        )

    def get(self, snippet, params={}):
        app_label = snippet._meta.app_label
        model_name = snippet._meta.model_name
        args = [quote(snippet.pk)]
        return self.client.get(
            reverse(f"wagtailsnippets_{app_label}_{model_name}:edit", args=args), params
        )

    def post(self, snippet, post_data={}):
        app_label = snippet._meta.app_label
        model_name = snippet._meta.model_name
        args = [quote(snippet.pk)]
        return self.client.post(
            reverse(f"wagtailsnippets_{app_label}_{model_name}:edit", args=args),
            post_data,
        )

    def create(self, snippet, post_data={}, model=Advert):
        app_label = snippet._meta.app_label
        model_name = snippet._meta.model_name
        return self.client.post(
            reverse(f"wagtailsnippets_{app_label}_{model_name}:add"),
            post_data,
        )

    def test_show_edit_view(self):
        response = self.get(self.snippet_a)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailsnippets/snippets/edit.html")

    def test_edit_invalid(self):
        response = self.post(self.snippet_a, post_data={"foo": "bar"})
        self.assertContains(response, "The snippet could not be saved due to errors.")
        self.assertContains(response, "This field is required.")

    def test_edit(self):
        response = self.post(
            self.snippet_a,
            post_data={"text": "Edited snippet", "snippet_id": "snippet_id_edited"},
        )
        self.assertRedirects(
            response,
            reverse(
                "wagtailsnippets_snippetstests_standardsnippetwithcustomprimarykey:list"
            ),
        )

        snippets = StandardSnippetWithCustomPrimaryKey.objects.all()
        self.assertEqual(snippets.count(), 2)
        self.assertEqual(snippets.last().snippet_id, "snippet_id_edited")

    def test_create(self):
        response = self.create(
            self.snippet_a,
            post_data={"text": "test snippet", "snippet_id": "snippet/02"},
        )
        self.assertRedirects(
            response,
            reverse(
                "wagtailsnippets_snippetstests_standardsnippetwithcustomprimarykey:list"
            ),
        )

        snippets = StandardSnippetWithCustomPrimaryKey.objects.all()
        self.assertEqual(snippets.count(), 2)
        self.assertEqual(snippets.last().text, "test snippet")

    def test_get_delete(self):
        response = self.client.get(
            reverse(
                "wagtailsnippets_snippetstests_standardsnippetwithcustomprimarykey:delete",
                args=[quote(self.snippet_a.pk)],
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "wagtailsnippets/snippets/confirm_delete.html"
        )

    def test_usage_link(self):
        response = self.client.get(
            reverse(
                "wagtailsnippets_snippetstests_standardsnippetwithcustomprimarykey:delete",
                args=[quote(self.snippet_a.pk)],
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "wagtailsnippets/snippets/confirm_delete.html"
        )
        self.assertContains(response, "Used 0 times")
        self.assertContains(response, self.snippet_a.usage_url())

    def test_redirect_to_edit(self):
        response = self.client.get(
            "/admin/snippets/snippetstests/standardsnippetwithcustomprimarykey/snippet_2F01/"
        )
        self.assertRedirects(
            response,
            "/admin/snippets/snippetstests/standardsnippetwithcustomprimarykey/edit/snippet_2F01/",
            status_code=301,
        )

    def test_redirect_to_delete(self):
        response = self.client.get(
            "/admin/snippets/snippetstests/standardsnippetwithcustomprimarykey/snippet_2F01/delete/"
        )
        self.assertRedirects(
            response,
            "/admin/snippets/snippetstests/standardsnippetwithcustomprimarykey/delete/snippet_2F01/",
            status_code=301,
        )

    def test_redirect_to_usage(self):
        response = self.client.get(
            "/admin/snippets/snippetstests/standardsnippetwithcustomprimarykey/snippet_2F01/usage/"
        )
        self.assertRedirects(
            response,
            "/admin/snippets/snippetstests/standardsnippetwithcustomprimarykey/usage/snippet_2F01/",
            status_code=301,
        )


class TestSnippetChooserBlockWithCustomPrimaryKey(TestCase):
    fixtures = ["test.json"]

    def test_serialize(self):
        """The value of a SnippetChooserBlock (a snippet instance) should serialize to an ID"""
        block = SnippetChooserBlock(AdvertWithCustomPrimaryKey)
        test_advert = AdvertWithCustomPrimaryKey.objects.get(pk="advert/01")

        self.assertEqual(block.get_prep_value(test_advert), test_advert.pk)

        # None should serialize to None
        self.assertIsNone(block.get_prep_value(None))

    def test_deserialize(self):
        """The serialized value of a SnippetChooserBlock (an ID) should deserialize to a snippet instance"""
        block = SnippetChooserBlock(AdvertWithCustomPrimaryKey)
        test_advert = AdvertWithCustomPrimaryKey.objects.get(pk="advert/01")

        self.assertEqual(block.to_python(test_advert.pk), test_advert)

        # None should deserialize to None
        self.assertIsNone(block.to_python(None))

    def test_adapt(self):
        block = SnippetChooserBlock(
            AdvertWithCustomPrimaryKey, help_text="pick an advert, any advert"
        )

        block.set_name("test_snippetchooserblock")
        js_args = FieldBlockAdapter().js_args(block)

        self.assertEqual(js_args[0], "test_snippetchooserblock")
        self.assertIsInstance(js_args[1], AdminSnippetChooser)
        self.assertEqual(js_args[1].model, AdvertWithCustomPrimaryKey)
        self.assertEqual(
            js_args[2],
            {
                "label": "Test snippetchooserblock",
                "required": True,
                "icon": "snippet",
                "helpText": "pick an advert, any advert",
                "classname": "w-field w-field--model_choice_field w-field--admin_snippet_chooser",
                "showAddCommentButton": True,
                "strings": {"ADD_COMMENT": "Add Comment"},
            },
        )

    def test_form_response(self):
        block = SnippetChooserBlock(AdvertWithCustomPrimaryKey)
        test_advert = AdvertWithCustomPrimaryKey.objects.get(pk="advert/01")

        value = block.value_from_datadict(
            {"advertwithcustomprimarykey": str(test_advert.pk)},
            {},
            "advertwithcustomprimarykey",
        )
        self.assertEqual(value, test_advert)

        empty_value = block.value_from_datadict(
            {"advertwithcustomprimarykey": ""}, {}, "advertwithcustomprimarykey"
        )
        self.assertIsNone(empty_value)

    def test_clean(self):
        required_block = SnippetChooserBlock(AdvertWithCustomPrimaryKey)
        nonrequired_block = SnippetChooserBlock(
            AdvertWithCustomPrimaryKey, required=False
        )
        test_advert = AdvertWithCustomPrimaryKey.objects.get(pk="advert/01")

        self.assertEqual(required_block.clean(test_advert), test_advert)
        with self.assertRaises(ValidationError):
            required_block.clean(None)

        self.assertEqual(nonrequired_block.clean(test_advert), test_advert)
        self.assertIsNone(nonrequired_block.clean(None))


class TestSnippetChooserPanelWithCustomPrimaryKey(TestCase, WagtailTestUtils):
    fixtures = ["test.json"]

    def setUp(self):
        self.request = RequestFactory().get("/")
        user = AnonymousUser()  # technically, Anonymous users cannot access the admin
        self.request.user = user

        model = SnippetChooserModelWithCustomPrimaryKey
        self.advert_text = "Test advert text"
        test_snippet = model.objects.create(
            advertwithcustomprimarykey=AdvertWithCustomPrimaryKey.objects.create(
                advert_id="advert/02", text=self.advert_text
            )
        )

        self.edit_handler = get_edit_handler(model)
        self.form_class = self.edit_handler.get_form_class()
        form = self.form_class(instance=test_snippet)
        edit_handler = self.edit_handler.get_bound_panel(
            instance=test_snippet, form=form, request=self.request
        )

        self.snippet_chooser_panel = [
            panel
            for panel in edit_handler.children
            if getattr(panel, "field_name", None) == "advertwithcustomprimarykey"
        ][0]

    def test_render_html(self):
        field_html = self.snippet_chooser_panel.render_html()
        self.assertIn(self.advert_text, field_html)
        self.assertIn("Choose advert with custom primary key", field_html)
        self.assertIn("Choose another advert with custom primary key", field_html)

    def test_render_as_empty_field(self):
        test_snippet = SnippetChooserModelWithCustomPrimaryKey()
        form = self.form_class(instance=test_snippet)
        edit_handler = self.edit_handler.get_bound_panel(
            instance=test_snippet, form=form, request=self.request
        )

        snippet_chooser_panel = [
            panel
            for panel in edit_handler.children
            if getattr(panel, "field_name", None) == "advertwithcustomprimarykey"
        ][0]

        field_html = snippet_chooser_panel.render_html()
        self.assertIn("Choose advert with custom primary key", field_html)
        self.assertIn("Choose another advert with custom primary key", field_html)

    def test_render_js(self):
        self.assertIn(
            'new SnippetChooser("id_advertwithcustomprimarykey");',
            self.snippet_chooser_panel.render_html(),
        )

    def test_target_model_autodetected(self):
        edit_handler = ObjectList(
            [FieldPanel("advertwithcustomprimarykey")]
        ).bind_to_model(SnippetChooserModelWithCustomPrimaryKey)
        form_class = edit_handler.get_form_class()
        form = form_class()
        widget = form.fields["advertwithcustomprimarykey"].widget
        self.assertIsInstance(widget, AdminSnippetChooser)
        self.assertEqual(widget.model, AdvertWithCustomPrimaryKey)


class TestSnippetChooseWithCustomPrimaryKey(TestCase, WagtailTestUtils):
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

    def test_ordering(self):
        """
        Listing should be ordered by PK if no ordering has been set on the model
        """
        AdvertWithCustomPrimaryKey.objects.all().delete()
        for i in range(10, 0, -1):
            AdvertWithCustomPrimaryKey.objects.create(pk=i, text="advert %d" % i)
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["items"][0].text, "advert 1")


class TestSnippetChosenWithCustomPrimaryKey(TestCase, WagtailTestUtils):
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


class TestSnippetChosenWithCustomUUIDPrimaryKey(TestCase, WagtailTestUtils):
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


class TestPanelConfigurationChecks(TestCase, WagtailTestUtils):
    def setUp(self):
        self.warning_id = "wagtailadmin.W002"

        def get_checks_result():
            # run checks only with the 'panels' tag
            checks_result = checks.run_checks(tags=["panels"])
            return [
                warning for warning in checks_result if warning.id == self.warning_id
            ]

        self.get_checks_result = get_checks_result

    def test_model_with_single_tabbed_panel_only(self):

        StandardSnippet.content_panels = [FieldPanel("text")]

        warning = checks.Warning(
            "StandardSnippet.content_panels will have no effect on snippets editing",
            hint="""Ensure that StandardSnippet uses `panels` instead of `content_panels`\
or set up an `edit_handler` if you want a tabbed editing interface.
There are no default tabs on non-Page models so there will be no\
 Content tab for the content_panels to render in.""",
            obj=StandardSnippet,
            id="wagtailadmin.W002",
        )

        checks_results = self.get_checks_result()

        self.assertEqual([warning], checks_results)

        # clean up for future checks
        delattr(StandardSnippet, "content_panels")
