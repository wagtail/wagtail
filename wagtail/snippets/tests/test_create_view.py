import datetime
from unittest import mock

from django.contrib.admin.utils import quote
from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse
from django.utils.timezone import now
from freezegun import freeze_time
from taggit.models import Tag

from wagtail.models import Locale, ModelLogEntry, Revision
from wagtail.signals import published
from wagtail.snippets.action_menu import (
    ActionMenuItem,
    get_base_snippet_action_menu_items,
)
from wagtail.test.snippets.models import (
    FileUploadSnippet,
)
from wagtail.test.testapp.models import (
    Advert,
    DraftStateModel,
    RevisableModel,
)
from wagtail.test.utils import WagtailTestUtils
from wagtail.test.utils.timestamps import submittable_timestamp


class TestSnippetCreateView(WagtailTestUtils, TestCase):
    def setUp(self):
        self.user = self.login()

    def get(self, params=None, model=Advert, headers=None):
        return self.client.get(
            reverse(model.snippet_viewset.get_url_name("add")), params, headers=headers
        )

    def post(self, post_data=None, model=Advert, headers=None):
        return self.client.post(
            reverse(model.snippet_viewset.get_url_name("add")),
            post_data,
            headers=headers,
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

        soup = self.get_soup(response.content)

        # Should have the unsaved controller set up
        editor_form = soup.select_one("#w-editor-form")
        self.assertIsNotNone(editor_form)
        self.assertIn("w-unsaved", editor_form.attrs.get("data-controller").split())
        self.assertTrue(
            {
                "w-unsaved#submit",
                "beforeunload@window->w-unsaved#confirm",
            }.issubset(editor_form.attrs.get("data-action").split())
        )
        self.assertEqual(
            editor_form.attrs.get("data-w-unsaved-confirmation-value"),
            "true",
        )
        self.assertEqual(
            editor_form.attrs.get("data-w-unsaved-force-value"),
            "false",
        )

    def test_snippet_with_tabbed_interface(self):
        response = self.client.get(
            reverse("wagtailsnippets_tests_advertwithtabbedinterface:add")
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailsnippets/snippets/create.html")
        self.assertContains(response, 'role="tablist"')
        self.assertContains(
            response,
            '<a id="tab-label-advert" href="#tab-advert" class="w-tabs__tab " role="tab" aria-selected="false" tabindex="-1" data-action="w-tabs#select:prevent" data-w-tabs-target="trigger">',
        )
        self.assertContains(
            response,
            '<a id="tab-label-other" href="#tab-other" class="w-tabs__tab " role="tab" aria-selected="false" tabindex="-1" data-action="w-tabs#select:prevent" data-w-tabs-target="trigger">',
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

        soup = self.get_soup(response.content)

        header_messages = soup.css.select(".messages[role='status'] ul > li")

        # there should be one header message that indicates the issue and has a go to error button
        self.assertEqual(len(header_messages), 1)
        message = header_messages[0]
        self.assertIn(
            "The advert could not be created due to errors.", message.get_text()
        )
        buttons = message.find_all("button")
        self.assertEqual(len(buttons), 1)
        self.assertEqual(buttons[0].attrs["data-controller"], "w-count w-focus")
        self.assertEqual(
            set(buttons[0].attrs["data-action"].split()),
            {"click->w-focus#focus", "wagtail:panel-init@document->w-count#count"},
        )
        self.assertIn("Go to the first error", buttons[0].get_text())

        # field specific error should be shown
        error_messages = soup.css.select(".error-message")
        self.assertEqual(len(error_messages), 1)
        error_message = error_messages[0]
        self.assertEqual(error_message.parent["id"], "panel-child-text-errors")
        self.assertIn("This field is required", error_message.get_text())

        # Should have the unsaved controller set up
        editor_form = soup.select_one("#w-editor-form")
        self.assertIsNotNone(editor_form)
        self.assertIn("w-unsaved", editor_form.attrs.get("data-controller").split())
        self.assertTrue(
            {
                "w-unsaved#submit",
                "beforeunload@window->w-unsaved#confirm",
            }.issubset(editor_form.attrs.get("data-action").split())
        )
        self.assertEqual(
            editor_form.attrs.get("data-w-unsaved-confirmation-value"),
            "true",
        )
        self.assertEqual(
            editor_form.attrs.get("data-w-unsaved-force-value"),
            # The form is invalid, we want to force it to be "dirty" on initial load
            "true",
        )

    def test_create_invalid_with_json_response(self):
        response = self.post(
            post_data={"foo": "bar"}, headers={"Accept": "application/json"}
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(
            response.json(),
            {
                "success": False,
                "error_code": "validation_error",
                "error_message": "There are validation errors, click save to highlight them.",
            },
        )

    def test_create(self):
        response = self.post(
            post_data={"text": "test_advert", "url": "http://www.example.com/"}
        )
        self.assertRedirects(response, reverse("wagtailsnippets_tests_advert:list"))

        snippets = Advert.objects.filter(text="test_advert")
        self.assertEqual(snippets.count(), 1)
        self.assertEqual(snippets.first().url, "http://www.example.com/")

    def test_create_with_json_response(self):
        response = self.post(
            post_data={"text": "test_advert", "url": "http://www.example.com/"},
            headers={"Accept": "application/json"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")

        snippets = Advert.objects.filter(text="test_advert")
        self.assertEqual(snippets.count(), 1)
        snippet = snippets.first()
        self.assertEqual(snippet.url, "http://www.example.com/")

        response_json = response.json()
        edit_url = reverse(
            snippet.snippet_viewset.get_url_name("edit"), args=(snippet.pk,)
        )
        self.assertEqual(response_json["success"], True)
        self.assertEqual(response_json["pk"], snippet.pk)
        self.assertEqual(response_json["field_updates"], {})
        self.assertEqual(response_json["url"], edit_url)
        self.assertEqual(
            response_json["hydrate_url"],
            f"{edit_url}?_w_hydrate_create_view=1",
        )

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

    def test_before_create_snippet_hook_get_with_json_response(self):
        def non_json_hook_func(request, model):
            self.assertIsInstance(request, HttpRequest)
            self.assertEqual(model, Advert)
            return HttpResponse("Overridden!")

        def json_hook_func(request, model):
            self.assertIsInstance(request, HttpRequest)
            self.assertEqual(model, Advert)
            return JsonResponse({"status": "purple"})

        with self.register_hook("before_create_snippet", non_json_hook_func):
            response = self.get(headers={"Accept": "application/json"})
            self.assertEqual(
                response.json(),
                {
                    "success": False,
                    "error_code": "blocked_by_hook",
                    "error_message": "Request to create advert was blocked by hook.",
                },
            )

        with self.register_hook("before_create_snippet", json_hook_func):
            response = self.get(headers={"Accept": "application/json"})
            self.assertEqual(response.json(), {"status": "purple"})

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

    def test_before_create_snippet_hook_post_with_json_response(self):
        def non_json_hook_func(request, model):
            self.assertIsInstance(request, HttpRequest)
            self.assertEqual(model, Advert)
            return HttpResponse("Overridden!")

        def json_hook_func(request, model):
            self.assertIsInstance(request, HttpRequest)
            self.assertEqual(model, Advert)
            return JsonResponse({"status": "purple"})

        with self.register_hook("before_create_snippet", non_json_hook_func):
            post_data = {"text": "Hook test", "url": "http://www.example.com/"}
            response = self.post(
                post_data=post_data,
                headers={"Accept": "application/json"},
            )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {
                "success": False,
                "error_code": "blocked_by_hook",
                "error_message": "Request to create advert was blocked by hook.",
            },
        )

        # Request intercepted before advert was created
        self.assertFalse(Advert.objects.exists())

        with self.register_hook("before_create_snippet", json_hook_func):
            post_data = {"text": "Hook test", "url": "http://www.example.com/"}
            response = self.post(
                post_data=post_data,
                headers={"Accept": "application/json"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "purple"})

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

    def test_after_create_snippet_hook_post_with_json_response(self):
        def non_json_hook_func(request, instance):
            self.assertIsInstance(request, HttpRequest)
            self.assertEqual(instance.text, "Hook test")
            self.assertEqual(instance.url, "http://www.example.com/")
            return HttpResponse("Overridden!")

        def json_hook_func(request, instance):
            self.assertIsInstance(request, HttpRequest)
            self.assertEqual(instance.text, "Another hook test")
            self.assertEqual(instance.url, "http://www.example.com/")
            return JsonResponse({"status": "purple"})

        with self.register_hook("after_create_snippet", non_json_hook_func):
            post_data = {"text": "Hook test", "url": "http://www.example.com/"}
            response = self.post(
                post_data=post_data,
                headers={"Accept": "application/json"},
            )

        self.assertEqual(response.status_code, 200)
        # hook response is ignored, since it's not a JSON response
        self.assertEqual(response.json()["success"], True)

        # Request intercepted after advert was created
        self.assertTrue(Advert.objects.filter(text="Hook test").exists())

        with self.register_hook("after_create_snippet", json_hook_func):
            post_data = {"text": "Another hook test", "url": "http://www.example.com/"}
            response = self.post(
                post_data=post_data,
                headers={"Accept": "application/json"},
            )

        self.assertEqual(response.status_code, 200)
        # hook response is used, since it's a JSON response
        self.assertEqual(response.json(), {"status": "purple"})

        # Request intercepted after advert was created
        self.assertTrue(Advert.objects.filter(text="Another hook test").exists())

    def test_register_snippet_action_menu_item(self):
        class TestSnippetActionMenuItem(ActionMenuItem):
            label = "Test"
            name = "test"
            icon_name = "check"
            classname = "custom-class"

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
            '<button type="submit" name="test" value="Test" class="button custom-class"><svg class="icon icon-check icon" aria-hidden="true"><use href="#icon-check"></use></svg>Test</button>',
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
            icon_name = "check"
            classname = "custom-class"

            def is_shown(self, context):
                return True

            class Media:
                js = ["js/some-default-item.js"]
                css = {"all": ["css/some-default-item.css"]}

        def hook_func(menu_items, request, context):
            self.assertIsInstance(menu_items, list)
            self.assertIsInstance(request, WSGIRequest)
            self.assertEqual(context["view"], "create")
            self.assertEqual(context["model"], Advert)

            # Replace save menu item
            menu_items[:] = [TestSnippetActionMenuItem(order=0)]

        with self.register_hook("construct_snippet_action_menu", hook_func):
            response = self.get()

        soup = self.get_soup(response.content)
        custom_action = soup.select_one("form button[name='test']")
        self.assertIsNotNone(custom_action)

        # We're replacing the save button, so it should not be in a dropdown
        # as it's the main action
        dropdown_parent = custom_action.find_parent(attrs={"class": "w-dropdown"})
        self.assertIsNone(dropdown_parent)

        self.assertEqual(custom_action.text.strip(), "Test")
        self.assertEqual(custom_action.attrs.get("class"), ["button", "custom-class"])
        icon = custom_action.select_one("svg use[href='#icon-check']")
        self.assertIsNotNone(icon)

        # Should contain media files
        js = soup.select_one("script[src='/static/js/some-default-item.js']")
        self.assertIsNotNone(js)
        css = soup.select_one("link[href='/static/css/some-default-item.css']")
        self.assertIsNotNone(css)

        save_item = soup.select_one("form button[name='action-save']")
        self.assertIsNone(save_item)

    def test_create_shows_status_side_panel_skeleton(self):
        self.user.first_name = "Chrismansyah"
        self.user.last_name = "Rahadi"
        self.user.save()
        response = self.get(model=RevisableModel)
        soup = self.get_soup(response.content)
        panel = soup.select_one('[data-side-panel="status"]')
        self.assertIsNotNone(panel)

        def assert_panel_section(label_id, label_text, description):
            section = panel.select_one(f'[aria-labelledby="{label_id}"]')
            self.assertIsNotNone(section)
            label = section.select_one(f"#{label_id}")
            self.assertIsNotNone(label)
            self.assertEqual(label.get_text(separator="\n", strip=True), label_text)
            self.assertEqual(
                section.get_text(separator="\n", strip=True),
                f"{label_text}\n{description}",
            )

        assert_panel_section(
            "status-sidebar-live",
            "Live",
            "To be created by Chrismansyah Rahadi",
        )

        usage_section = panel.select("section")[-1]
        self.assertIsNotNone(usage_section)
        self.assertEqual(
            usage_section.get_text(separator="\n", strip=True),
            "Usage\nUsed 0 times",
        )


@override_settings(WAGTAIL_I18N_ENABLED=True)
class TestLocaleSelectorOnCreate(WagtailTestUtils, TestCase):
    fixtures = ["test.json"]

    def setUp(self):
        self.fr_locale = Locale.objects.create(language_code="fr")
        self.user = self.login()

    def test_locale_selector(self):
        response = self.client.get(
            reverse("wagtailsnippets_snippetstests_translatablesnippet:add")
        )

        self.assertContains(response, "Switch locales")

        switch_to_french_url = (
            reverse("wagtailsnippets_snippetstests_translatablesnippet:add")
            + "?locale=fr"
        )
        self.assertContains(
            response,
            f'<a href="{switch_to_french_url}" lang="fr">',
        )

    def test_locale_selector_with_existing_locale(self):
        response = self.client.get(
            reverse("wagtailsnippets_snippetstests_translatablesnippet:add")
            + "?locale=fr"
        )

        self.assertContains(response, "Switch locales")

        switch_to_english_url = (
            reverse("wagtailsnippets_snippetstests_translatablesnippet:add")
            + "?locale=en"
        )
        self.assertContains(
            response,
            f'<a href="{switch_to_english_url}" lang="en">',
        )

    @override_settings(WAGTAIL_I18N_ENABLED=False)
    def test_locale_selector_not_present_when_i18n_disabled(self):
        response = self.client.get(
            reverse("wagtailsnippets_snippetstests_translatablesnippet:add")
        )

        self.assertNotContains(response, "Switch locales")

        switch_to_french_url = (
            reverse("wagtailsnippets_snippetstests_translatablesnippet:add")
            + "?locale=fr"
        )
        self.assertNotContains(
            response,
            f'<a href="{switch_to_french_url}" lang="fr">',
        )

    def test_locale_selector_not_present_on_non_translatable_snippet(self):
        response = self.client.get(reverse("wagtailsnippets_tests_advert:add"))

        self.assertNotContains(response, "Switch locales")

        switch_to_french_url = (
            reverse("wagtailsnippets_snippetstests_translatablesnippet:add")
            + "?locale=fr"
        )
        self.assertNotContains(
            response,
            f'<a href="{switch_to_french_url}" lang="fr">',
        )


class TestCreateDraftStateSnippet(WagtailTestUtils, TestCase):
    STATUS_TOGGLE_BADGE_REGEX = (
        r'data-side-panel-toggle="status"[^<]+<svg[^<]+<use[^<]+</use[^<]+</svg[^<]+'
        r"<div data-side-panel-toggle-counter[^>]+w-bg-critical-200[^>]+>\s*%(num_errors)s\s*</div>"
    )

    def setUp(self):
        self.user = self.login()

    def get(self):
        return self.client.get(reverse("wagtailsnippets_tests_draftstatemodel:add"))

    def post(self, post_data=None):
        return self.client.post(
            reverse("wagtailsnippets_tests_draftstatemodel:add"),
            post_data,
        )

    def test_get(self):
        add_url = reverse("wagtailsnippets_tests_draftstatemodel:add")
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
            '<button\n    type="submit"\n    name="action-publish"\n    value="action-publish"\n    class="button action-save button-longrunning"\n    data-controller="w-progress"\n    data-action="w-progress#activate"\n',
        )
        # The status side panel should be rendered so that the
        # publishing schedule can be configured
        self.assertContains(
            response,
            '<div class="form-side__panel" data-side-panel="status" hidden>',
        )

        # The status side panel should show "No publishing schedule set" info
        self.assertContains(response, "No publishing schedule set")

        # Should show the "Set schedule" button
        html = response.content.decode()
        self.assertTagInHTML(
            '<button type="button" data-a11y-dialog-show="schedule-publishing-dialog">Set schedule</button>',
            html,
            count=1,
            allow_extra_attrs=True,
        )
        # Should show the dialog template pointing to the [data-edit-form] selector as the root
        soup = self.get_soup(html)
        dialog = soup.select_one(
            """
            template[data-controller="w-teleport"][data-w-teleport-target-value="[data-edit-form]"]
            #schedule-publishing-dialog
            """
        )
        self.assertIsNotNone(dialog)
        # Should render the main form with data-edit-form attribute
        self.assertTagInHTML(
            f'<form action="{add_url}" method="POST" data-edit-form>',
            html,
            count=1,
            allow_extra_attrs=True,
        )
        self.assertTagInHTML(
            '<div id="schedule-publishing-dialog" class="w-dialog publishing" data-controller="w-dialog">',
            html,
            count=1,
            allow_extra_attrs=True,
        )

        # Should show the correct subtitle in the dialog
        self.assertContains(
            response, "Choose when this draft state model should go live and/or expire"
        )

        # Should not show the Unpublish action menu item
        unpublish_url = "/admin/snippets/tests/draftstatemodel/unpublish/"
        self.assertNotContains(response, unpublish_url)
        self.assertNotContains(response, "Unpublish")

    def test_save_draft(self):
        response = self.post(post_data={"text": "Draft-enabled Foo"})
        snippet = DraftStateModel.objects.get(text="Draft-enabled Foo")

        self.assertRedirects(
            response,
            reverse("wagtailsnippets_tests_draftstatemodel:edit", args=[snippet.pk]),
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

        # A log entry should be created
        log_entry = ModelLogEntry.objects.for_instance(snippet).get(
            action="wagtail.create"
        )
        self.assertEqual(log_entry.revision, snippet.latest_revision)
        self.assertEqual(log_entry.label, "Draft-enabled Foo")

    def test_create_skips_validation_when_saving_draft(self):
        response = self.post(post_data={"text": ""})
        snippet = DraftStateModel.objects.get(text="")

        self.assertRedirects(
            response,
            reverse(
                "wagtailsnippets_tests_draftstatemodel:edit", args=[quote(snippet.pk)]
            ),
        )

        self.assertFalse(snippet.live)

        # A log entry should be created (with a fallback label)
        log_entry = ModelLogEntry.objects.for_instance(snippet).get(
            action="wagtail.create"
        )
        self.assertEqual(log_entry.revision, snippet.latest_revision)
        self.assertEqual(log_entry.label, f"DraftStateModel object ({snippet.pk})")

    def test_required_asterisk_on_reshowing_form(self):
        """
        If a form is reshown due to a validation error elsewhere, fields whose validation
        was deferred should still show the required asterisk.
        """
        response = self.client.post(
            reverse("some_namespace:add"),
            {"text": "", "country_code": "UK", "some_number": "meef"},
        )

        self.assertEqual(response.status_code, 200)

        # The empty text should not cause a validation error, but the invalid number should
        self.assertNotContains(response, "This field is required.")
        self.assertContains(response, "Enter a whole number.", count=1)

        soup = self.get_soup(response.content)
        self.assertTrue(soup.select_one('label[for="id_text"] > span.w-required-mark'))

    def test_create_will_not_publish_invalid_snippet(self):
        response = self.post(
            post_data={"text": "", "action-publish": "Publish"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, "The draft state model could not be created due to errors."
        )

        snippets = DraftStateModel.objects.filter(text="")
        self.assertEqual(snippets.count(), 0)

    def test_publish(self):
        # Connect a mock signal handler to published signal
        mock_handler = mock.MagicMock()
        published.connect(mock_handler)

        try:
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
        finally:
            published.disconnect(mock_handler)

    def test_publish_bad_permissions(self):
        # Only add create and edit permission
        self.user.is_superuser = False
        add_permission = Permission.objects.get(
            content_type__app_label="tests",
            codename="add_draftstatemodel",
        )
        edit_permission = Permission.objects.get(
            content_type__app_label="tests",
            codename="change_draftstatemodel",
        )
        admin_permission = Permission.objects.get(
            content_type__app_label="wagtailadmin",
            codename="access_admin",
        )
        self.user.user_permissions.add(
            add_permission,
            edit_permission,
            admin_permission,
        )
        self.user.save()

        # Connect a mock signal handler to published signal
        mock_handler = mock.MagicMock()
        published.connect(mock_handler)

        try:
            response = self.post(
                post_data={
                    "text": "Draft-enabled Foo",
                    "action-publish": "action-publish",
                }
            )
            snippet = DraftStateModel.objects.get(text="Draft-enabled Foo")

            # Should be taken to the edit page
            self.assertRedirects(
                response,
                reverse(
                    "wagtailsnippets_tests_draftstatemodel:edit",
                    args=[snippet.pk],
                ),
            )

            # The instance should still be created
            self.assertEqual(snippet.text, "Draft-enabled Foo")

            # The instance should not be live
            self.assertFalse(snippet.live)
            self.assertTrue(snippet.has_unpublished_changes)

            # A revision should be created and set as latest_revision, but not live_revision
            self.assertIsNotNone(snippet.latest_revision)
            self.assertIsNone(snippet.live_revision)

            # The revision content should contain the data
            self.assertEqual(
                snippet.latest_revision.content["text"],
                "Draft-enabled Foo",
            )

            # Check that the published signal was not fired
            self.assertEqual(mock_handler.call_count, 0)
        finally:
            published.disconnect(mock_handler)

    def test_publish_with_publish_permission(self):
        # Use create and publish permissions instead of relying on superuser flag
        self.user.is_superuser = False
        add_permission = Permission.objects.get(
            content_type__app_label="tests",
            codename="add_draftstatemodel",
        )
        publish_permission = Permission.objects.get(
            content_type__app_label="tests",
            codename="publish_draftstatemodel",
        )
        admin_permission = Permission.objects.get(
            content_type__app_label="wagtailadmin",
            codename="access_admin",
        )
        self.user.user_permissions.add(
            add_permission,
            publish_permission,
            admin_permission,
        )
        self.user.save()

        # Connect a mock signal handler to published signal
        mock_handler = mock.MagicMock()
        published.connect(mock_handler)

        try:
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
        finally:
            published.disconnect(mock_handler)

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

        snippet = DraftStateModel.objects.get(text="Some content")

        # Should be redirected to the edit page
        self.assertRedirects(
            response,
            reverse("wagtailsnippets_tests_draftstatemodel:edit", args=[snippet.pk]),
        )

        # Should be saved as draft with the scheduled publishing dates
        self.assertEqual(snippet.go_live_at.date(), go_live_at.date())
        self.assertEqual(snippet.expire_at.date(), expire_at.date())
        self.assertIs(snippet.expired, False)
        self.assertEqual(snippet.status_string, "draft")

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
            response.context["form"],
            "go_live_at",
            "Go live date/time must be before expiry date/time",
        )
        self.assertFormError(
            response.context["form"],
            "expire_at",
            "Go live date/time must be before expiry date/time",
        )

        self.assertContains(
            response,
            '<div class="w-label-3 w-text-primary">Invalid schedule</div>',
            html=True,
        )

        num_errors = 2

        # Should show the correct number on the badge of the toggle button
        self.assertRegex(
            response.content.decode(),
            self.STATUS_TOGGLE_BADGE_REGEX % {"num_errors": num_errors},
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
            response.context["form"],
            "expire_at",
            "Expiry date/time must be in the future.",
        )

        self.assertContains(
            response,
            '<div class="w-label-3 w-text-primary">Invalid schedule</div>',
            html=True,
        )

        num_errors = 1

        # Should show the correct number on the badge of the toggle button
        self.assertRegex(
            response.content.decode(),
            self.STATUS_TOGGLE_BADGE_REGEX % {"num_errors": num_errors},
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
        self.assertRedirects(
            response, reverse("wagtailsnippets_tests_draftstatemodel:list")
        )

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
        self.assertEqual(snippet.status_string, "scheduled")

    def test_create_shows_status_side_panel_skeleton(self):
        self.user.first_name = "Chrismansyah"
        self.user.last_name = "Rahadi"
        self.user.save()
        response = self.get()
        soup = self.get_soup(response.content)
        panel = soup.select_one('[data-side-panel="status"]')
        self.assertIsNotNone(panel)

        def assert_panel_section(label_id, label_text, description):
            section = panel.select_one(f'[aria-labelledby="{label_id}"]')
            self.assertIsNotNone(section)
            label = section.select_one(f"#{label_id}")
            self.assertIsNotNone(label)
            self.assertEqual(label.get_text(separator="\n", strip=True), label_text)
            self.assertEqual(
                section.get_text(separator="\n", strip=True),
                f"{label_text}\n{description}",
            )

        assert_panel_section(
            "status-sidebar-draft",
            "Draft",
            "To be created by Chrismansyah Rahadi",
        )

        usage_section = panel.select("section")[-1]
        self.assertIsNotNone(usage_section)
        self.assertEqual(
            usage_section.get_text(separator="\n", strip=True),
            "Usage\nUsed 0 times",
        )


class TestInlinePanelMedia(WagtailTestUtils, TestCase):
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
