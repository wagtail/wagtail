import datetime
from unittest import mock

from django.contrib.admin.utils import quote
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse
from django.utils.timezone import now
from freezegun import freeze_time
from taggit.models import Tag

from wagtail.admin.admin_url_finder import AdminURLFinder
from wagtail.models import Locale, ModelLogEntry, Revision
from wagtail.signals import published
from wagtail.snippets.action_menu import (
    ActionMenuItem,
    get_base_snippet_action_menu_items,
)
from wagtail.test.snippets.models import (
    FileUploadSnippet,
    StandardSnippetWithCustomPrimaryKey,
    TranslatableSnippet,
)
from wagtail.test.testapp.models import (
    Advert,
    AdvertWithTabbedInterface,
    CustomPreviewSizesModel,
    DraftStateCustomPrimaryKeyModel,
    DraftStateModel,
    FullFeaturedSnippet,
    PreviewableModel,
    RevisableModel,
)
from wagtail.test.utils import WagtailTestUtils
from wagtail.test.utils.timestamps import submittable_timestamp
from wagtail.utils.timestamps import render_timestamp


class BaseTestSnippetEditView(WagtailTestUtils, TestCase):
    def get_edit_url(self):
        snippet = self.test_snippet
        args = [quote(snippet.pk)]
        return reverse(snippet.snippet_viewset.get_url_name("edit"), args=args)

    def get(self, params=None, headers=None):
        return self.client.get(self.get_edit_url(), params, headers=headers)

    def post(self, post_data=None, headers=None):
        return self.client.post(self.get_edit_url(), post_data, headers=headers)

    def setUp(self):
        self.user = self.login()

    def assertSchedulingDialogRendered(self, response, label="Edit schedule"):
        # Should show the "Edit schedule" button
        html = response.content.decode()
        self.assertTagInHTML(
            f'<button type="button" data-a11y-dialog-show="schedule-publishing-dialog">{label}</button>',
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
            f'<form action="{self.get_edit_url()}" method="POST" data-edit-form>',
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

        usage_url = reverse(
            "wagtailsnippets_tests_advert:usage", args=[quote(self.test_snippet.pk)]
        )
        # Usage link should be present in the status side panel
        self.assertContains(response, usage_url)

        # Live status and last updated info should be shown, with a link to the history page
        self.assertContains(response, "3\xa0weeks ago")
        self.assertTagInHTML(
            f'<a href="{history_url}" aria-describedby="status-sidebar-live">View history</a>',
            html,
            allow_extra_attrs=True,
        )

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

        self.assertIsNone(editor_form.select_one("input[name='loaded_revision_id']"))
        self.assertIsNone(
            editor_form.select_one("input[name='loaded_revision_created_at']")
        )

        self.assertIsNotNone(editor_form)
        self.assertNotIn("w-autosave", editor_form["data-controller"].split())
        self.assertNotIn("w-autosave", editor_form["data-action"])
        self.assertIsNone(editor_form.attrs.get("data-w-autosave-interval-value"))

        url_finder = AdminURLFinder(self.user)
        expected_url = "/admin/snippets/tests/advert/edit/%d/" % self.test_snippet.pk
        self.assertEqual(url_finder.get_edit_url(self.test_snippet), expected_url)

    def test_get_hydrate_create_view(self):
        response = self.get(params={"_w_hydrate_create_view": "1"})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/generic/edit_partials.html")
        soup = self.get_soup(response.content)

        # Should reload only the status side panel
        side_panels = soup.select(
            "template[data-controller='w-teleport']"
            "[data-w-teleport-target-value^='[data-side-panel=']"
            "[data-w-teleport-mode-value='innerHTML']"
        )
        self.assertEqual(len(side_panels), 1)
        status_side_panel = side_panels[0]
        self.assertEqual(
            status_side_panel["data-w-teleport-target-value"],
            "[data-side-panel='status']",
        )

        # Workflow and privacy features are not available
        workflow_status_dialog = soup.find("div", id="workflow-status-dialog")
        self.assertIsNone(workflow_status_dialog)
        set_privacy_dialog = soup.find("div", id="set-privacy")
        self.assertIsNone(set_privacy_dialog)

        breadcrumbs = soup.find(
            "template",
            {
                "data-controller": "w-teleport",
                "data-w-teleport-target-value": "header [data-w-breadcrumbs]",
                "data-w-teleport-mode-value": "outerHTML",
            },
        )
        self.assertIsNotNone(breadcrumbs)
        # Should include header buttons as they were not rendered in the create view
        self.assertIsNotNone(breadcrumbs.select_one("#w-slim-header-buttons"))

        # Should render the history link button as it wasn't rendered in the create view
        history_link = soup.find(
            "template",
            {
                "data-controller": "w-teleport",
                "data-w-teleport-target-value": "[data-side-panel-toggle]:last-of-type",
                "data-w-teleport-mode-value": "afterend",
            },
        )
        history_url = reverse(
            self.test_snippet.snippet_viewset.get_url_name("history"),
            args=(quote(self.test_snippet.pk),),
        )
        self.assertIsNotNone(history_link)
        self.assertIsNotNone(history_link.select_one(f"a[href='{history_url}']"))

        form_title_heading = soup.find(
            "template",
            {
                "data-controller": "w-teleport",
                "data-w-teleport-target-value": "#header-title span",
                "data-w-teleport-mode-value": "textContent",
            },
        )
        self.assertIsNotNone(form_title_heading)
        self.assertEqual(form_title_heading.text.strip(), str(self.test_snippet))
        header_title = soup.find(
            "template",
            {
                "data-controller": "w-teleport",
                "data-w-teleport-target-value": "head title",
                "data-w-teleport-mode-value": "textContent",
            },
        )
        self.assertIsNotNone(header_title)
        self.assertEqual(header_title.text.strip(), f"Editing: {self.test_snippet}")

        # Should not include any updates to the form as we don't have revisions
        # enabled and thus don't need to add loaded revision info
        form_adds = soup.find(
            "template",
            {
                "data-controller": "w-teleport",
                "data-w-teleport-target-value": "form[data-edit-form]",
                "data-w-teleport-mode-value": "afterbegin",
            },
        )
        self.assertIsNone(form_adds)

        # Should load the editing sessions module as it was not in the create view
        editing_sessions = soup.find(
            "template",
            {
                "data-controller": "w-teleport",
                "data-w-teleport-target-value": "#w-autosave-indicator",
                "data-w-teleport-mode-value": "afterend",
            },
        )
        self.assertIsNotNone(editing_sessions)
        # without the revision info
        self.assertIsNone(editing_sessions.select_one("input[name='revision_id']"))
        self.assertIsNone(
            editing_sessions.select_one("input[name='revision_created_at']")
        )

    def test_non_existent_model(self):
        response = self.client.get(
            f"/admin/snippets/tests/foo/edit/{quote(self.test_snippet.pk)}/"
        )
        self.assertEqual(response.status_code, 404)

    def test_nonexistent_id(self):
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
        soup = self.get_soup(response.content)

        header_messages = soup.css.select(".messages[role='status'] ul > li")

        # the top level message should indicate that the page could not be saved
        self.assertEqual(len(header_messages), 1)
        message = header_messages[0]
        self.assertIn(
            "The advert could not be saved due to errors.", message.get_text()
        )

        # the top level message should provide a go to error button
        buttons = message.find_all("button")
        self.assertEqual(len(buttons), 1)
        self.assertEqual(buttons[0].attrs["data-controller"], "w-count w-focus")
        self.assertEqual(
            set(buttons[0].attrs["data-action"].split()),
            {"click->w-focus#focus", "wagtail:panel-init@document->w-count#count"},
        )
        self.assertIn("Go to the first error", buttons[0].get_text())

        # the error should only appear once: against the field, not in the header message
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

    def test_edit_invalid_with_json_response(self):
        response = self.post(
            post_data={"foo": "bar"},
            headers={"Accept": "application/json"},
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

    def test_edit_with_json_response(self):
        response = self.post(
            post_data={
                "text": "edited_test_advert",
                "url": "http://www.example.com/edited",
            },
            headers={"Accept": "application/json"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")

        snippets = Advert.objects.filter(text="edited_test_advert")
        self.assertEqual(snippets.count(), 1)
        snippet = snippets.first()
        self.assertEqual(snippet.url, "http://www.example.com/edited")

        response_json = response.json()
        self.assertEqual(response_json["success"], True)
        self.assertEqual(response_json["pk"], snippet.pk)
        self.assertEqual(response_json["field_updates"], {})

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

    def test_before_edit_snippet_hook_get_with_json_response(self):
        def non_json_hook_func(request, instance):
            self.assertIsInstance(request, HttpRequest)
            self.assertEqual(instance.text, "test_advert")
            self.assertEqual(instance.url, "http://www.example.com")

            return HttpResponse("Overridden!")

        def json_hook_func(request, instance):
            self.assertIsInstance(request, HttpRequest)
            self.assertEqual(instance.text, "test_advert")
            self.assertEqual(instance.url, "http://www.example.com")

            return JsonResponse({"status": "purple"})

        with self.register_hook("before_edit_snippet", non_json_hook_func):
            response = self.get(
                headers={"Accept": "application/json"},
            )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {
                "success": False,
                "error_code": "blocked_by_hook",
                "error_message": "Request to edit advert was blocked by hook.",
            },
        )

        with self.register_hook("before_edit_snippet", json_hook_func):
            response = self.get(
                headers={"Accept": "application/json"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "purple"})

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

    def test_before_edit_snippet_hook_post_with_json_response(self):
        def non_json_hook_func(request, instance):
            self.assertIsInstance(request, HttpRequest)
            self.assertEqual(instance.text, "test_advert")
            self.assertEqual(instance.url, "http://www.example.com")

            return HttpResponse("Overridden!")

        def json_hook_func(request, instance):
            self.assertIsInstance(request, HttpRequest)
            self.assertEqual(instance.text, "test_advert")
            self.assertEqual(instance.url, "http://www.example.com")

            return JsonResponse({"status": "purple"})

        with self.register_hook("before_edit_snippet", non_json_hook_func):
            post_data = {
                "text": "Edited and runs hook",
                "url": "http://www.example.com/hook-enabled-edited",
            }
            response = self.post(
                post_data,
                headers={"Accept": "application/json"},
            )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {
                "success": False,
                "error_code": "blocked_by_hook",
                "error_message": "Request to edit advert was blocked by hook.",
            },
        )

        # Request intercepted before advert was updated
        self.assertEqual(Advert.objects.get().text, "test_advert")

        with self.register_hook("before_edit_snippet", json_hook_func):
            post_data = {
                "text": "Edited and runs hook",
                "url": "http://www.example.com/hook-enabled-edited",
            }
            response = self.post(
                post_data,
                headers={"Accept": "application/json"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "purple"})

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

    def test_after_edit_snippet_hook_with_json_response(self):
        def non_json_hook_func(request, instance):
            self.assertIsInstance(request, HttpRequest)
            self.assertEqual(instance.text, "Edited and runs hook")
            self.assertEqual(instance.url, "http://www.example.com/hook-enabled-edited")

            return HttpResponse("Overridden!")

        def json_hook_func(request, instance):
            self.assertIsInstance(request, HttpRequest)
            self.assertEqual(instance.text, "Edited and runs hook x2")
            self.assertEqual(instance.url, "http://www.example.com/hook-enabled-edited")

            return JsonResponse({"status": "purple"})

        with self.register_hook("after_edit_snippet", non_json_hook_func):
            post_data = {
                "text": "Edited and runs hook",
                "url": "http://www.example.com/hook-enabled-edited",
            }
            response = self.post(
                post_data,
                headers={"Accept": "application/json"},
            )

        self.assertEqual(response.status_code, 200)
        # hook response is ignored, since it's not a JSON response
        self.assertEqual(response.json()["success"], True)

        # Request intercepted after advert was updated
        self.assertEqual(Advert.objects.get().text, "Edited and runs hook")

        with self.register_hook("after_edit_snippet", json_hook_func):
            post_data = {
                "text": "Edited and runs hook x2",
                "url": "http://www.example.com/hook-enabled-edited",
            }
            response = self.post(
                post_data,
                headers={"Accept": "application/json"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "purple"})

        # Request intercepted after advert was updated
        self.assertEqual(Advert.objects.get().text, "Edited and runs hook x2")

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

    def test_previewable_snippet(self):
        self.test_snippet = PreviewableModel.objects.create(
            text="Preview-enabled snippet"
        )
        response = self.get()
        self.assertEqual(response.status_code, 200)
        soup = self.get_soup(response.content)

        radios = soup.select('input[type="radio"][name="preview-size"]')
        self.assertEqual(len(radios), 3)

        self.assertEqual(
            [
                "Preview in mobile size",
                "Preview in tablet size",
                "Preview in desktop size",
            ],
            [radio["aria-label"] for radio in radios],
        )

        self.assertEqual("375", radios[0]["data-device-width"])
        self.assertTrue(radios[0].has_attr("checked"))

    def test_custom_preview_sizes(self):
        self.test_snippet = CustomPreviewSizesModel.objects.create(
            text="Preview-enabled with custom sizes",
        )

        response = self.get()
        self.assertEqual(response.status_code, 200)
        soup = self.get_soup(response.content)

        radios = soup.select('input[type="radio"][name="preview-size"]')
        self.assertEqual(len(radios), 2)

        self.assertEqual("412", radios[0]["data-device-width"])
        self.assertEqual("Custom mobile preview", radios[0]["aria-label"])
        self.assertFalse(radios[0].has_attr("checked"))

        self.assertEqual("1280", radios[1]["data-device-width"])
        self.assertEqual("Original desktop", radios[1]["aria-label"])
        self.assertTrue(radios[1].has_attr("checked"))


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
            '<a id="tab-label-advert" href="#tab-advert" class="w-tabs__tab " role="tab" aria-selected="false" tabindex="-1" data-action="w-tabs#select:prevent" data-w-tabs-target="trigger">',
        )
        self.assertContains(
            response,
            '<a id="tab-label-other" href="#tab-other" class="w-tabs__tab " role="tab" aria-selected="false" tabindex="-1" data-action="w-tabs#select:prevent" data-w-tabs-target="trigger">',
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

    def test_get_hydrate_create_view(self):
        latest_revision = self.test_snippet.save_revision(user=self.user)
        response = self.get(params={"_w_hydrate_create_view": "1"})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/generic/edit_partials.html")
        soup = self.get_soup(response.content)

        # Should reload only the status side panel
        side_panels = soup.select(
            "template[data-controller='w-teleport']"
            "[data-w-teleport-target-value^='[data-side-panel=']"
            "[data-w-teleport-mode-value='innerHTML']"
        )
        self.assertEqual(len(side_panels), 1)
        status_side_panel = side_panels[0]
        self.assertEqual(
            status_side_panel["data-w-teleport-target-value"],
            "[data-side-panel='status']",
        )

        # Workflow and privacy features are not available
        workflow_status_dialog = soup.find("div", id="workflow-status-dialog")
        self.assertIsNone(workflow_status_dialog)
        set_privacy_dialog = soup.find("div", id="set-privacy")
        self.assertIsNone(set_privacy_dialog)

        breadcrumbs = soup.find(
            "template",
            {
                "data-controller": "w-teleport",
                "data-w-teleport-target-value": "header [data-w-breadcrumbs]",
                "data-w-teleport-mode-value": "outerHTML",
            },
        )
        self.assertIsNotNone(breadcrumbs)
        # Should include header buttons as they were not rendered in the create view
        self.assertIsNotNone(breadcrumbs.select_one("#w-slim-header-buttons"))

        # Should render the history link button as it wasn't rendered in the create view
        history_link = soup.find(
            "template",
            {
                "data-controller": "w-teleport",
                "data-w-teleport-target-value": "[data-side-panel-toggle]:last-of-type",
                "data-w-teleport-mode-value": "afterend",
            },
        )
        history_url = reverse(
            self.test_snippet.snippet_viewset.get_url_name("history"),
            args=(quote(self.test_snippet.pk),),
        )
        self.assertIsNotNone(history_link)
        self.assertIsNotNone(history_link.select_one(f"a[href='{history_url}']"))

        form_title_heading = soup.find(
            "template",
            {
                "data-controller": "w-teleport",
                "data-w-teleport-target-value": "#header-title span",
                "data-w-teleport-mode-value": "textContent",
            },
        )
        self.assertIsNotNone(form_title_heading)
        self.assertEqual(form_title_heading.text.strip(), str(self.test_snippet))
        header_title = soup.find(
            "template",
            {
                "data-controller": "w-teleport",
                "data-w-teleport-target-value": "head title",
                "data-w-teleport-mode-value": "textContent",
            },
        )
        self.assertIsNotNone(header_title)
        self.assertEqual(header_title.text.strip(), f"Editing: {self.test_snippet}")

        # Should include loaded revision ID and timestamp in the form for
        # subsequent autosave requests
        form_adds = soup.find(
            "template",
            {
                "data-controller": "w-teleport",
                "data-w-teleport-target-value": "form[data-edit-form]",
                "data-w-teleport-mode-value": "afterbegin",
            },
        )
        self.assertIsNotNone(form_adds)
        self.assertEqual(
            form_adds.select_one("input[name='loaded_revision_id']")["value"],
            str(latest_revision.pk),
        )
        self.assertEqual(
            form_adds.select_one("input[name='loaded_revision_created_at']")["value"],
            latest_revision.created_at.isoformat(),
        )

        # Should load the editing sessions module as it was not in the create view
        editing_sessions = soup.find(
            "template",
            {
                "data-controller": "w-teleport",
                "data-w-teleport-target-value": "#w-autosave-indicator",
                "data-w-teleport-mode-value": "afterend",
            },
        )
        self.assertIsNotNone(editing_sessions)
        # with the revision info
        self.assertEqual(
            editing_sessions.select_one("input[name='revision_id']")["value"],
            str(latest_revision.pk),
        )
        self.assertEqual(
            editing_sessions.select_one("input[name='revision_created_at']")["value"],
            latest_revision.created_at.isoformat(),
        )

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

    def test_edit_snippet_with_revision_and_json_response(self):
        initial_revision = self.test_snippet.save_revision(user=self.user)
        self.assertEqual(self.test_snippet.revisions.count(), 1)
        response = self.post(
            post_data={
                "text": "bar",
                "loaded_revision_id": initial_revision.pk,
                "loaded_revision_created_at": initial_revision.created_at.isoformat(),
            },
            headers={"Accept": "application/json"},
        )

        # Should be a 200 OK JSON response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        response_json = response.json()
        self.assertIs(response_json["success"], True)
        self.assertEqual(response_json["pk"], self.test_snippet.pk)

        # Should create a new revision to be overwritten later
        self.assertEqual(self.test_snippet.revisions.count(), 2)
        self.assertNotEqual(response_json["revision_id"], initial_revision.pk)
        revision = self.test_snippet.revisions.get(pk=response_json["revision_id"])
        self.assertEqual(
            response_json["revision_created_at"],
            revision.created_at.isoformat(),
        )
        self.assertEqual(revision.content["text"], "bar")

        # The instance should be updated
        snippets = RevisableModel.objects.filter(text="bar")
        self.assertEqual(snippets.count(), 1)

        # The log entry should have the revision attached
        log_entries = ModelLogEntry.objects.for_instance(self.test_snippet).filter(
            action="wagtail.edit"
        )
        self.assertEqual(log_entries.count(), 1)
        self.assertEqual(log_entries.first().revision, revision)

    def test_save_outdated_revision_with_json_response(self):
        self.test_snippet.text = "Initial revision"
        revision = self.test_snippet.save_revision(user=self.user)
        self.test_snippet.text = "Latest revision"
        self.test_snippet.save_revision()
        self.assertEqual(self.test_snippet.revisions.count(), 2)
        response = self.post(
            post_data={
                "text": "Updated revision",
                "loaded_revision_id": revision.pk,
            },
            headers={"Accept": "application/json"},
        )

        # Instead of creating a new revision for autosave (which means the user
        # would unknowingly replace a newer revision), we return an error
        # response that should be a 400 response
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(
            response.json(),
            {
                "success": False,
                "error_code": "invalid_revision",
                "error_message": "Saving will overwrite a newer version.",
            },
        )

        self.assertEqual(self.test_snippet.revisions.count(), 2)
        revision.refresh_from_db()
        self.assertEqual(revision.content["text"], "Initial revision")

    def test_save_outdated_revision_timestampwith_json_response(self):
        self.test_snippet.text = "Initial revision"
        revision = self.test_snippet.save_revision(user=self.user)
        loaded_revision_created_at = revision.created_at.isoformat()
        self.test_snippet.text = "Latest revision"
        self.test_snippet.save_revision(user=self.user, overwrite_revision=revision)
        self.assertEqual(self.test_snippet.revisions.count(), 1)
        response = self.post(
            post_data={
                "text": "Updated revision",
                "loaded_revision_id": revision.pk,
                "loaded_revision_created_at": loaded_revision_created_at,
            },
            headers={"Accept": "application/json"},
        )

        # Instead of creating a new revision for autosave (which means the user
        # would unknowingly replace a newer revision), we return an error
        # response that should be a 400 response
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(
            response.json(),
            {
                "success": False,
                "error_code": "invalid_revision",
                "error_message": "Saving will overwrite a newer version.",
            },
        )

        self.assertEqual(self.test_snippet.revisions.count(), 1)
        revision.refresh_from_db()
        self.assertEqual(revision.content["text"], "Latest revision")

    def test_overwrite_revision_with_json_response(self):
        self.test_snippet.text = "Initial revision"
        initial_revision = self.test_snippet.save_revision()
        self.test_snippet.text = "Changed via a previous autosave"
        revision = self.test_snippet.save_revision(user=self.user)
        self.assertEqual(self.test_snippet.revisions.count(), 2)
        response = self.post(
            post_data={
                "text": "Updated revision",
                # The page was originally loaded with initial_revision, but
                # a successful autosave created a new revision which we now
                # want to overwrite with a new autosave request
                "loaded_revision_id": initial_revision.pk,
                "overwrite_revision_id": revision.pk,
            },
            headers={"Accept": "application/json"},
        )

        # Should be a 200 OK JSON response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        revision.refresh_from_db()
        response_json = response.json()
        self.assertIs(response_json["success"], True)
        self.assertEqual(response_json["pk"], self.test_snippet.pk)
        self.assertEqual(response_json["revision_id"], revision.pk)
        self.assertEqual(
            response_json["revision_created_at"],
            revision.created_at.isoformat(),
        )
        self.assertEqual(response_json["field_updates"], {})
        soup = self.get_soup(response_json["html"])
        status_side_panel = soup.find(
            "template",
            {
                "data-controller": "w-teleport",
                "data-w-teleport-target-value": "[data-side-panel='status']",
                "data-w-teleport-mode-value": "innerHTML",
            },
        )
        self.assertIsNotNone(status_side_panel)
        breadcrumbs = soup.find(
            "template",
            {
                "data-controller": "w-teleport",
                "data-w-teleport-target-value": "header [data-w-breadcrumbs]",
                "data-w-teleport-mode-value": "outerHTML",
            },
        )
        self.assertIsNotNone(breadcrumbs)
        form_title_heading = soup.find(
            "template",
            {
                "data-controller": "w-teleport",
                "data-w-teleport-target-value": "#header-title span",
                "data-w-teleport-mode-value": "textContent",
            },
        )
        self.assertIsNotNone(form_title_heading)
        self.assertEqual(form_title_heading.text.strip(), "Updated revision")
        header_title = soup.find(
            "template",
            {
                "data-controller": "w-teleport",
                "data-w-teleport-target-value": "head title",
                "data-w-teleport-mode-value": "textContent",
            },
        )
        self.assertIsNotNone(header_title)
        self.assertEqual(header_title.text.strip(), "Editing: Updated revision")

        self.assertEqual(self.test_snippet.revisions.count(), 2)
        revision.refresh_from_db()
        self.assertEqual(revision.content["text"], "Updated revision")

    def test_overwrite_non_latest_revision(self):
        self.test_snippet.text = "Initial revision"
        initial_revision = self.test_snippet.save_revision(user=self.user)
        self.test_snippet.text = "First update via autosave"
        user_revision = self.test_snippet.save_revision(user=self.user)
        self.test_snippet.text = "Someone else's changed text"
        later_revision = self.test_snippet.save_revision()
        self.assertEqual(self.test_snippet.revisions.count(), 3)

        post_data = {
            "text": "Updated revision",
            "loaded_revision_id": initial_revision.id,
            "overwrite_revision_id": user_revision.id,
        }
        response = self.post(
            post_data=post_data,
            headers={"Accept": "application/json"},
        )

        # Should be a 400 response
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(
            response.json(),
            {
                "success": False,
                "error_code": "invalid_revision",
                "error_message": "Saving will overwrite a newer version.",
            },
        )

        # Live DB record should be unchanged
        # (neither save_revision nor the failed form post should have updated it)
        self.test_snippet.refresh_from_db()
        self.assertEqual(self.test_snippet.text, "foo")

        # The passed revision for overwriting, and the actual latest revision, should both be unchanged
        self.assertEqual(self.test_snippet.revisions.count(), 3)
        user_revision.refresh_from_db()
        self.assertEqual(user_revision.content["text"], "First update via autosave")
        later_revision.refresh_from_db()
        self.assertEqual(later_revision.content["text"], "Someone else's changed text")
        self.assertEqual(self.test_snippet.get_latest_revision().id, later_revision.id)

    def test_overwrite_nonexistent_revision(self):
        self.test_snippet.text = "Initial revision"
        user_revision = self.test_snippet.save_revision(user=self.user)
        self.assertEqual(self.test_snippet.revisions.count(), 1)

        post_data = {
            "text": "Updated revision",
            "overwrite_revision_id": 999999,
        }
        response = self.post(
            post_data=post_data,
            headers={"Accept": "application/json"},
        )

        # Should be a 400 response
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(
            response.json(),
            {
                "success": False,
                "error_code": "invalid_revision",
                # We only naively check whether overwrite_revision_id matches
                # the latest revision ID, and if it doesn't, we assume there's
                # a newer revision.
                "error_message": "Saving will overwrite a newer version.",
            },
        )

        # Live DB record should be unchanged
        # (neither save_revision nor the failed form post should have updated it)
        self.test_snippet.refresh_from_db()
        self.assertEqual(self.test_snippet.text, "foo")

        # The latest revision should be unchanged
        self.assertEqual(self.test_snippet.revisions.count(), 1)
        latest_revision = self.test_snippet.get_latest_revision()
        self.assertEqual(latest_revision.id, user_revision.id)
        self.assertEqual(latest_revision.content["text"], "Initial revision")


class TestEditDraftStateSnippet(BaseTestSnippetEditView):
    STATUS_TOGGLE_BADGE_REGEX = (
        r'data-side-panel-toggle="status"[^<]+<svg[^<]+<use[^<]+</use[^<]+</svg[^<]+'
        r"<div data-side-panel-toggle-counter[^>]+w-bg-critical-200[^>]+>\s*%(num_errors)s\s*</div>"
    )

    def setUp(self):
        super().setUp()
        self.test_snippet = DraftStateCustomPrimaryKeyModel.objects.create(
            custom_id="custom/1", text="Draft-enabled Foo", live=False
        )

    def test_get(self):
        revision = self.test_snippet.save_revision()
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
            '<button\n    type="submit"\n    name="action-publish"\n    value="action-publish"\n    class="button action-save button-longrunning"\n    data-controller="w-progress"\n    data-action="w-progress#activate"\n',
        )

        # The status side panel should show "No publishing schedule set" info
        self.assertContains(response, "No publishing schedule set")

        # Should show the "Set schedule" button
        self.assertSchedulingDialogRendered(response, label="Set schedule")

        # Should show the correct subtitle in the dialog
        self.assertContains(
            response,
            "Choose when this draft state custom primary key model should go live and/or expire",
        )

        # Should not show the Unpublish action menu item
        unpublish_url = reverse(
            "wagtailsnippets_tests_draftstatecustomprimarykeymodel:unpublish",
            args=(quote(self.test_snippet.pk),),
        )
        self.assertNotContains(
            response,
            f'<a class="button" href="{unpublish_url}">',
        )
        self.assertNotContains(response, "Unpublish")

        soup = self.get_soup(response.content)
        form = soup.select_one("form[data-edit-form]")
        self.assertIsNotNone(form)
        loaded_revision = form.select_one("input[name='loaded_revision_id']")
        self.assertIsNotNone(loaded_revision)
        self.assertEqual(int(loaded_revision["value"]), revision.pk)
        loaded_timestamp = form.select_one("input[name='loaded_revision_created_at']")
        self.assertIsNotNone(loaded_timestamp)
        self.assertEqual(loaded_timestamp["value"], revision.created_at.isoformat())

        # Autosave defaults to enabled with 500ms interval
        soup = self.get_soup(response.content)
        form = soup.select_one("form[data-edit-form]")
        self.assertIsNotNone(form)
        self.assertIn("w-autosave", form["data-controller"].split())
        self.assertTrue(
            {
                "w-unsaved:add->w-autosave#save:prevent",
                "w-autosave:success->w-unsaved#clear",
            }.issubset(form["data-action"].split())
        )
        self.assertEqual(form.attrs.get("data-w-autosave-interval-value"), "500")

    def test_get_hydrate_create_view(self):
        # Use FullFeaturedSnippet to test the UI hydration of all features
        snippet = FullFeaturedSnippet.objects.create(
            text="Hello world",
            country_code="UK",
            some_number=42,
        )
        latest_revision = snippet.save_revision(user=self.user)
        edit_url = reverse(
            snippet.snippet_viewset.get_url_name("edit"),
            args=(quote(snippet.pk),),
        )
        response = self.client.get(edit_url, {"_w_hydrate_create_view": "1"})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/generic/edit_partials.html")
        soup = self.get_soup(response.content)

        # Should reload the status and preview side panels only
        side_panels = soup.select(
            "template[data-controller='w-teleport']"
            "[data-w-teleport-target-value^='[data-side-panel=']"
            "[data-w-teleport-mode-value='innerHTML']"
        )
        self.assertEqual(len(side_panels), 2)
        status_side_panel = side_panels[0]
        self.assertEqual(
            status_side_panel["data-w-teleport-target-value"],
            "[data-side-panel='status']",
        )

        # Under normal circumstances, a newly-created snippet would never
        # immediately enter a workflow without a full-page reload, so don't
        # bother rendering the workflow status dialog when hydrating a create view
        workflow_status_dialog = soup.find("div", id="workflow-status-dialog")
        self.assertIsNone(workflow_status_dialog)
        # Privacy features are not available for snippets
        set_privacy_dialog = soup.find("div", id="set-privacy")
        self.assertIsNone(set_privacy_dialog)

        # We need to change the preview URL to use the one for editing, but there is
        # no way to declaratively change attributes via partial rendering yet, and we
        # need to restart the controller anyway, so just re-render the whole panel
        preview_side_panel = side_panels[1]
        self.assertEqual(
            preview_side_panel["data-w-teleport-target-value"],
            "[data-side-panel='preview']",
        )
        preview_url = reverse(
            snippet.snippet_viewset.get_url_name("preview_on_edit"),
            args=(quote(snippet.pk),),
        )
        self.assertIsNotNone(
            preview_side_panel.select_one(f"[data-w-preview-url-value='{preview_url}']")
        )

        breadcrumbs = soup.find(
            "template",
            {
                "data-controller": "w-teleport",
                "data-w-teleport-target-value": "header [data-w-breadcrumbs]",
                "data-w-teleport-mode-value": "outerHTML",
            },
        )
        self.assertIsNotNone(breadcrumbs)
        # Should include header buttons as they were not rendered in the create view
        self.assertIsNotNone(breadcrumbs.select_one("#w-slim-header-buttons"))

        # Should render the history link button as it wasn't rendered in the create view
        history_link = soup.find(
            "template",
            {
                "data-controller": "w-teleport",
                "data-w-teleport-target-value": "[data-side-panel-toggle]:last-of-type",
                "data-w-teleport-mode-value": "afterend",
            },
        )
        history_url = reverse(
            snippet.snippet_viewset.get_url_name("history"),
            args=(quote(snippet.pk),),
        )
        self.assertIsNotNone(history_link)
        self.assertIsNotNone(history_link.select_one(f"a[href='{history_url}']"))

        form_title_heading = soup.find(
            "template",
            {
                "data-controller": "w-teleport",
                "data-w-teleport-target-value": "#header-title span",
                "data-w-teleport-mode-value": "textContent",
            },
        )
        self.assertIsNotNone(form_title_heading)
        self.assertEqual(form_title_heading.text.strip(), str(snippet))
        header_title = soup.find(
            "template",
            {
                "data-controller": "w-teleport",
                "data-w-teleport-target-value": "head title",
                "data-w-teleport-mode-value": "textContent",
            },
        )
        self.assertIsNotNone(header_title)
        self.assertEqual(header_title.text.strip(), f"Editing: {snippet}")

        # Should include loaded revision ID and timestamp in the form for
        # subsequent autosave requests
        form_adds = soup.find(
            "template",
            {
                "data-controller": "w-teleport",
                "data-w-teleport-target-value": "form[data-edit-form]",
                "data-w-teleport-mode-value": "afterbegin",
            },
        )
        self.assertIsNotNone(form_adds)
        self.assertEqual(
            form_adds.select_one("input[name='loaded_revision_id']")["value"],
            str(latest_revision.pk),
        )
        self.assertEqual(
            form_adds.select_one("input[name='loaded_revision_created_at']")["value"],
            latest_revision.created_at.isoformat(),
        )

        # Should load the editing sessions module as it was not in the create view
        editing_sessions = soup.find(
            "template",
            {
                "data-controller": "w-teleport",
                "data-w-teleport-target-value": "#w-autosave-indicator",
                "data-w-teleport-mode-value": "afterend",
            },
        )
        self.assertIsNotNone(editing_sessions)
        # with the revision info
        self.assertEqual(
            editing_sessions.select_one("input[name='revision_id']")["value"],
            str(latest_revision.pk),
        )
        self.assertEqual(
            editing_sessions.select_one("input[name='revision_created_at']")["value"],
            latest_revision.created_at.isoformat(),
        )

    @override_settings(WAGTAIL_AUTOSAVE_INTERVAL=0)
    def test_autosave_disabled(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        soup = self.get_soup(response.content)
        form = soup.select_one("form[data-edit-form]")
        self.assertIsNotNone(form)
        self.assertNotIn("w-autosave", form["data-controller"].split())
        self.assertNotIn("w-autosave", form["data-action"])
        self.assertIsNone(form.attrs.get("data-w-autosave-interval-value"))

    @override_settings(WAGTAIL_AUTOSAVE_INTERVAL=2000)
    def test_autosave_custom_interval(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        soup = self.get_soup(response.content)
        form = soup.select_one("form[data-edit-form]")
        self.assertIsNotNone(form)
        self.assertIn("w-autosave", form["data-controller"].split())
        self.assertTrue(
            {
                "w-unsaved:add->w-autosave#save:prevent",
                "w-autosave:success->w-unsaved#clear",
            }.issubset(form["data-action"].split())
        )
        self.assertEqual(form.attrs.get("data-w-autosave-interval-value"), "2000")

    def test_save_draft(self):
        response = self.post(post_data={"text": "Draft-enabled Bar"})
        self.test_snippet.refresh_from_db()
        revisions = Revision.objects.for_instance(self.test_snippet)
        latest_revision = self.test_snippet.latest_revision

        self.assertRedirects(response, self.get_edit_url())

        # The instance should be updated, since it is still a draft
        self.assertEqual(self.test_snippet.text, "Draft-enabled Bar")

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

        # A log entry should be created
        log_entry = (
            ModelLogEntry.objects.for_instance(self.test_snippet)
            .filter(action="wagtail.edit")
            .order_by("-timestamp")
            .first()
        )
        self.assertEqual(log_entry.revision, self.test_snippet.latest_revision)
        self.assertEqual(log_entry.label, "Draft-enabled Bar")

    def test_skip_validation_on_save_draft(self):
        response = self.post(post_data={"text": ""})
        self.test_snippet.refresh_from_db()
        revisions = Revision.objects.for_instance(self.test_snippet)
        latest_revision = self.test_snippet.latest_revision

        self.assertRedirects(response, self.get_edit_url())

        # The instance should be updated, since it is still a draft
        self.assertEqual(self.test_snippet.text, "")

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
        self.assertEqual(latest_revision.content["text"], "")

        # A log entry should be created (with a fallback label)
        log_entry = (
            ModelLogEntry.objects.for_instance(self.test_snippet)
            .filter(action="wagtail.edit")
            .order_by("-timestamp")
            .first()
        )
        self.assertEqual(log_entry.revision, self.test_snippet.latest_revision)
        self.assertEqual(
            log_entry.label,
            f"DraftStateCustomPrimaryKeyModel object ({self.test_snippet.pk})",
        )

    def test_required_asterisk_on_reshowing_form(self):
        """
        If a form is reshown due to a validation error elsewhere, fields whose validation
        was deferred should still show the required asterisk.
        """
        snippet = FullFeaturedSnippet.objects.create(
            text="Hello world",
            country_code="UK",
            some_number=42,
        )
        response = self.client.post(
            reverse("some_namespace:edit", args=[snippet.pk]),
            {"text": "", "country_code": "UK", "some_number": "meef"},
        )

        self.assertEqual(response.status_code, 200)

        # The empty text should not cause a validation error, but the invalid number should
        self.assertNotContains(response, "This field is required.")
        self.assertContains(response, "Enter a whole number.", count=1)

        soup = self.get_soup(response.content)
        self.assertTrue(soup.select_one('label[for="id_text"] > span.w-required-mark'))

    def test_cannot_publish_invalid(self):
        # Connect a mock signal handler to published signal
        mock_handler = mock.MagicMock()
        published.connect(mock_handler)

        try:
            response = self.post(
                post_data={
                    "text": "",
                    "action-publish": "action-publish",
                }
            )

            self.test_snippet.refresh_from_db()

            self.assertEqual(response.status_code, 200)
            self.assertContains(
                response,
                "The draft state custom primary key model could not be saved due to errors.",
            )

            # The instance should be unchanged
            self.assertEqual(self.test_snippet.text, "Draft-enabled Foo")
            self.assertFalse(self.test_snippet.live)

            # The published signal should not have been fired
            self.assertEqual(mock_handler.call_count, 0)
        finally:
            published.disconnect(mock_handler)

    def test_publish(self):
        # Connect a mock signal handler to published signal
        mock_handler = mock.MagicMock()
        published.connect(mock_handler)

        try:
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
            self.assertIsInstance(
                mock_call["instance"], DraftStateCustomPrimaryKeyModel
            )
        finally:
            published.disconnect(mock_handler)

    def test_publish_bad_permissions(self):
        # Only add edit permission
        self.user.is_superuser = False
        edit_permission = Permission.objects.get(
            content_type__app_label="tests",
            codename="change_draftstatecustomprimarykeymodel",
        )
        admin_permission = Permission.objects.get(
            content_type__app_label="wagtailadmin",
            codename="access_admin",
        )
        self.user.user_permissions.add(edit_permission, admin_permission)
        self.user.save()

        # Connect a mock signal handler to published signal
        mock_handler = mock.MagicMock()
        published.connect(mock_handler)

        try:
            response = self.post(
                post_data={
                    "text": "Edited draft Foo",
                    "action-publish": "action-publish",
                }
            )
            self.test_snippet.refresh_from_db()

            # Should remain on the edit page
            self.assertRedirects(response, self.get_edit_url())

            # The instance should be edited, since it is still a draft
            self.assertEqual(self.test_snippet.text, "Edited draft Foo")

            # The instance should not be live
            self.assertFalse(self.test_snippet.live)
            self.assertTrue(self.test_snippet.has_unpublished_changes)

            # A revision should be created and set as latest_revision, but not live_revision
            self.assertIsNotNone(self.test_snippet.latest_revision)
            self.assertIsNone(self.test_snippet.live_revision)

            # The revision content should contain the data
            self.assertEqual(
                self.test_snippet.latest_revision.content["text"],
                "Edited draft Foo",
            )

            # Check that the published signal was not fired
            self.assertEqual(mock_handler.call_count, 0)
        finally:
            published.disconnect(mock_handler)

    def test_publish_with_publish_permission(self):
        # Only add edit and publish permissions
        self.user.is_superuser = False
        edit_permission = Permission.objects.get(
            content_type__app_label="tests",
            codename="change_draftstatecustomprimarykeymodel",
        )
        publish_permission = Permission.objects.get(
            content_type__app_label="tests",
            codename="publish_draftstatecustomprimarykeymodel",
        )
        admin_permission = Permission.objects.get(
            content_type__app_label="wagtailadmin", codename="access_admin"
        )
        self.user.user_permissions.add(
            edit_permission,
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
            self.assertIsInstance(
                mock_call["instance"], DraftStateCustomPrimaryKeyModel
            )
        finally:
            published.disconnect(mock_handler)

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

        self.assertRedirects(response, self.get_edit_url())

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
            f'<a class="button" href="{unpublish_url}">',
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
            f'<a class="button" href="{unpublish_url}">',
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
            f'<a class="button" href="{unpublish_url}">',
        )
        self.assertContains(response, "Unpublish")

        soup = self.get_soup(response.content)
        h2 = soup.select_one("#header-title")
        self.assertIsNotNone(h2)
        icon = h2.select_one("svg use")
        self.assertIsNotNone(icon)
        self.assertEqual(icon["href"], "#icon-snippet")
        self.assertEqual(h2.text.strip(), "Draft-enabled Bar, In Draft")

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

        # Should be redirected to the edit page
        self.assertRedirects(
            response,
            reverse(
                "wagtailsnippets_tests_draftstatecustomprimarykeymodel:edit",
                args=[quote(self.test_snippet.pk)],
            ),
        )

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

        # Should show the draft go_live_at and expire_at under the "Once scheduled" label
        self.assertContains(
            response,
            '<div class="w-label-3 w-text-primary">Once scheduled:</div>',
            html=True,
            count=1,
        )
        self.assertContains(
            response,
            f'<span class="w-text-grey-600">Go-live:</span> {render_timestamp(go_live_at)}',
            html=True,
            count=1,
        )
        self.assertContains(
            response,
            f'<span class="w-text-grey-600">Expiry:</span> {render_timestamp(expire_at)}',
            html=True,
            count=1,
        )
        self.assertSchedulingDialogRendered(response)

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

    def test_edit_post_invalid_schedule_with_existing_draft_schedule(self):
        self.test_snippet.go_live_at = now() + datetime.timedelta(days=1)
        self.test_snippet.expire_at = now() + datetime.timedelta(days=2)
        latest_revision = self.test_snippet.save_revision()

        go_live_at = now() + datetime.timedelta(days=10)
        expire_at = now() + datetime.timedelta(days=-20)
        response = self.post(
            post_data={
                "text": "Some edited content",
                "go_live_at": submittable_timestamp(go_live_at),
                "expire_at": submittable_timestamp(expire_at),
            }
        )

        # Should render the edit page with errors instead of redirecting
        self.assertEqual(response.status_code, 200)

        self.test_snippet.refresh_from_db()

        # The snippet will not be live
        self.assertFalse(self.test_snippet.live)

        # No new revision should have been created
        self.assertEqual(self.test_snippet.latest_revision_id, latest_revision.pk)

        # Should not show the draft go_live_at and expire_at under the "Once scheduled" label
        self.assertNotContains(
            response,
            '<div class="w-label-3 w-text-primary">Once scheduled:</div>',
            html=True,
        )
        self.assertNotContains(
            response,
            '<span class="w-text-grey-600">Go-live:</span>',
            html=True,
        )
        self.assertNotContains(
            response,
            '<span class="w-text-grey-600">Expiry:</span>',
            html=True,
        )

        # Should show the "Edit schedule" button
        html = response.content.decode()
        self.assertTagInHTML(
            '<button type="button" data-a11y-dialog-show="schedule-publishing-dialog">Edit schedule</button>',
            html,
            count=1,
            allow_extra_attrs=True,
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
        self.assertRedirects(
            response,
            reverse("wagtailsnippets_tests_draftstatecustomprimarykeymodel:list"),
        )

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
            msg="An object scheduled for future publishing should have has_unpublished_changes=True",
        )

        self.assertEqual(self.test_snippet.status_string, "scheduled")

        response = self.get()

        # Should show the go_live_at and expire_at without the "Once scheduled" label
        self.assertNotContains(
            response,
            '<div class="w-label-3 w-text-primary">Once scheduled:</div>',
            html=True,
        )
        self.assertContains(
            response,
            f'<span class="w-text-grey-600">Go-live:</span> {render_timestamp(go_live_at)}',
            html=True,
            count=1,
        )
        self.assertContains(
            response,
            f'<span class="w-text-grey-600">Expiry:</span> {render_timestamp(expire_at)}',
            html=True,
            count=1,
        )
        self.assertSchedulingDialogRendered(response)

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
        self.assertRedirects(
            response,
            reverse("wagtailsnippets_tests_draftstatecustomprimarykeymodel:list"),
        )

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
        self.assertRedirects(
            response,
            reverse("wagtailsnippets_tests_draftstatecustomprimarykeymodel:list"),
        )

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
        self.assertSchedulingDialogRendered(response)

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
        self.assertRedirects(
            response,
            reverse("wagtailsnippets_tests_draftstatecustomprimarykeymodel:list"),
        )

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
            msg="An object scheduled for future publishing should have has_unpublished_changes=True",
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

        # Should show the go_live_at and expire_at without the "Once scheduled" label
        self.assertNotContains(
            response,
            '<div class="w-label-3 w-text-primary">Once scheduled:</div>',
            html=True,
        )
        self.assertContains(
            response,
            f'<span class="w-text-grey-600">Go-live:</span> {render_timestamp(go_live_at)}',
            html=True,
            count=1,
        )
        self.assertContains(
            response,
            f'<span class="w-text-grey-600">Expiry:</span> {render_timestamp(expire_at)}',
            html=True,
            count=1,
        )
        self.assertSchedulingDialogRendered(response)

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
        self.assertRedirects(
            response,
            reverse("wagtailsnippets_tests_draftstatecustomprimarykeymodel:list"),
        )

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
        self.assertRedirects(
            response,
            reverse("wagtailsnippets_tests_draftstatecustomprimarykeymodel:list"),
        )

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
        self.assertRedirects(
            response,
            reverse("wagtailsnippets_tests_draftstatecustomprimarykeymodel:list"),
        )

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

        # Should be redirected to the edit page
        self.assertRedirects(
            response,
            reverse(
                "wagtailsnippets_tests_draftstatecustomprimarykeymodel:edit",
                args=[quote(self.test_snippet.pk)],
            ),
        )

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
            f'<span class="w-text-grey-600">Expiry:</span> {render_timestamp(expire_at)}',
            html=True,
            count=1,
        )

        # Should also show the draft go_live_at and expire_at under the "Once scheduled" label
        self.assertContains(
            response,
            '<div class="w-label-3 w-text-primary">Once scheduled:</div>',
            html=True,
            count=1,
        )
        self.assertContains(
            response,
            f'<span class="w-text-grey-600">Go-live:</span> {render_timestamp(go_live_at)}',
            html=True,
            count=1,
        )
        self.assertContains(
            response,
            f'<span class="w-text-grey-600">Expiry:</span> {render_timestamp(new_expire_at)}',
            html=True,
            count=1,
        )
        self.assertSchedulingDialogRendered(response)

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
        self.assertRedirects(
            response,
            reverse("wagtailsnippets_tests_draftstatecustomprimarykeymodel:list"),
        )

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
        self.assertRedirects(
            response,
            reverse("wagtailsnippets_tests_draftstatecustomprimarykeymodel:list"),
        )

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
            f'<span class="w-text-grey-600">Expiry:</span> {render_timestamp(expire_at)}',
            html=True,
        )

        # Should show the go_live_at and expire_at without the "Once scheduled" label
        self.assertNotContains(
            response,
            '<div class="w-label-3 w-text-primary">Once scheduled:</div>',
            html=True,
        )
        self.assertContains(
            response,
            f'<span class="w-text-grey-600">Go-live:</span> {render_timestamp(go_live_at)}',
            html=True,
            count=1,
        )
        self.assertContains(
            response,
            f'<span class="w-text-grey-600">Expiry:</span> {render_timestamp(new_expire_at)}',
            html=True,
            count=1,
        )
        self.assertSchedulingDialogRendered(response)

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
        self.assertRedirects(
            response,
            reverse("wagtailsnippets_tests_draftstatecustomprimarykeymodel:list"),
        )

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
        self.assertRedirects(
            response,
            reverse("wagtailsnippets_tests_draftstatecustomprimarykeymodel:list"),
        )

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
            f'<span class="w-text-grey-600">Expiry:</span> {render_timestamp(expire_at)}',
            html=True,
            count=1,
        )

        # Should show the go_live_at and expire_at without the "Once scheduled" label
        self.assertNotContains(
            response,
            '<div class="w-label-3 w-text-primary">Once scheduled:</div>',
            html=True,
        )
        self.assertContains(
            response,
            f'<span class="w-text-grey-600">Go-live:</span> {render_timestamp(go_live_at)}',
            html=True,
            count=1,
        )
        self.assertContains(
            response,
            f'<span class="w-text-grey-600">Expiry:</span> {render_timestamp(new_expire_at)}',
            html=True,
            count=1,
        )
        self.assertSchedulingDialogRendered(response)

    def test_use_fallback_for_blank_string_representation(self):
        self.snippet = DraftStateModel.objects.create(text="", live=False)

        response = self.client.get(
            reverse(
                "wagtailsnippets_tests_draftstatemodel:edit",
                args=[quote(self.snippet.pk)],
            ),
        )

        title = f"DraftStateModel object ({self.snippet.pk})"

        soup = self.get_soup(response.content)
        h2 = soup.select_one("#header-title")
        self.assertEqual(h2.text.strip(), title)

        sublabel = soup.select_one(".w-breadcrumbs li:last-of-type")
        self.assertEqual(sublabel.get_text(strip=True), title)


class TestScheduledForPublishLock(BaseTestSnippetEditView):
    def setUp(self):
        super().setUp()
        self.test_snippet = DraftStateModel.objects.create(
            text="Draft-enabled Foo", live=False
        )
        self.go_live_at = now() + datetime.timedelta(days=1)
        self.test_snippet.text = "I've been edited!"
        self.test_snippet.go_live_at = self.go_live_at
        self.latest_revision = self.test_snippet.save_revision()
        self.latest_revision.publish()
        self.test_snippet.refresh_from_db()

    def test_edit_get_scheduled_for_publishing_with_publish_permission(self):
        self.user.is_superuser = False

        edit_permission = Permission.objects.get(
            content_type__app_label="tests", codename="change_draftstatemodel"
        )
        publish_permission = Permission.objects.get(
            content_type__app_label="tests", codename="publish_draftstatemodel"
        )
        admin_permission = Permission.objects.get(
            content_type__app_label="wagtailadmin", codename="access_admin"
        )

        self.user.user_permissions.add(
            edit_permission,
            publish_permission,
            admin_permission,
        )
        self.user.save()

        response = self.get()

        # Should show the go_live_at without the "Once scheduled" label
        self.assertNotContains(
            response,
            '<div class="w-label-3 w-text-primary">Once scheduled:</div>',
            html=True,
        )

        self.assertContains(
            response,
            f'<span class="w-text-grey-600">Go-live:</span> {render_timestamp(self.go_live_at)}',
            html=True,
            count=1,
        )

        # Should show the lock message
        self.assertContains(
            response,
            "Draft state model 'I&#x27;ve been edited!' is locked and has been scheduled to go live at",
            count=1,
        )

        # Should show the lock information in the status side panel
        self.assertContains(response, "Locked by schedule")
        self.assertContains(
            response,
            '<div class="w-help-text">Currently locked and will go live on the scheduled date</div>',
            html=True,
            count=1,
        )

        html = response.content.decode()

        # Should not show the "Edit schedule" button
        self.assertTagInHTML(
            '<button type="button" data-a11y-dialog-show="schedule-publishing-dialog">Edit schedule</button>',
            html,
            count=0,
            allow_extra_attrs=True,
        )

        # Should show button to cancel scheduled publishing
        unschedule_url = reverse(
            "wagtailsnippets_tests_draftstatemodel:revisions_unschedule",
            args=[self.test_snippet.pk, self.latest_revision.pk],
        )
        self.assertTagInHTML(
            f'<button data-action="w-action#post" data-controller="w-action" data-w-action-url-value="{unschedule_url}">Cancel scheduled publish</button>',
            html,
            count=1,
            allow_extra_attrs=True,
        )

    def test_edit_get_scheduled_for_publishing_without_publish_permission(self):
        self.user.is_superuser = False

        edit_permission = Permission.objects.get(
            content_type__app_label="tests", codename="change_draftstatemodel"
        )
        admin_permission = Permission.objects.get(
            content_type__app_label="wagtailadmin", codename="access_admin"
        )

        self.user.user_permissions.add(edit_permission, admin_permission)
        self.user.save()

        response = self.get()

        # Should show the go_live_at without the "Once scheduled" label
        self.assertNotContains(
            response,
            '<div class="w-label-3 w-text-primary">Once scheduled:</div>',
            html=True,
        )

        self.assertContains(
            response,
            f'<span class="w-text-grey-600">Go-live:</span> {render_timestamp(self.go_live_at)}',
            html=True,
            count=1,
        )

        # Should show the lock message
        self.assertContains(
            response,
            "Draft state model 'I&#x27;ve been edited!' is locked and has been scheduled to go live at",
            count=1,
        )

        # Should show the lock information in the status side panel
        self.assertContains(response, "Locked by schedule")
        self.assertContains(
            response,
            '<div class="w-help-text">Currently locked and will go live on the scheduled date</div>',
            html=True,
            count=1,
        )

        html = response.content.decode()

        # Should not show the "Edit schedule" button
        self.assertTagInHTML(
            '<button type="button" data-a11y-dialog-show="schedule-publishing-dialog">Edit schedule</button>',
            html,
            count=0,
            allow_extra_attrs=True,
        )

        # Should not show button to cancel scheduled publishing
        unschedule_url = reverse(
            "wagtailsnippets_tests_draftstatemodel:revisions_unschedule",
            args=[self.test_snippet.pk, self.latest_revision.pk],
        )
        self.assertTagInHTML(
            f'<button data-action="w-action#post" data-controller="w-action" data-w-action-url-value="{unschedule_url}">Cancel scheduled publish</button>',
            html,
            count=0,
            allow_extra_attrs=True,
        )

    def test_edit_post_scheduled_for_publishing(self):
        response = self.post(
            post_data={
                "text": "I'm edited while it's locked for scheduled publishing!",
                "go_live_at": submittable_timestamp(self.go_live_at),
            }
        )

        self.test_snippet.refresh_from_db()

        # Should not create a new revision,
        # so the latest revision's content should still be the same
        self.assertEqual(self.test_snippet.latest_revision, self.latest_revision)
        self.assertEqual(
            self.test_snippet.latest_revision.content["text"],
            "I've been edited!",
        )

        # Should show a message explaining why the changes were not saved
        self.assertContains(
            response,
            "The draft state model could not be saved as it is locked",
            count=1,
        )

        # Should not show the lock message, as we already have the error message
        self.assertNotContains(
            response,
            "Draft state model 'I&#x27;ve been edited!' is locked and has been scheduled to go live at",
        )

        # Should show the lock information in the status side panel
        self.assertContains(response, "Locked by schedule")
        self.assertContains(
            response,
            '<div class="w-help-text">Currently locked and will go live on the scheduled date</div>',
            html=True,
            count=1,
        )

        html = response.content.decode()

        # Should not show the "Edit schedule" button
        self.assertTagInHTML(
            '<button type="button" data-a11y-dialog-show="schedule-publishing-dialog">Edit schedule</button>',
            html,
            count=0,
            allow_extra_attrs=True,
        )

        # Should not show button to cancel scheduled publishing as the lock message isn't shown
        unschedule_url = reverse(
            "wagtailsnippets_tests_draftstatemodel:revisions_unschedule",
            args=[self.test_snippet.pk, self.latest_revision.pk],
        )
        self.assertTagInHTML(
            f'<button data-action="w-action#post" data-controller="w-action" data-w-action-url-value="{unschedule_url}">Cancel scheduled publish</button>',
            html,
            count=0,
            allow_extra_attrs=True,
        )


class TestSnippetViewWithCustomPrimaryKey(WagtailTestUtils, TestCase):
    fixtures = ["test.json"]

    def setUp(self):
        super().setUp()
        self.login()
        self.snippet_a = StandardSnippetWithCustomPrimaryKey.objects.create(
            snippet_id="snippet/01", text="Hello"
        )
        self.snippet_b = StandardSnippetWithCustomPrimaryKey.objects.create(
            snippet_id="abc_407269_1", text="Goodbye"
        )

    def get(self, snippet, params=None):
        args = [quote(snippet.pk)]
        return self.client.get(
            reverse(snippet.snippet_viewset.get_url_name("edit"), args=args),
            params,
        )

    def post(self, snippet, post_data=None):
        args = [quote(snippet.pk)]
        return self.client.post(
            reverse(snippet.snippet_viewset.get_url_name("edit"), args=args),
            post_data,
        )

    def create(self, snippet, post_data=None, model=Advert):
        return self.client.post(
            reverse(snippet.snippet_viewset.get_url_name("add")),
            post_data,
        )

    def test_show_edit_view(self):
        for snippet in [self.snippet_a, self.snippet_b]:
            with self.subTest(snippet=snippet):
                response = self.get(snippet)
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, "wagtailsnippets/snippets/edit.html")

    def test_edit_invalid(self):
        response = self.post(self.snippet_a, post_data={"foo": "bar"})
        soup = self.get_soup(response.content)
        header_messages = soup.css.select(".messages[role='status'] ul > li")

        # the top level message should indicate that the page could not be saved
        self.assertEqual(len(header_messages), 1)
        message = header_messages[0]
        self.assertIn(
            "The standard snippet with custom primary key could not be saved due to errors.",
            message.get_text(),
        )

        # the top level message should provide a go to error button
        buttons = message.find_all("button")
        self.assertEqual(len(buttons), 1)
        self.assertEqual(buttons[0].attrs["data-controller"], "w-count w-focus")
        self.assertEqual(
            set(buttons[0].attrs["data-action"].split()),
            {"click->w-focus#focus", "wagtail:panel-init@document->w-count#count"},
        )
        self.assertIn("Go to the first error", buttons[0].get_text())

        # the errors should appear against the fields with issues
        error_messages = soup.css.select(".error-message")
        self.assertEqual(len(error_messages), 2)
        error_message = error_messages[0]
        self.assertEqual(error_message.parent["id"], "panel-child-snippet_id-errors")
        self.assertIn("This field is required", error_message.get_text())

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
        self.assertEqual(snippets.count(), 3)
        # Saving with a new primary key creates a new instance
        self.assertTrue(snippets.filter(snippet_id="snippet_id_edited").exists())
        self.assertTrue(snippets.filter(snippet_id="snippet/01").exists())

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
        self.assertEqual(snippets.count(), 3)
        self.assertEqual(snippets.order_by("snippet_id").last().text, "test snippet")

    def test_get_delete(self):
        for snippet in [self.snippet_a, self.snippet_b]:
            with self.subTest(snippet=snippet):
                response = self.client.get(
                    reverse(
                        "wagtailsnippets_snippetstests_standardsnippetwithcustomprimarykey:delete",
                        args=[quote(snippet.pk)],
                    )
                )
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(
                    response, "wagtailadmin/generic/confirm_delete.html"
                )

    def test_usage_link(self):
        for snippet in [self.snippet_a, self.snippet_b]:
            with self.subTest(snippet=snippet):
                response = self.client.get(
                    reverse(
                        "wagtailsnippets_snippetstests_standardsnippetwithcustomprimarykey:delete",
                        args=[quote(snippet.pk)],
                    )
                )
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(
                    response, "wagtailadmin/generic/confirm_delete.html"
                )
                self.assertContains(
                    response,
                    "This standard snippet with custom primary key is referenced 0 times",
                )
                self.assertContains(
                    response,
                    reverse(
                        "wagtailsnippets_snippetstests_standardsnippetwithcustomprimarykey:usage",
                        args=[quote(snippet.pk)],
                    )
                    + "?describe_on_delete=1",
                )
