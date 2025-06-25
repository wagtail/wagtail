import datetime

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time

from wagtail.admin.staticfiles import versioned_static
from wagtail.admin.templatetags.wagtailadmin_tags import absolute_static
from wagtail.admin.views.generic.preview import PreviewOnEdit
from wagtail.test.testapp.models import (
    EventCategory,
    MultiPreviewModesModel,
    NonPreviewableModel,
    PreviewableModel,
    RevisableModel,
)
from wagtail.test.utils import WagtailTestUtils


class TestPreview(WagtailTestUtils, TestCase):
    def setUp(self):
        self.user = self.login()

        self.meetings_category = EventCategory.objects.create(name="Meetings")
        self.parties_category = EventCategory.objects.create(name="Parties")
        self.holidays_category = EventCategory.objects.create(name="Holidays")
        self.snippet = PreviewableModel.objects.create(text="A previewable snippet")

        self.preview_on_add_url = reverse(
            "wagtailsnippets_tests_previewablemodel:preview_on_add"
        )
        self.preview_on_edit_url = reverse(
            "wagtailsnippets_tests_previewablemodel:preview_on_edit",
            args=(self.snippet.pk,),
        )
        self.session_key_prefix = "wagtail-preview-tests-previewablemodel"
        self.edit_session_key = f"{self.session_key_prefix}-{self.snippet.pk}"

        self.post_data = {
            "text": "An edited previewable snippet",
            "categories": [self.parties_category.id, self.holidays_category.id],
        }

    def test_preview_on_create_with_no_session_data(self):
        self.assertNotIn(self.session_key_prefix, self.client.session)

        response = self.client.get(self.preview_on_add_url)

        # The preview should be unavailable
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/generic/preview_error.html")
        self.assertContains(
            response,
            "<title>Preview not available - Wagtail</title>",
            html=True,
        )
        self.assertContains(
            response,
            '<h1 class="preview-error__title">Preview not available</h1>',
            html=True,
        )
        self.assertNotContains(response, versioned_static("wagtailadmin/js/icons.js"))

    def test_preview_on_create_with_invalid_data(self):
        self.assertNotIn(self.session_key_prefix, self.client.session)

        response = self.client.post(self.preview_on_add_url, {"categories": [999999]})

        # Check the JSON response
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode(),
            {"is_valid": False, "is_available": False},
        )

        # The invalid data should not be saved in the session
        self.assertNotIn(self.session_key_prefix, self.client.session)

        response = self.client.get(self.preview_on_add_url)

        # The preview should still be unavailable
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/generic/preview_error.html")
        self.assertContains(
            response,
            "<title>Preview not available - Wagtail</title>",
            html=True,
        )
        self.assertContains(
            response,
            '<h1 class="preview-error__title">Preview not available</h1>',
            html=True,
        )
        self.assertNotContains(response, versioned_static("wagtailadmin/js/icons.js"))

    def test_preview_on_create_with_m2m_field(self):
        response = self.client.post(self.preview_on_add_url, self.post_data)

        # Check the JSON response
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode(),
            {"is_valid": True, "is_available": True},
        )

        # Check the user can refresh the preview
        self.assertIn(self.session_key_prefix, self.client.session)

        response = self.client.get(self.preview_on_add_url)

        # Check the HTML response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tests/previewable_model.html")
        self.assertContains(response, "An edited previewable snippet")
        self.assertContains(response, "<li>Parties</li>")
        self.assertContains(response, "<li>Holidays</li>")

    def test_preview_on_create_with_deferred_required_fields(self):
        response = self.client.post(
            self.preview_on_add_url,
            {"categories": [self.holidays_category.id]},
        )

        # Check the JSON response
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode(),
            {"is_valid": True, "is_available": True},
        )

        # Check the user can refresh the preview
        self.assertIn(self.session_key_prefix, self.client.session)

        response = self.client.get(self.preview_on_add_url)

        # Check the HTML response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tests/previewable_model.html")

        # The text is empty
        self.assertContains(response, "<title>(Default Preview)</title>", html=True)
        self.assertContains(response, "<h1></h1>", html=True)

        # The category is Holidays (only)
        self.assertNotContains(response, "<li>Parties</li>")
        self.assertContains(response, "<li>Holidays</li>")

    def test_preview_on_edit_with_m2m_field(self):
        response = self.client.post(self.preview_on_edit_url, self.post_data)

        # Check the JSON response
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode(),
            {"is_valid": True, "is_available": True},
        )

        # Check the user can refresh the preview
        self.assertIn(self.edit_session_key, self.client.session)

        response = self.client.get(self.preview_on_edit_url)

        # Check the HTML response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tests/previewable_model.html")
        self.assertContains(response, "An edited previewable snippet")
        self.assertContains(response, "<li>Parties</li>")
        self.assertContains(response, "<li>Holidays</li>")

    def test_preview_on_edit_with_valid_then_invalid_data(self):
        response = self.client.post(self.preview_on_edit_url, self.post_data)

        # Check the JSON response
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode(),
            {"is_valid": True, "is_available": True},
        )

        # Send an invalid update request
        response = self.client.post(
            self.preview_on_edit_url, {**self.post_data, "categories": [999999]}
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode(),
            {"is_valid": False, "is_available": True},
        )

        # Check the user can still see the preview with the last valid data
        self.assertIn(self.edit_session_key, self.client.session)

        response = self.client.get(self.preview_on_edit_url)

        # Check the HTML response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tests/previewable_model.html")
        self.assertContains(response, "An edited previewable snippet")
        self.assertContains(response, "<li>Parties</li>")
        self.assertContains(response, "<li>Holidays</li>")

    def test_preview_on_edit_with_deferred_required_fields(self):
        response = self.client.post(
            self.preview_on_edit_url,
            {"categories": [self.holidays_category.id]},
        )

        # Check the JSON response
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode(),
            {"is_valid": True, "is_available": True},
        )

        # Check the user can refresh the preview
        self.assertIn(self.edit_session_key, self.client.session)

        response = self.client.get(self.preview_on_edit_url)

        # Check the HTML response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tests/previewable_model.html")

        # The text is empty
        self.assertContains(response, "<title>(Default Preview)</title>", html=True)
        self.assertContains(response, "<h1></h1>", html=True)

        # The category is Holidays (only)
        self.assertNotContains(response, "<li>Parties</li>")
        self.assertContains(response, "<li>Holidays</li>")

    def test_preview_on_edit_expiry(self):
        initial_datetime = timezone.now()
        expiry_datetime = initial_datetime + datetime.timedelta(
            seconds=PreviewOnEdit.preview_expiration_timeout + 1
        )

        new_snippet = PreviewableModel.objects.create(text="A new previewable snippet")

        with freeze_time(initial_datetime) as frozen_datetime:
            response = self.client.post(self.preview_on_edit_url, self.post_data)
            self.assertEqual(response.status_code, 200)
            response = self.client.get(self.preview_on_edit_url)
            self.assertEqual(response.status_code, 200)

            frozen_datetime.move_to(expiry_datetime)

            preview_url = reverse(
                "wagtailsnippets_tests_previewablemodel:preview_on_edit",
                args=(new_snippet.pk,),
            )

            response = self.client.post(preview_url, self.post_data)
            self.assertEqual(response.status_code, 200)
            response = self.client.get(preview_url)
            self.assertEqual(response.status_code, 200)

            # Stale preview data should be removed from the session
            self.assertNotIn(self.edit_session_key, self.client.session)
            self.assertIn(
                f"{self.session_key_prefix}-{new_snippet.pk}",
                self.client.session,
            )

    def test_preview_on_create_clear_preview_data(self):
        # Set a fake preview session data for the page
        self.client.session[self.session_key_prefix] = "test data"

        response = self.client.delete(self.preview_on_add_url)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode(),
            {"success": True},
        )

        # The data should no longer exist in the session
        self.assertNotIn(self.session_key_prefix, self.client.session)

        response = self.client.get(self.preview_on_add_url)

        # The preview should be unavailable
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/generic/preview_error.html")
        self.assertContains(
            response,
            "<title>Preview not available - Wagtail</title>",
            html=True,
        )
        self.assertContains(
            response,
            '<h1 class="preview-error__title">Preview not available</h1>',
            html=True,
        )
        self.assertNotContains(response, versioned_static("wagtailadmin/js/icons.js"))

    def test_preview_on_edit_clear_preview_data(self):
        # Set a fake preview session data for the page
        self.client.session[self.edit_session_key] = "test data"

        response = self.client.delete(self.preview_on_edit_url)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode(),
            {"success": True},
        )

        # The data should no longer exist in the session
        self.assertNotIn(self.edit_session_key, self.client.session)

        response = self.client.get(self.preview_on_edit_url)

        # The preview should be unavailable
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/generic/preview_error.html")
        self.assertContains(
            response,
            "<title>Preview not available - Wagtail</title>",
            html=True,
        )
        self.assertContains(
            response,
            '<h1 class="preview-error__title">Preview not available</h1>',
            html=True,
        )
        self.assertNotContains(response, versioned_static("wagtailadmin/js/icons.js"))

    @override_settings(WAGTAILADMIN_BASE_URL="http://other.example.com:8000")
    def test_userbar_in_preview(self):
        self.client.post(self.preview_on_edit_url, self.post_data)
        response = self.client.get(self.preview_on_edit_url)

        # Check the HTML response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tests/previewable_model.html")
        soup = self.get_soup(response.content)
        userbar = soup.select_one("wagtail-userbar")
        self.assertIsNotNone(userbar)

        # Absolute URLs to static assets should be rendered with the original
        # request's host as the base URL, as snippets have no concept of the
        # current site or fully qualified URLs.

        css_links = soup.select("link[rel='stylesheet']")
        self.assertEqual(
            [link.get("href") for link in css_links],
            [
                absolute_static("wagtailadmin/css/core.css"),
                "/path/to/my/custom.css",
            ],
        )
        scripts = soup.select("script[src]")
        self.assertEqual(
            [script.get("src") for script in scripts],
            [
                absolute_static("wagtailadmin/js/vendor.js"),
                absolute_static("wagtailadmin/js/userbar.js"),
            ],
        )

    def test_preview_revision(self):
        snippet = MultiPreviewModesModel.objects.create(text="Multiple modes")
        revision = snippet.save_revision(log_action=True)
        response = self.client.get(
            reverse(
                "wagtailsnippets_tests_multipreviewmodesmodel:revisions_view",
                args=(snippet.pk, revision.id),
            )
        )

        self.assertEqual(response.status_code, 200)

        # Should respect the default_preview_mode
        self.assertTemplateUsed(response, "tests/previewable_model_alt.html")
        self.assertContains(response, "Multiple modes (Alternate Preview)")


class TestEnablePreview(WagtailTestUtils, TestCase):
    def setUp(self):
        self.user = self.login()
        self.single = PreviewableModel.objects.create(text="Single preview mode")
        self.multiple = MultiPreviewModesModel.objects.create(
            text="Multiple preview modes"
        )

    def get_url(self, snippet, name, args=None):
        model_name = type(snippet)._meta.model_name
        return reverse(f"wagtailsnippets_tests_{model_name}:{name}", args=args)

    def test_show_preview_panel_on_create_with_single_mode(self):
        create_url = self.get_url(self.single, "add")
        preview_url = self.get_url(self.single, "preview_on_add")
        new_tab_url = preview_url + "?mode="
        response = self.client.get(create_url)

        self.assertEqual(response.status_code, 200)

        # Should have the preview side panel toggle button
        soup = self.get_soup(response.content)
        self.assertIsNotNone(soup.select_one('[data-side-panel="preview"]'))
        toggle_button = soup.find("button", {"data-side-panel-toggle": "preview"})
        self.assertIsNotNone(toggle_button)
        self.assertEqual("w-tooltip w-kbd", toggle_button["data-controller"])
        self.assertEqual("mod+p", toggle_button["data-w-kbd-key-value"])

        # Should set the preview URL value on the controller
        controller = soup.select_one('[data-controller="w-preview"]')
        self.assertIsNotNone(controller)
        self.assertEqual(controller.get("data-w-preview-url-value"), preview_url)

        # Should show the iframe
        iframe = controller.select_one("#w-preview-iframe")
        self.assertIsNotNone(iframe)
        self.assertEqual(iframe.get("data-w-preview-target"), "iframe")

        # Should show the new tab button with the default mode set
        new_tab_button = controller.select_one('a[data-w-preview-target="newTab"]')
        self.assertIsNotNone(new_tab_button)
        self.assertEqual(new_tab_button["href"], new_tab_url)
        self.assertEqual(new_tab_button["target"], "_blank")

        # Should not show the preview mode selection
        mode_select = controller.select_one('[data-w-preview-target="mode"]')
        self.assertIsNone(mode_select)

    def test_show_preview_panel_on_create_with_multiple_modes(self):
        create_url = self.get_url(self.multiple, "add")
        preview_url = self.get_url(self.multiple, "preview_on_add")
        new_tab_url = preview_url + "?mode=alt%231"
        response = self.client.get(create_url)

        self.assertEqual(response.status_code, 200)

        # Should show the preview panel
        self.assertContains(response, 'data-side-panel-toggle="preview"')
        self.assertContains(response, 'data-side-panel="preview"')

        # Should set the preview URL value on the controller
        soup = self.get_soup(response.content)
        controller = soup.select_one('[data-controller="w-preview"]')
        self.assertIsNotNone(controller)
        self.assertEqual(controller.get("data-w-preview-url-value"), preview_url)

        # Should show the iframe
        iframe = controller.select_one("#w-preview-iframe")
        self.assertIsNotNone(iframe)
        self.assertEqual(iframe.get("data-w-preview-target"), "iframe")

        # Should show the new tab button with the default mode set and correctly quoted
        new_tab_button = controller.select_one('a[data-w-preview-target="newTab"]')
        self.assertIsNotNone(new_tab_button)
        self.assertEqual(new_tab_button["href"], new_tab_url)
        self.assertEqual(new_tab_button["target"], "_blank")

        # should show the preview mode selection with the default mode selected
        mode_select = controller.select_one('[data-w-preview-target="mode"]')
        self.assertIsNotNone(mode_select)
        self.assertEqual(mode_select["id"], "id_preview_mode")
        default_option = mode_select.select_one('option[value="alt#1"]')
        self.assertIsNotNone(default_option)
        self.assertIsNotNone(default_option.get("selected"))
        other_option = mode_select.select_one('option[value=""]')
        self.assertIsNotNone(other_option)
        self.assertEqual(other_option.text.strip(), "Normal")
        self.assertIsNone(other_option.get("selected"))

    def test_show_preview_panel_on_edit_with_single_mode(self):
        edit_url = self.get_url(self.single, "edit", args=(self.single.pk,))
        preview_url = self.get_url(
            self.single, "preview_on_edit", args=(self.multiple.pk,)
        )
        new_tab_url = preview_url + "?mode="
        response = self.client.get(edit_url)

        self.assertEqual(response.status_code, 200)

        # Should have the preview side panel toggle button
        soup = self.get_soup(response.content)
        self.assertIsNotNone(soup.select_one('[data-side-panel="preview"]'))
        toggle_button = soup.find("button", {"data-side-panel-toggle": "preview"})
        self.assertIsNotNone(toggle_button)
        self.assertEqual("w-tooltip w-kbd", toggle_button["data-controller"])
        self.assertEqual("mod+p", toggle_button["data-w-kbd-key-value"])

        # Should set the preview URL value on the controller
        controller = soup.select_one('[data-controller="w-preview"]')
        self.assertIsNotNone(controller)
        self.assertEqual(controller.get("data-w-preview-url-value"), preview_url)

        # Should show the iframe
        iframe = controller.select_one("#w-preview-iframe")
        self.assertIsNotNone(iframe)
        self.assertEqual(iframe.get("data-w-preview-target"), "iframe")

        # Should show the new tab button with the default mode set
        new_tab_button = controller.select_one('a[data-w-preview-target="newTab"]')
        self.assertIsNotNone(new_tab_button)
        self.assertEqual(new_tab_button["href"], new_tab_url)
        self.assertEqual(new_tab_button["target"], "_blank")

        # Should not show the preview mode selection
        mode_select = controller.select_one('[data-w-preview-target="mode"]')
        self.assertIsNone(mode_select)

    def test_show_preview_panel_on_edit_with_multiple_modes(self):
        edit_url = self.get_url(self.multiple, "edit", args=(self.multiple.pk,))
        preview_url = self.get_url(
            self.multiple, "preview_on_edit", args=(self.multiple.pk,)
        )
        new_tab_url = preview_url + "?mode=alt%231"
        response = self.client.get(edit_url)

        self.assertEqual(response.status_code, 200)

        # Should show the preview panel
        self.assertContains(response, 'data-side-panel-toggle="preview"')
        self.assertContains(response, 'data-side-panel="preview"')

        # Should set the preview URL value on the controller
        soup = self.get_soup(response.content)
        controller = soup.select_one('[data-controller="w-preview"]')
        self.assertIsNotNone(controller)
        self.assertEqual(controller.get("data-w-preview-url-value"), preview_url)

        # Should have a default interval of 500ms and should render the hidden spinner
        interval_value = controller.get("data-w-preview-auto-update-interval-value")
        self.assertEqual(interval_value, "500")
        spinner = controller.select_one('[data-w-preview-target="spinner"]')
        self.assertIsNotNone(spinner)
        self.assertIsNotNone(spinner.get("hidden"))
        self.assertIsNotNone(spinner.select_one("svg.icon-spinner"))

        # Should not render any buttons (the refresh button in particular)
        refresh_button = controller.select_one("button")
        self.assertIsNone(refresh_button)

        # Should show the iframe
        iframe = controller.select_one("#w-preview-iframe")
        self.assertIsNotNone(iframe)
        self.assertEqual(iframe.get("data-w-preview-target"), "iframe")

        # Should show the new tab button with the default mode set and correctly quoted
        new_tab_button = controller.select_one('a[data-w-preview-target="newTab"]')
        self.assertIsNotNone(new_tab_button)
        self.assertEqual(new_tab_button["href"], new_tab_url)
        self.assertEqual(new_tab_button["target"], "_blank")

        # should show the preview mode selection with the default mode selected
        mode_select = controller.select_one('[data-w-preview-target="mode"]')
        self.assertIsNotNone(mode_select)
        self.assertEqual(mode_select["id"], "id_preview_mode")
        default_option = mode_select.select_one('option[value="alt#1"]')
        self.assertIsNotNone(default_option)
        self.assertIsNotNone(default_option.get("selected"))
        other_option = mode_select.select_one('option[value=""]')
        self.assertIsNotNone(other_option)
        self.assertEqual(other_option.text.strip(), "Normal")
        self.assertIsNone(other_option.get("selected"))

    @override_settings(WAGTAIL_AUTO_UPDATE_PREVIEW_INTERVAL=12345)
    def test_custom_auto_update_interval(self):
        edit_url = self.get_url(self.single, "edit", args=(self.single.pk,))
        preview_url = self.get_url(
            self.single, "preview_on_edit", args=(self.multiple.pk,)
        )
        response = self.client.get(edit_url)

        self.assertEqual(response.status_code, 200)

        soup = self.get_soup(response.content)

        # Should set the custom interval value on the controller
        controller = soup.select_one('[data-controller="w-preview"]')
        self.assertIsNotNone(controller)
        self.assertEqual(controller.get("data-w-preview-url-value"), preview_url)
        interval_value = controller.get("data-w-preview-auto-update-interval-value")
        self.assertEqual(interval_value, "12345")

        # Should render the spinner
        spinner = controller.select_one('[data-w-preview-target="spinner"]')
        self.assertIsNotNone(spinner)
        self.assertIsNotNone(spinner.get("hidden"))
        self.assertIsNotNone(spinner.select_one("svg.icon-spinner"))

        # Should not render any buttons (the refresh button in particular)
        refresh_button = controller.select_one("button")
        self.assertIsNone(refresh_button)

    @override_settings(WAGTAIL_AUTO_UPDATE_PREVIEW_INTERVAL=0)
    def test_disable_auto_update_using_zero_interval(self):
        edit_url = self.get_url(self.single, "edit", args=(self.single.pk,))
        preview_url = self.get_url(
            self.single, "preview_on_edit", args=(self.multiple.pk,)
        )
        response = self.client.get(edit_url)

        self.assertEqual(response.status_code, 200)

        soup = self.get_soup(response.content)

        # Should set the interval value on the controller
        controller = soup.select_one('[data-controller="w-preview"]')
        self.assertIsNotNone(controller)
        self.assertEqual(controller.get("data-w-preview-url-value"), preview_url)
        interval_value = controller.get("data-w-preview-auto-update-interval-value")
        self.assertEqual(interval_value, "0")

        # Should not render the spinner
        spinner = controller.select_one('[data-w-preview-target="spinner"]')
        self.assertIsNone(spinner)

        # Should render the refresh button with the w-progress controller
        refresh_button = controller.select_one("button")
        self.assertIsNotNone(refresh_button)
        self.assertEqual(refresh_button.get("data-controller"), "w-progress")
        self.assertEqual(refresh_button.text.strip(), "Refresh")

    def test_show_preview_on_revisions_list(self):
        latest_revision = self.multiple.save_revision(log_action=True)
        history_url = self.get_url(self.multiple, "history", args=(self.multiple.pk,))
        preview_url = self.get_url(
            self.multiple,
            "revisions_view",
            args=(self.multiple.pk, latest_revision.id),
        )

        response = self.client.get(history_url)
        self.assertContains(response, "Preview")
        self.assertContains(response, preview_url)


class TestDisablePreviewWithEmptyModes(WagtailTestUtils, TestCase):
    """
    Preview can be disabled by setting preview_modes to an empty list.
    """

    # NonPreviewableModel has preview_modes = []
    model = NonPreviewableModel

    def setUp(self):
        self.user = self.login()
        self.snippet = self.model.objects.create(text="A non-previewable snippet")
        self.model_name = self.model._meta.model_name

    def get_url(self, name, args=None):
        return reverse(f"wagtailsnippets_tests_{self.model_name}:{name}", args=args)

    def test_disable_preview_on_create(self):
        response = self.client.get(self.get_url("add"))
        self.assertEqual(response.status_code, 200)

        preview_url = self.get_url("preview_on_add")
        self.assertNotContains(response, 'data-side-panel-toggle="preview"')
        self.assertNotContains(response, 'data-side-panel="preview"')
        self.assertNotContains(response, 'data-controller="w-preview"')
        self.assertNotContains(response, preview_url)

    def test_disable_preview_on_edit(self):
        response = self.client.get(self.get_url("edit", args=(self.snippet.pk,)))
        self.assertEqual(response.status_code, 200)

        preview_url = self.get_url("preview_on_edit", args=(self.snippet.pk,))
        self.assertNotContains(response, 'data-side-panel-toggle="preview"')
        self.assertNotContains(response, 'data-side-panel="preview"')
        self.assertNotContains(response, 'data-controller="w-preview"')
        self.assertNotContains(response, preview_url)

    def test_disable_preview_on_revisions_list(self):
        latest_revision = self.snippet.save_revision(log_action=True)

        response = self.client.get(self.get_url("history", args=(self.snippet.pk,)))
        preview_url = self.get_url(
            "revisions_view", args=(self.snippet.pk, latest_revision.id)
        )

        self.assertNotContains(response, preview_url)

        soup = self.get_soup(response.content)

        preview_link = soup.find("a", {"href": preview_url})
        self.assertIsNone(preview_link)


class TestDisablePreviewWithoutMixin(TestDisablePreviewWithEmptyModes):
    """
    Preview can be disabled by not extending PreviewableMixin.
    """

    # RevisableModel does not extend PreviewableMixin
    model = RevisableModel

    def get_url(self, name, args=None):
        # Cannot use reverse() as the urls are not registered
        # if the model does not extend PreviewableMixin
        if name == "preview_on_add":
            return f"/admin/snippets/tests/{self.model_name}/preview/"
        if name == "preview_on_edit":
            return f"/admin/snippets/tests/{self.model_name}/preview/{args[0]}/"
        if name == "revisions_view":
            return (
                f"/admin/snippets/tests/{self.model_name}/history/"
                f"{args[0]}/revisions/{args[1]}/view/"
            )
        return super().get_url(name, args)
