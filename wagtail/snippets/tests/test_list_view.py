from django.contrib.admin.utils import quote
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase, TransactionTestCase
from django.test.utils import override_settings
from django.urls import reverse
from django.utils.timezone import now

from wagtail import hooks
from wagtail.admin.forms.search import SearchForm
from wagtail.admin.staticfiles import versioned_static
from wagtail.admin.widgets.button import Button, ButtonWithDropdown, ListingButton
from wagtail.models import Locale, ModelLogEntry
from wagtail.snippets.widgets import (
    SnippetListingButton,
)
from wagtail.test.snippets.models import (
    NonAutocompleteSearchableSnippet,
    SearchableSnippet,
    StandardSnippetWithCustomPrimaryKey,
    TranslatableSnippet,
)
from wagtail.test.testapp.models import (
    Advert,
    DraftStateModel,
    FullFeaturedSnippet,
)
from wagtail.test.utils import WagtailTestUtils
from wagtail.utils.deprecation import RemovedInWagtail80Warning


class TestSnippetListView(WagtailTestUtils, TestCase):
    def setUp(self):
        self.login()
        user_model = get_user_model()
        self.user = user_model.objects.get()

    def get(self, params=None):
        return self.client.get(reverse("wagtailsnippets_tests_advert:list"), params)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailsnippets/snippets/index.html")
        self.assertEqual(response.context["header_icon"], "snippet")

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

    def get_with_edit_permission_only(self):
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            ),
            Permission.objects.get(
                content_type__app_label="tests", codename="change_advert"
            ),
        )
        self.user.save()

        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "<p>There are no adverts to display.</p>",
            html=True,
        )
        self.assertNotContains(response, reverse("wagtailsnippets_tests_advert:add"))

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
            self.assertTemplateUsed(response, "wagtailsnippets/snippets/index.html")

    def test_displays_add_button(self):
        self.assertContains(self.get(), "Add advert")

    def test_not_searchable(self):
        self.assertFalse(self.get().context.get("search_form"))

    def test_register_snippet_listing_buttons_hook_deprecated_class(self):
        advert = Advert.objects.create(text="My Lovely advert")

        def snippet_listing_buttons(snippet, user, next_url=None):
            self.assertEqual(snippet, advert)
            self.assertEqual(user, self.user)
            self.assertEqual(next_url, reverse("wagtailsnippets_tests_advert:list"))

            yield SnippetListingButton(
                "Another useless snippet listing button", "/custom-url", priority=10
            )

        with hooks.register_temporarily(
            "register_snippet_listing_buttons", snippet_listing_buttons
        ):
            with self.assertWarnsMessage(
                RemovedInWagtail80Warning,
                "`SnippetListingButton` is deprecated. "
                "Use `wagtail.admin.widgets.button.Button` "
                "or `wagtail.admin.widgets.button.ListingButton` instead.",
            ):
                response = self.get()

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/shared/buttons.html")

        soup = self.get_soup(response.content)
        actions = soup.select_one("tbody tr td ul.actions")
        top_level_custom_button = actions.select_one("li > a[href='/custom-url']")
        self.assertIsNone(top_level_custom_button)
        custom_button = actions.select_one(
            "li [data-controller='w-dropdown'] a[href='/custom-url']"
        )
        self.assertIsNotNone(custom_button)
        self.assertEqual(
            custom_button.text.strip(),
            "Another useless snippet listing button",
        )

    def test_register_snippet_listing_buttons_hook(self):
        advert = Advert.objects.create(text="My Lovely advert")

        def snippet_listing_buttons(snippet, user, next_url=None):
            self.assertEqual(snippet, advert)
            self.assertEqual(user, self.user)
            self.assertEqual(next_url, reverse("wagtailsnippets_tests_advert:list"))

            yield ListingButton(
                "A useless top-level snippet listing button",
                "/custom-url",
                priority=10,
            )

            yield Button(
                "A useless snippet listing button inside the 'More' dropdown",
                "/custom-url",
                priority=10,
            )

        with hooks.register_temporarily(
            "register_snippet_listing_buttons", snippet_listing_buttons
        ):
            response = self.get()

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/shared/buttons.html")

        soup = self.get_soup(response.content)
        actions = soup.select_one("tbody tr td ul.actions")
        custom_buttons = actions.select("a[href='/custom-url']")
        top_level_custom_button = actions.select_one("li > a[href='/custom-url']")
        self.assertIs(top_level_custom_button, custom_buttons[0])
        self.assertEqual(
            top_level_custom_button.text.strip(),
            "A useless top-level snippet listing button",
        )
        in_dropdown_custom_button = actions.select_one(
            "li [data-controller='w-dropdown'] a[href='/custom-url']"
        )
        self.assertIs(in_dropdown_custom_button, custom_buttons[1])
        self.assertEqual(
            in_dropdown_custom_button.text.strip(),
            "A useless snippet listing button inside the 'More' dropdown",
        )

    def test_register_snippet_listing_buttons_hook_with_dropdown(self):
        advert = Advert.objects.create(text="My Lovely advert")

        def snippet_listing_buttons(snippet, user, next_url=None):
            self.assertEqual(snippet, advert)
            self.assertEqual(user, self.user)
            self.assertEqual(next_url, reverse("wagtailsnippets_tests_advert:list"))
            yield ButtonWithDropdown(
                label="Moar pls!",
                buttons=[ListingButton("Alrighty", "/cheers", priority=10)],
                attrs={"data-foo": "bar"},
            )

        with hooks.register_temporarily(
            "register_snippet_listing_buttons", snippet_listing_buttons
        ):
            response = self.get()

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/shared/buttons.html")

        soup = self.get_soup(response.content)
        actions = soup.select_one("tbody tr td ul.actions")
        nested_dropdown = actions.select_one(
            "li [data-controller='w-dropdown'] [data-controller='w-dropdown']"
        )
        self.assertIsNone(nested_dropdown)
        dropdown_buttons = actions.select("li > [data-controller='w-dropdown']")
        # Default "More" button and the custom "Moar pls!" button
        self.assertEqual(len(dropdown_buttons), 2)
        custom_dropdown = None
        for button in dropdown_buttons:
            if "Moar pls!" in button.text.strip():
                custom_dropdown = button
        self.assertIsNotNone(custom_dropdown)
        self.assertEqual(custom_dropdown.select_one("button").text.strip(), "Moar pls!")
        self.assertEqual(custom_dropdown.get("data-foo"), "bar")
        # Should contain the custom button inside the custom dropdown
        custom_button = custom_dropdown.find("a", attrs={"href": "/cheers"})
        self.assertIsNotNone(custom_button)
        self.assertEqual(custom_button.text.strip(), "Alrighty")

    def test_construct_snippet_listing_buttons_hook(self):
        Advert.objects.create(text="My Lovely advert")

        # testapp implements a construct_snippet_listing_buttons hook
        # that adds a dummy button with the label 'Dummy Button' which points
        # to '/dummy-button' and is placed inside the default "More" dropdown button
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/shared/buttons.html")

        soup = self.get_soup(response.content)
        dropdowns = soup.select(
            "tbody tr td ul.actions > li > [data-controller='w-dropdown']"
        )
        self.assertEqual(len(dropdowns), 1)
        more_dropdown = dropdowns[0]
        dummy_button = more_dropdown.find("a", attrs={"href": "/dummy-button"})
        self.assertIsNotNone(dummy_button)
        self.assertEqual(dummy_button.text.strip(), "Dummy Button")

    def test_construct_snippet_listing_buttons_hook_contains_default_buttons(self):
        advert = Advert.objects.create(text="My Lovely advert")
        delete_url = reverse(
            "wagtailsnippets_tests_advert:delete", args=[quote(advert.pk)]
        )

        def hide_delete_button_for_lovely_advert(buttons, snippet, user):
            # Edit, delete, dummy button, copy button
            self.assertEqual(len(buttons), 4)
            buttons[:] = [button for button in buttons if button.url != delete_url]
            self.assertEqual(len(buttons), 3)

        with hooks.register_temporarily(
            "construct_snippet_listing_buttons",
            hide_delete_button_for_lovely_advert,
        ):
            response = self.get()

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/shared/buttons.html")
        self.assertNotContains(response, delete_url)

    def test_dropdown_not_rendered_when_no_child_buttons_exist(self):
        Advert.objects.create(text="My Lovely advert")

        def remove_all_buttons(buttons, snippet, user):
            buttons[:] = []
            self.assertEqual(len(buttons), 0)

        with hooks.register_temporarily(
            "construct_snippet_listing_buttons",
            remove_all_buttons,
        ):
            response = self.get()

        soup = self.get_soup(response.content)
        actions = soup.select_one("tbody tr td ul.actions")
        self.assertIsNone(actions)

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
            f"""
            <a href="{edit_url}">
                <span id="snippet_{quote(snippet.pk)}_title">
                    Draft-enabled Bar, In Draft
                </span>
            </a>
            """,
            html=True,
        )

    def test_use_fallback_for_blank_string_representation(self):
        snippet = DraftStateModel.objects.create(text="", live=False)

        response = self.client.get(
            reverse("wagtailsnippets_tests_draftstatemodel:list"),
        )

        edit_url = reverse(
            "wagtailsnippets_tests_draftstatemodel:edit",
            args=[quote(snippet.pk)],
        )
        title = f"DraftStateModel object ({snippet.pk})"

        self.assertContains(
            response,
            f"""
            <a href="{edit_url}">
                <span id="snippet_{quote(snippet.pk)}_title">
                    {title}
                </span>
            </a>
            """,
            html=True,
        )

    def test_use_fallback_for_blank_title_field(self):
        # FullFeaturedSnippet's listing view uses the "text" field as the title column,
        # rather than the str() representation. If this is blank, we show "(blank)" so that
        # there is something to click on
        snippet = FullFeaturedSnippet.objects.create(text="", live=False)
        response = self.client.get(
            reverse("some_namespace:list"),
        )
        edit_url = reverse(
            "some_namespace:edit",
            args=[quote(snippet.pk)],
        )
        self.assertContains(
            response,
            f"""
            <a href="{edit_url}">
                <span id="snippet_{quote(snippet.pk)}_title">
                    (blank)
                </span>
            </a>
            """,
            html=True,
        )

    def test_bulk_action_rendered(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        # Should render bulk actions markup
        bulk_actions_js = versioned_static("wagtailadmin/js/bulk-actions.js")
        soup = self.get_soup(response.content)
        script = soup.select_one(f"script[src='{bulk_actions_js}']")
        self.assertIsNotNone(script)
        bulk_actions = soup.select("[data-bulk-action-button]")
        self.assertTrue(bulk_actions)
        # 'next' parameter is constructed client-side later based on filters state
        for action in bulk_actions:
            self.assertNotIn("next=", action["href"])


@override_settings(WAGTAIL_I18N_ENABLED=True)
class TestLocaleFeaturesOnList(WagtailTestUtils, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.fr_locale = Locale.objects.create(language_code="fr")
        cls.list_url = reverse("wagtailsnippets_snippetstests_translatablesnippet:list")
        cls.add_url = reverse("wagtailsnippets_snippetstests_translatablesnippet:add")

    def setUp(self):
        self.user = self.login()

    def _add_snippets(self):
        TranslatableSnippet.objects.create(text="English snippet")
        TranslatableSnippet.objects.create(text="French snippet", locale=self.fr_locale)

    @override_settings(
        WAGTAIL_CONTENT_LANGUAGES=[
            ("ar", "Arabic"),
            ("en", "English"),
            ("fr", "French"),
        ]
    )
    def test_locale_selector(self):
        response = self.client.get(self.list_url)
        soup = self.get_soup(response.content)

        # Should only show languages that also have the corresponding Locale
        # (the Arabic locale is not created in the setup, so it should not be shown)
        arabic_input = soup.select_one('input[name="locale"][value="ar"]')
        self.assertIsNone(arabic_input)

        french_input = soup.select_one('input[name="locale"][value="fr"]')
        self.assertIsNotNone(french_input)

        # Check that the add URLs include the locale
        add_url = f"{self.add_url}?locale=en"
        add_buttons = soup.select(f'a[href="{add_url}"]')
        self.assertEqual(len(add_buttons), 2)
        self.assertContains(
            response,
            f"""<p>There are no translatable snippets to display.
            Why not <a href="{add_url}">add one</a>?</p>""",
            html=True,
        )

    def test_no_locale_filter_when_only_one_locale(self):
        self.fr_locale.delete()
        response = self.client.get(self.list_url)
        soup = self.get_soup(response.content)

        locale_input = soup.select_one('input[name="locale"]')
        self.assertIsNone(locale_input)

        # The viewset has no other filters configured,
        # so the filters drilldown should not be present
        filters_drilldown = soup.select_one("#filters-drilldown")
        self.assertIsNone(filters_drilldown)

    @override_settings(WAGTAIL_I18N_ENABLED=False)
    def test_locale_selector_not_present_when_i18n_disabled(self):
        response = self.client.get(self.list_url)
        soup = self.get_soup(response.content)

        input_element = soup.select_one('input[name="locale"]')
        self.assertIsNone(input_element)

        # Check that the add URLs don't include the locale
        add_url = self.add_url
        soup = self.get_soup(response.content)
        add_buttons = soup.select(f'a[href="{add_url}"]')
        self.assertEqual(len(add_buttons), 2)
        self.assertContains(
            response,
            f"""<p>There are no translatable snippets to display.
            Why not <a href="{add_url}">add one</a>?</p>""",
            html=True,
        )

    def test_locale_selector_not_present_on_non_translatable_snippet(self):
        response = self.client.get(reverse("wagtailsnippets_tests_advert:list"))
        soup = self.get_soup(response.content)

        input_element = soup.select_one('input[name="locale"]')
        self.assertIsNone(input_element)

        # Check that the add URLs don't include the locale
        add_url = reverse("wagtailsnippets_tests_advert:add")
        soup = self.get_soup(response.content)
        add_buttons = soup.select(f'a[href="{add_url}"]')
        self.assertEqual(len(add_buttons), 2)
        self.assertContains(
            response,
            f"""<p>There are no adverts to display.
            Why not <a href="{add_url}">add one</a>?</p>""",
            html=True,
        )

    def test_locale_column(self):
        self._add_snippets()
        response = self.client.get(self.list_url)
        soup = self.get_soup(response.content)
        labels = soup.select("main table td .w-status--label")
        self.assertEqual(len(labels), 2)
        self.assertEqual(
            sorted(label.text.strip() for label in labels),
            ["English", "French"],
        )

    @override_settings(WAGTAIL_I18N_ENABLED=False)
    def test_locale_column_not_present_with_i18n_disabled(self):
        self._add_snippets()
        response = self.client.get(self.list_url)
        soup = self.get_soup(response.content)
        labels = soup.select("main table td .w-status--label")
        self.assertEqual(len(labels), 0)

    def test_locale_column_not_present_for_non_translatable_snippet(self):
        response = self.client.get(reverse("wagtailsnippets_tests_advert:list"))
        Advert.objects.create(text="English text")
        soup = self.get_soup(response.content)
        labels = soup.select("main table td .w-status--label")
        self.assertEqual(len(labels), 0)


class TestListViewOrdering(WagtailTestUtils, TestCase):
    @classmethod
    def setUpTestData(cls):
        for i in range(1, 10):
            advert = Advert.objects.create(text=f"{i * 'a'}dvert {i}")
            draft = DraftStateModel.objects.create(
                text=f"{i * 'd'}raft {i}", live=False
            )
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
            f'<th><a href="{sort_updated_url}" title="Sort by &#x27;Updated&#x27; in ascending order." class="icon icon-arrow-down-after label">Updated</a></th>',
            html=True,
        )
        # Should not contain the Status column header
        self.assertNotContains(
            response,
            f'<th><a href="{sort_live_url}" title="Sort by &#x27;Status&#x27; in ascending order." class="icon icon-arrow-down-after label">Status</a></th>',
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
            f'<th><a href="{sort_updated_url}" title="Sort by &#x27;Updated&#x27; in ascending order." class="icon icon-arrow-down-after label">Updated</a></th>',
            html=True,
        )
        # The Status column header should be a link with the correct query param
        self.assertContains(
            response,
            f'<th><a href="{sort_live_url}" title="Sort by &#x27;Status&#x27; in ascending order." class="icon icon-arrow-down-after label">Status</a></th>',
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


class TestSnippetListViewWithSearchableSnippet(WagtailTestUtils, TransactionTestCase):
    def setUp(self):
        self.login()

        # Create some instances of the searchable snippet for testing
        self.snippet_a = SearchableSnippet.objects.create(text="Hello")
        self.snippet_b = SearchableSnippet.objects.create(text="World")
        self.snippet_c = SearchableSnippet.objects.create(text="Hello World")

    def get(self, params=None):
        return self.client.get(
            reverse("wagtailsnippets_snippetstests_searchablesnippet:list"),
            params,
        )

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailsnippets/snippets/index.html")

        # All snippets should be in items
        items = list(response.context["page_obj"].object_list)
        self.assertIn(self.snippet_a, items)
        self.assertIn(self.snippet_b, items)
        self.assertIn(self.snippet_c, items)

        # The search box should not raise an error
        self.assertNotContains(response, "This field is required.")

    def test_empty_q(self):
        response = self.get({"q": ""})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailsnippets/snippets/index.html")

        # All snippets should be in items
        items = list(response.context["page_obj"].object_list)
        self.assertIn(self.snippet_a, items)
        self.assertIn(self.snippet_b, items)
        self.assertIn(self.snippet_c, items)

        # The search box should not raise an error
        self.assertNotContains(response, "This field is required.")

    def test_is_searchable(self):
        self.assertIsInstance(self.get().context["search_form"], SearchForm)

    def test_search_hello(self):
        response = self.get({"q": "Hello"})

        # Just snippets with "Hello" should be in items
        items = list(response.context["page_obj"].object_list)
        self.assertIn(self.snippet_a, items)
        self.assertNotIn(self.snippet_b, items)
        self.assertIn(self.snippet_c, items)

    def test_search_world_autocomplete(self):
        response = self.get({"q": "wor"})

        # Just snippets with "World" should be in items
        items = list(response.context["page_obj"].object_list)
        self.assertNotIn(self.snippet_a, items)
        self.assertIn(self.snippet_b, items)
        self.assertIn(self.snippet_c, items)


class TestSnippetListViewWithNonAutocompleteSearchableSnippet(
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
                "wagtailsnippets_snippetstests_nonautocompletesearchablesnippet:list"
            ),
            params,
        )

    def test_search_hello(self):
        with self.assertWarnsRegex(
            RuntimeWarning, "does not specify any AutocompleteFields"
        ):
            response = self.get({"q": "Hello"})

        # Just snippets with "Hello" should be in items
        items = list(response.context["page_obj"].object_list)
        self.assertIn(self.snippet_a, items)
        self.assertNotIn(self.snippet_b, items)
        self.assertIn(self.snippet_c, items)


class TestSnippetListViewWithCustomPrimaryKey(WagtailTestUtils, TestCase):
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

    def get(self, params=None):
        return self.client.get(
            reverse(
                "wagtailsnippets_snippetstests_standardsnippetwithcustomprimarykey:list"
            ),
            params,
        )

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailsnippets/snippets/index.html")

        # All snippets should be in items
        items = list(response.context["page_obj"].object_list)
        self.assertIn(self.snippet_a, items)
        self.assertIn(self.snippet_b, items)
        self.assertIn(self.snippet_c, items)
