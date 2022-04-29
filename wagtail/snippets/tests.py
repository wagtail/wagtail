import datetime
import json

from django.contrib.admin.utils import quote
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser, Permission
from django.contrib.contenttypes.models import ContentType
from django.core import checks
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpRequest, HttpResponse
from django.test import RequestFactory, TestCase
from django.test.utils import override_settings
from django.urls import reverse
from django.utils.timezone import make_aware
from taggit.models import Tag

from wagtail import hooks
from wagtail.admin.admin_url_finder import AdminURLFinder
from wagtail.admin.forms import WagtailAdminModelForm
from wagtail.admin.panels import FieldPanel, ObjectList
from wagtail.blocks.field_block import FieldBlockAdapter
from wagtail.models import Locale, ModelLogEntry, Page
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
    SnippetChooserModel,
    SnippetChooserModelWithCustomPrimaryKey,
)
from wagtail.test.utils import WagtailTestUtils


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
        self.assertTemplateUsed(response, "wagtailsnippets/snippets/index.html")

    def test_displays_snippet(self):
        self.assertContains(self.get(), "Adverts")


class TestSnippetListView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()
        user_model = get_user_model()
        self.user = user_model.objects.get()

    def get(self, params={}):
        return self.client.get(
            reverse("wagtailsnippets:list", args=("tests", "advert")), params
        )

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
        Listing should be ordered by PK if no ordering has been set on the model
        """
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
            self.assertEqual(
                next_url, reverse("wagtailsnippets:list", args=("tests", "advert"))
            )

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


@override_settings(WAGTAIL_I18N_ENABLED=True)
class TestLocaleSelectorOnList(TestCase, WagtailTestUtils):
    def setUp(self):
        self.fr_locale = Locale.objects.create(language_code="fr")
        self.user = self.login()

    def test_locale_selector(self):
        response = self.client.get(
            reverse(
                "wagtailsnippets:list", args=["snippetstests", "translatablesnippet"]
            )
        )

        switch_to_french_url = (
            reverse(
                "wagtailsnippets:list", args=["snippetstests", "translatablesnippet"]
            )
            + "?locale=fr"
        )
        self.assertContains(
            response,
            f'<a href="{switch_to_french_url}" aria-label="French" class="u-link is-live w-no-underline">',
        )

        # Check that the add URLs include the locale
        add_url = (
            reverse(
                "wagtailsnippets:add", args=["snippetstests", "translatablesnippet"]
            )
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
            reverse(
                "wagtailsnippets:list", args=["snippetstests", "translatablesnippet"]
            )
        )

        switch_to_french_url = (
            reverse(
                "wagtailsnippets:list", args=["snippetstests", "translatablesnippet"]
            )
            + "?locale=fr"
        )
        self.assertNotContains(
            response,
            f'<a href="{switch_to_french_url}" aria-label="French" class="u-link is-live w-no-underline">',
        )

        # Check that the add URLs don't include the locale
        add_url = reverse(
            "wagtailsnippets:add", args=["snippetstests", "translatablesnippet"]
        )
        self.assertContains(
            response, f'<a href="{add_url}" class="button bicolor button--icon">'
        )
        self.assertContains(
            response,
            f'No translatable snippets have been created. Why not <a href="{add_url}">add one</a>',
        )

    def test_locale_selector_not_present_on_non_translatable_snippet(self):
        response = self.client.get(
            reverse("wagtailsnippets:list", args=["tests", "advert"])
        )

        self.assertNotContains(
            response, 'aria-label="French" class="u-link is-live w-no-underline">'
        )

        # Check that the add URLs don't include the locale
        add_url = reverse("wagtailsnippets:add", args=["tests", "advert"])
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
            reverse("wagtailsnippets:list", args=("tests", "advertwithtabbedinterface"))
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["items"][0].text, "aaaadvert")

    def test_chooser_respects_model_ordering(self):
        response = self.client.get(
            reverse(
                "wagtailsnippets:choose", args=("tests", "advertwithtabbedinterface")
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["items"][0].text, "aaaadvert")


class TestSnippetListViewWithSearchableSnippet(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

        # Create some instances of the searchable snippet for testing
        self.snippet_a = SearchableSnippet.objects.create(text="Hello")
        self.snippet_b = SearchableSnippet.objects.create(text="World")
        self.snippet_c = SearchableSnippet.objects.create(text="Hello World")

    def get(self, params={}):
        return self.client.get(
            reverse(
                "wagtailsnippets:list", args=("snippetstests", "searchablesnippet")
            ),
            params,
        )

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailsnippets/snippets/type_index.html")

        # All snippets should be in items
        items = list(response.context["items"].object_list)
        self.assertIn(self.snippet_a, items)
        self.assertIn(self.snippet_b, items)
        self.assertIn(self.snippet_c, items)

    def test_is_searchable(self):
        self.assertTrue(self.get().context["is_searchable"])

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


class TestSnippetCreateView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.user = self.login()

    def get(self, params={}, model=Advert):
        args = (model._meta.app_label, model._meta.model_name)
        return self.client.get(reverse("wagtailsnippets:add", args=args), params)

    def post(self, post_data={}, model=Advert):
        args = (model._meta.app_label, model._meta.model_name)
        return self.client.post(reverse("wagtailsnippets:add", args=args), post_data)

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
            reverse("wagtailsnippets:add", args=("tests", "advertwithtabbedinterface"))
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
        self.assertContains(
            response,
            """<p class="error-message"><span>This field is required.</span></p>""",
            count=1,
            html=True,
        )
        self.assertContains(response, "This field is required", count=1)

    def test_create(self):
        response = self.post(
            post_data={"text": "test_advert", "url": "http://www.example.com/"}
        )
        self.assertRedirects(
            response, reverse("wagtailsnippets:list", args=("tests", "advert"))
        )

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

        self.assertRedirects(
            response, reverse("wagtailsnippets:list", args=("tests", "advert"))
        )

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
            reverse(
                "wagtailsnippets:list", args=("snippetstests", "fileuploadsnippet")
            ),
        )
        snippet = FileUploadSnippet.objects.get()
        self.assertEqual(snippet.file.read(), b"Uploaded file")

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
            reverse(
                "wagtailsnippets:add", args=["snippetstests", "translatablesnippet"]
            )
        )

        switch_to_french_url = (
            reverse(
                "wagtailsnippets:add", args=["snippetstests", "translatablesnippet"]
            )
            + "?locale=fr"
        )
        self.assertContains(
            response,
            f'<a href="{switch_to_french_url}" aria-label="French" class="u-link is-live w-no-underline">',
        )

    @override_settings(WAGTAIL_I18N_ENABLED=False)
    def test_locale_selector_not_present_when_i18n_disabled(self):
        response = self.client.get(
            reverse(
                "wagtailsnippets:add", args=["snippetstests", "translatablesnippet"]
            )
        )

        switch_to_french_url = (
            reverse(
                "wagtailsnippets:add", args=["snippetstests", "translatablesnippet"]
            )
            + "?locale=fr"
        )
        self.assertNotContains(
            response,
            f'<a href="{switch_to_french_url}" aria-label="French" class="u-link is-live w-no-underline">',
        )

    def test_locale_selector_not_present_on_non_translatable_snippet(self):
        response = self.client.get(
            reverse("wagtailsnippets:add", args=["tests", "advert"])
        )

        switch_to_french_url = (
            reverse("wagtailsnippets:add", args=["tests", "advert"]) + "?locale=fr"
        )
        self.assertNotContains(
            response,
            f'<a href="{switch_to_french_url}" aria-label="French" class="u-link is-live w-no-underline">',
        )


class BaseTestSnippetEditView(TestCase, WagtailTestUtils):
    def get(self, params={}):
        snippet = self.test_snippet
        args = (snippet._meta.app_label, snippet._meta.model_name, quote(snippet.pk))
        return self.client.get(reverse("wagtailsnippets:edit", args=args), params)

    def post(self, post_data={}):
        snippet = self.test_snippet
        args = (snippet._meta.app_label, snippet._meta.model_name, quote(snippet.pk))
        return self.client.post(reverse("wagtailsnippets:edit", args=args), post_data)

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
            timestamp=make_aware(datetime.datetime(2021, 9, 30, 10, 1, 0)),
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
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailsnippets/snippets/edit.html")
        self.assertNotContains(response, 'role="tablist"')

        # "Last updated" timestamp should be present
        self.assertContains(
            response, 'data-wagtail-tooltip="Sept. 30, 2021, 10:01 a.m."'
        )
        # History link should be present
        self.assertContains(
            response,
            'href="/admin/snippets/tests/advert/history/%d/"' % self.test_snippet.pk,
        )

        url_finder = AdminURLFinder(self.user)
        expected_url = "/admin/snippets/tests/advert/edit/%d/" % self.test_snippet.pk
        self.assertEqual(url_finder.get_edit_url(self.test_snippet), expected_url)

    def test_non_existant_model(self):
        response = self.client.get(
            reverse(
                "wagtailsnippets:edit",
                args=("tests", "foo", quote(self.test_snippet.pk)),
            )
        )
        self.assertEqual(response.status_code, 404)

    def test_nonexistant_id(self):
        response = self.client.get(
            reverse("wagtailsnippets:edit", args=("tests", "advert", 999999))
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
        self.assertContains(
            response,
            """<p class="error-message"><span>This field is required.</span></p>""",
            count=1,
            html=True,
        )
        self.assertContains(response, "This field is required", count=1)

    def test_edit(self):
        response = self.post(
            post_data={
                "text": "edited_test_advert",
                "url": "http://www.example.com/edited",
            }
        )
        self.assertRedirects(
            response, reverse("wagtailsnippets:list", args=("tests", "advert"))
        )

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

        self.assertRedirects(
            response, reverse("wagtailsnippets:list", args=("tests", "advert"))
        )

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
            reverse(
                "wagtailsnippets:list", args=("snippetstests", "fileuploadsnippet")
            ),
        )
        snippet = FileUploadSnippet.objects.get()
        self.assertEqual(snippet.file.read(), b"Replacement document")


@override_settings(WAGTAIL_I18N_ENABLED=True)
class TestLocaleSelectorOnEdit(BaseTestSnippetEditView):
    fixtures = ["test.json"]

    LOCALE_SELECTOR_HTML = '<a href="javascript:void(0)" aria-label="English" class="c-dropdown__button u-btn-current w-no-underline">'
    LOCALE_INDICATOR_HTML = '<use href="#icon-site"></use></svg>\n    English'

    def setUp(self):
        super().setUp()
        self.test_snippet = TranslatableSnippet.objects.create(text="This is a test")
        self.fr_locale = Locale.objects.create(language_code="fr")
        self.test_snippet_fr = self.test_snippet.copy_for_translation(self.fr_locale)
        self.test_snippet_fr.save()

    def test_locale_selector(self):
        response = self.get()

        self.assertContains(response, self.LOCALE_SELECTOR_HTML)

        switch_to_french_url = reverse(
            "wagtailsnippets:edit",
            args=[
                "snippetstests",
                "translatablesnippet",
                quote(self.test_snippet_fr.pk),
            ],
        )
        self.assertContains(
            response,
            f'<a href="{switch_to_french_url}" aria-label="French" class="u-link is-live w-no-underline">',
        )

    def test_locale_selector_without_translation(self):
        self.test_snippet_fr.delete()

        response = self.get()

        self.assertContains(response, self.LOCALE_INDICATOR_HTML)

        switch_to_french_url = reverse(
            "wagtailsnippets:edit",
            args=[
                "snippetstests",
                "translatablesnippet",
                quote(self.test_snippet_fr.pk),
            ],
        )
        self.assertNotContains(
            response,
            f'<a href="{switch_to_french_url}" aria-label="French" class="u-link is-live w-no-underline">',
        )

    @override_settings(WAGTAIL_I18N_ENABLED=False)
    def test_locale_selector_not_present_when_i18n_disabled(self):
        response = self.get()

        self.assertNotContains(response, self.LOCALE_SELECTOR_HTML)

        switch_to_french_url = reverse(
            "wagtailsnippets:edit",
            args=[
                "snippetstests",
                "translatablesnippet",
                quote(self.test_snippet_fr.pk),
            ],
        )
        self.assertNotContains(
            response,
            f'<a href="{switch_to_french_url}" aria-label="French" class="u-link is-live w-no-underline">',
        )

    def test_locale_selector_not_present_on_non_translatable_snippet(self):
        self.test_snippet = Advert.objects.get(pk=1)

        response = self.get()

        self.assertNotContains(response, self.LOCALE_SELECTOR_HTML)
        self.assertNotContains(response, 'aria-label="French" class="u-link is-live">')


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
                "wagtailsnippets:delete",
                args=(
                    "tests",
                    "advert",
                    quote(self.test_snippet.pk),
                ),
            )
        )
        self.assertEqual(response.status_code, 302)

    def test_delete_get(self):
        response = self.client.get(
            reverse(
                "wagtailsnippets:delete",
                args=(
                    "tests",
                    "advert",
                    quote(self.test_snippet.pk),
                ),
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
                "wagtailsnippets:delete",
                args=(
                    "tests",
                    "advert",
                    quote(self.test_snippet.pk),
                ),
            )
        )
        self.assertEqual(response.status_code, 302)

    def test_delete_post(self):
        response = self.client.post(
            reverse(
                "wagtailsnippets:delete",
                args=(
                    "tests",
                    "advert",
                    quote(self.test_snippet.pk),
                ),
            )
        )

        # Should be redirected to explorer page
        self.assertRedirects(
            response, reverse("wagtailsnippets:list", args=("tests", "advert"))
        )

        # Check that the page is gone
        self.assertEqual(Advert.objects.filter(text="test_advert").count(), 0)

    @override_settings(WAGTAIL_USAGE_COUNT_ENABLED=True)
    def test_usage_link(self):
        response = self.client.get(
            reverse(
                "wagtailsnippets:delete",
                args=(
                    "tests",
                    "advert",
                    quote(self.test_snippet.pk),
                ),
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
                reverse(
                    "wagtailsnippets:delete", args=["tests", "advert", quote(advert.pk)]
                )
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
                    "wagtailsnippets:delete",
                    args=(
                        "tests",
                        "advert",
                        quote(advert.pk),
                    ),
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
                    "wagtailsnippets:delete",
                    args=(
                        "tests",
                        "advert",
                        quote(advert.pk),
                    ),
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
        url = reverse("wagtailsnippets:delete-multiple", args=("tests", "advert"))
        url += "?id=%s" % (self.snippet.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_delete_post(self):
        url = reverse("wagtailsnippets:delete-multiple", args=("tests", "advert"))
        url += "?id=%s" % (self.snippet.id)
        response = self.client.post(url)

        # Should be redirected to explorer page
        self.assertRedirects(
            response, reverse("wagtailsnippets:list", args=("tests", "advert"))
        )

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
        url = reverse("wagtailsnippets:delete-multiple", args=("tests", "advert"))
        url += "?id=%s" % (
            "&id=".join(["%s" % snippet.id for snippet in self.snippets])
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_delete_post(self):
        # tests that the URL is available on post and deletes snippets
        url = reverse("wagtailsnippets:delete-multiple", args=("tests", "advert"))
        url += "?id=%s" % (
            "&id=".join(["%s" % snippet.id for snippet in self.snippets])
        )
        response = self.client.post(url)

        # Should be redirected to explorer page
        self.assertRedirects(
            response, reverse("wagtailsnippets:list", args=("tests", "advert"))
        )

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

        self.edit_handler = get_snippet_edit_handler(model)
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

    def test_render_as_field(self):
        field_html = self.snippet_chooser_panel.render_as_field()
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

        field_html = snippet_chooser_panel.render_as_field()
        self.assertIn("Choose advert", field_html)
        self.assertIn("Choose another advert", field_html)

    def test_render_js(self):
        self.assertIn(
            'createSnippetChooser("id_advert");',
            self.snippet_chooser_panel.render_as_field(),
        )

    def test_target_model_autodetected(self):
        edit_handler = ObjectList([FieldPanel("advert")]).bind_to_model(
            SnippetChooserModel
        )
        form_class = edit_handler.get_form_class()
        form = form_class()
        widget = form.fields["advert"].widget
        self.assertIsInstance(widget, AdminSnippetChooser)
        self.assertEqual(widget.target_model, Advert)


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

    @override_settings(WAGTAIL_USAGE_COUNT_ENABLED=True)
    def test_snippet_usage_count(self):
        advert = Advert.objects.get(pk=1)
        self.assertEqual(advert.get_usage().count(), 2)


class TestUsedBy(TestCase):
    fixtures = ["test.json"]

    @override_settings(WAGTAIL_USAGE_COUNT_ENABLED=True)
    def test_snippet_used_by(self):
        advert = Advert.objects.get(pk=1)
        self.assertEqual(type(advert.get_usage()[0]), Page)


class TestSnippetHistory(TestCase, WagtailTestUtils):
    fixtures = ["test.json"]

    def get(self, params={}):
        snippet = self.test_snippet
        args = (snippet._meta.app_label, snippet._meta.model_name, quote(snippet.pk))
        return self.client.get(reverse("wagtailsnippets:history", args=args), params)

    def setUp(self):
        self.user = self.login()
        self.test_snippet = Advert.objects.get(pk=1)
        ModelLogEntry.objects.create(
            content_type=ContentType.objects.get_for_model(Advert),
            label="Test Advert",
            action="wagtail.create",
            timestamp=make_aware(datetime.datetime(2021, 9, 30, 10, 1, 0)),
            object_id="1",
        )

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<td>Created</td>", html=True)
        self.assertContains(
            response,
            '<div class="human-readable-date" title="Sept. 30, 2021, 10:01 a.m.">',
        )


class TestSnippetChoose(TestCase, WagtailTestUtils):
    fixtures = ["test.json"]

    def setUp(self):
        self.login()
        self.url_args = ["tests", "advert"]

    def get(self, params=None):
        return self.client.get(
            reverse("wagtailsnippets:choose", args=self.url_args), params or {}
        )

    def test_simple(self):
        response = self.get()
        self.assertTemplateUsed(response, "wagtailsnippets/chooser/choose.html")

        # Check locale filter doesn't exist normally
        self.assertNotIn(
            '<select id="snippet-chooser-locale" name="lang">', response.json()["html"]
        )

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
            self.assertTemplateUsed(response, "wagtailsnippets/chooser/choose.html")

    def test_not_searchable(self):
        self.assertFalse(self.get().context["is_searchable"])

    @override_settings(WAGTAIL_I18N_ENABLED=True)
    def test_filter_by_locale(self):
        self.url_args = ["snippetstests", "translatablesnippet"]
        fr_locale = Locale.objects.create(language_code="fr")

        TranslatableSnippet.objects.create(text="English snippet")
        TranslatableSnippet.objects.create(text="French snippet", locale=fr_locale)

        response = self.get()

        # Check the filter is added
        self.assertIn(
            '<select id="snippet-chooser-locale" name="locale_filter">',
            response.json()["html"],
        )

        # Check both snippets are shown
        self.assertEqual(len(response.context["items"]), 2)
        self.assertEqual(response.context["items"][0].text, "English snippet")
        self.assertEqual(response.context["items"][1].text, "French snippet")

        # Now test with a locale selected
        response = self.get({"locale": "en"})

        self.assertEqual(len(response.context["items"]), 1)
        self.assertEqual(response.context["items"][0].text, "English snippet")


class TestSnippetChooseWithSearchableSnippet(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

        # Create some instances of the searchable snippet for testing
        self.snippet_a = SearchableSnippet.objects.create(text="Hello")
        self.snippet_b = SearchableSnippet.objects.create(text="World")
        self.snippet_c = SearchableSnippet.objects.create(text="Hello World")

    def get(self, params=None):
        return self.client.get(
            reverse(
                "wagtailsnippets:choose", args=("snippetstests", "searchablesnippet")
            ),
            params or {},
        )

    def test_simple(self):
        response = self.get()
        self.assertTemplateUsed(response, "wagtailsnippets/chooser/choose.html")

        # All snippets should be in items
        items = list(response.context["items"].object_list)
        self.assertIn(self.snippet_a, items)
        self.assertIn(self.snippet_b, items)
        self.assertIn(self.snippet_c, items)

    def test_is_searchable(self):
        self.assertTrue(self.get().context["is_searchable"])

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
            reverse("wagtailsnippets:chosen", args=("tests", "advert", pk)),
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
        response = self.client.get(
            reverse("wagtailsnippets:list", args=("tests", "advert"))
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailsnippets/snippets/type_index.html")

        # user should get an "Add advert" button
        self.assertContains(response, "Add advert")

    def test_get_add(self):
        response = self.client.get(
            reverse("wagtailsnippets:add", args=("tests", "advert"))
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailsnippets/snippets/create.html")

    def test_get_edit(self):
        response = self.client.get(
            reverse(
                "wagtailsnippets:edit",
                args=("tests", "advert", quote(self.test_snippet.pk)),
            )
        )
        # permission should be denied
        self.assertRedirects(response, reverse("wagtailadmin_home"))

    def test_get_delete(self):
        response = self.client.get(
            reverse(
                "wagtailsnippets:delete",
                args=(
                    "tests",
                    "advert",
                    quote(self.test_snippet.pk),
                ),
            )
        )
        # permission should be denied
        self.assertRedirects(response, reverse("wagtailadmin_home"))

    def test_get_delete_mulitple(self):
        url = reverse("wagtailsnippets:delete-multiple", args=("tests", "advert"))
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
        response = self.client.get(
            reverse("wagtailsnippets:list", args=("tests", "advert"))
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailsnippets/snippets/type_index.html")

        # user should not get an "Add advert" button
        self.assertNotContains(response, "Add advert")

    def test_get_add(self):
        response = self.client.get(
            reverse("wagtailsnippets:add", args=("tests", "advert"))
        )
        # permission should be denied
        self.assertRedirects(response, reverse("wagtailadmin_home"))

    def test_get_edit(self):
        response = self.client.get(
            reverse(
                "wagtailsnippets:edit",
                args=("tests", "advert", quote(self.test_snippet.pk)),
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailsnippets/snippets/edit.html")

    def test_get_delete(self):
        response = self.client.get(
            reverse(
                "wagtailsnippets:delete",
                args=(
                    "tests",
                    "advert",
                    quote(self.test_snippet.pk),
                ),
            )
        )
        # permission should be denied
        self.assertRedirects(response, reverse("wagtailadmin_home"))

    def test_get_delete_mulitple(self):
        url = reverse("wagtailsnippets:delete-multiple", args=("tests", "advert"))
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
        response = self.client.get(
            reverse("wagtailsnippets:list", args=("tests", "advert"))
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailsnippets/snippets/type_index.html")

        # user should not get an "Add advert" button
        self.assertNotContains(response, "Add advert")

    def test_get_add(self):
        response = self.client.get(
            reverse("wagtailsnippets:add", args=("tests", "advert"))
        )
        # permission should be denied
        self.assertRedirects(response, reverse("wagtailadmin_home"))

    def test_get_edit(self):
        response = self.client.get(
            reverse(
                "wagtailsnippets:edit",
                args=("tests", "advert", quote(self.test_snippet.pk)),
            )
        )
        # permission should be denied
        self.assertRedirects(response, reverse("wagtailadmin_home"))

    def test_get_delete(self):
        response = self.client.get(
            reverse(
                "wagtailsnippets:delete",
                args=(
                    "tests",
                    "advert",
                    quote(self.test_snippet.pk),
                ),
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "wagtailsnippets/snippets/confirm_delete.html"
        )

    def test_get_delete_mulitple(self):
        url = reverse("wagtailsnippets:delete-multiple", args=("tests", "advert"))
        url += "?id=%s" % self.test_snippet.id
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "wagtailsnippets/snippets/confirm_delete.html"
        )


class TestSnippetEditHandlers(TestCase, WagtailTestUtils):
    def test_standard_edit_handler(self):
        edit_handler = get_snippet_edit_handler(StandardSnippet)
        form_class = edit_handler.get_form_class()
        self.assertTrue(issubclass(form_class, WagtailAdminModelForm))
        self.assertFalse(issubclass(form_class, FancySnippetForm))

    def test_fancy_edit_handler(self):
        edit_handler = get_snippet_edit_handler(FancySnippet)
        form_class = edit_handler.get_form_class()
        self.assertTrue(issubclass(form_class, WagtailAdminModelForm))
        self.assertTrue(issubclass(form_class, FancySnippetForm))


class TestInlinePanelMedia(TestCase, WagtailTestUtils):
    """
    Test that form media required by InlinePanels is correctly pulled in to the edit page
    """

    def test_inline_panel_media(self):
        self.login()

        response = self.client.get(
            reverse(
                "wagtailsnippets:add",
                args=("snippetstests", "multisectionrichtextsnippet"),
            )
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
        self.assertEqual(js_args[1].target_model, Advert)
        self.assertEqual(
            js_args[2],
            {
                "label": "Test snippetchooserblock",
                "required": True,
                "icon": "snippet",
                "helpText": "pick an advert, any advert",
                "classname": "field model_choice_field widget-admin_snippet_chooser fieldname-test_snippetchooserblock",
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
                "wagtailsnippets:list",
                args=("snippetstests", "standardsnippetwithcustomprimarykey"),
            ),
            params,
        )

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailsnippets/snippets/type_index.html")

        # All snippets should be in items
        items = list(response.context["items"].object_list)
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
        args = (snippet._meta.app_label, snippet._meta.model_name, quote(snippet.pk))
        return self.client.get(reverse("wagtailsnippets:edit", args=args), params)

    def post(self, snippet, post_data={}):
        args = (snippet._meta.app_label, snippet._meta.model_name, quote(snippet.pk))
        return self.client.post(reverse("wagtailsnippets:edit", args=args), post_data)

    def create(self, snippet, post_data={}, model=Advert):
        args = (snippet._meta.app_label, snippet._meta.model_name)
        return self.client.post(reverse("wagtailsnippets:add", args=args), post_data)

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
                "wagtailsnippets:list",
                args=("snippetstests", "standardsnippetwithcustomprimarykey"),
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
                "wagtailsnippets:list",
                args=("snippetstests", "standardsnippetwithcustomprimarykey"),
            ),
        )

        snippets = StandardSnippetWithCustomPrimaryKey.objects.all()
        self.assertEqual(snippets.count(), 2)
        self.assertEqual(snippets.last().text, "test snippet")

    def test_get_delete(self):
        response = self.client.get(
            reverse(
                "wagtailsnippets:delete",
                args=(
                    "snippetstests",
                    "standardsnippetwithcustomprimarykey",
                    quote(self.snippet_a.pk),
                ),
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "wagtailsnippets/snippets/confirm_delete.html"
        )

    @override_settings(WAGTAIL_USAGE_COUNT_ENABLED=True)
    def test_usage_link(self):
        response = self.client.get(
            reverse(
                "wagtailsnippets:delete",
                args=(
                    "snippetstests",
                    "standardsnippetwithcustomprimarykey",
                    quote(self.snippet_a.pk),
                ),
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

    @override_settings(WAGTAIL_USAGE_COUNT_ENABLED=True)
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
        self.assertEqual(js_args[1].target_model, AdvertWithCustomPrimaryKey)
        self.assertEqual(
            js_args[2],
            {
                "label": "Test snippetchooserblock",
                "required": True,
                "icon": "snippet",
                "helpText": "pick an advert, any advert",
                "classname": "field model_choice_field widget-admin_snippet_chooser fieldname-test_snippetchooserblock",
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

        self.edit_handler = get_snippet_edit_handler(model)
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

    def test_render_as_field(self):
        field_html = self.snippet_chooser_panel.render_as_field()
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

        field_html = snippet_chooser_panel.render_as_field()
        self.assertIn("Choose advert with custom primary key", field_html)
        self.assertIn("Choose another advert with custom primary key", field_html)

    def test_render_js(self):
        self.assertIn(
            'createSnippetChooser("id_advertwithcustomprimarykey");',
            self.snippet_chooser_panel.render_as_field(),
        )

    def test_target_model_autodetected(self):
        edit_handler = ObjectList(
            [FieldPanel("advertwithcustomprimarykey")]
        ).bind_to_model(SnippetChooserModelWithCustomPrimaryKey)
        form_class = edit_handler.get_form_class()
        form = form_class()
        widget = form.fields["advertwithcustomprimarykey"].widget
        self.assertIsInstance(widget, AdminSnippetChooser)
        self.assertEqual(widget.target_model, AdvertWithCustomPrimaryKey)


class TestSnippetChooseWithCustomPrimaryKey(TestCase, WagtailTestUtils):
    fixtures = ["test.json"]

    def setUp(self):
        self.login()

    def get(self, params=None):
        return self.client.get(
            reverse(
                "wagtailsnippets:choose", args=("tests", "advertwithcustomprimarykey")
            ),
            params or {},
        )

    def test_simple(self):
        response = self.get()
        self.assertTemplateUsed(response, "wagtailsnippets/chooser/choose.html")

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
                "wagtailsnippets:chosen",
                args=("tests", "advertwithcustomprimarykey", quote(pk)),
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
                "wagtailsnippets:chosen",
                args=("tests", "advertwithcustomuuidprimarykey", quote(pk)),
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
