from django.test import TestCase, override_settings
from django.urls import reverse

from wagtail.admin.staticfiles import versioned_static
from wagtail.test.testapp.models import (
    MultiPreviewModesGenericSetting,
    PreviewableGenericSetting,
)
from wagtail.test.utils import WagtailTestUtils


class TestPreview(WagtailTestUtils, TestCase):
    def setUp(self):
        self.user = self.login()

        self.setting = PreviewableGenericSetting.objects.create(
            text="A previewable setting"
        )
        self.preview_on_edit_url = reverse(
            "wagtailsettings:preview_on_edit",
            args=(
                "tests",
                "previewablegenericsetting",
                self.setting.pk,
            ),
        )
        self.session_key_prefix = "wagtail-preview-tests-previewablegenericsetting"
        self.edit_session_key = f"{self.session_key_prefix}-{self.setting.pk}"

        self.post_data = {
            "text": "An edited previewable setting",
        }

    def test_preview_on_edit_with_valid_then_invalid_data(self):
        response = self.client.post(self.preview_on_edit_url, self.post_data)

        # Check the JSON response
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode(),
            {"is_valid": True, "is_available": True},
        )

        # Send an invalid update request
        response = self.client.post(self.preview_on_edit_url, {})
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
        self.assertTemplateUsed(response, "tests/previewable_setting.html")
        self.assertContains(
            response, "<h1>An edited previewable setting</h1>", html=True
        )
        self.assertContains(
            response, "<span>An edited previewable setting</span>", html=True
        )

    def test_preview_on_edit_clear_preview_data(self):
        # Set a fake preview session data for the setting
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


class TestEnablePreview(WagtailTestUtils, TestCase):
    def setUp(self):
        self.user = self.login()
        self.single = PreviewableGenericSetting.objects.create(
            text="Single preview mode"
        )
        self.multiple = MultiPreviewModesGenericSetting.objects.create(
            text="Multiple preview modes"
        )

    def get_url(self, setting, name):
        model_name = type(setting)._meta.model_name
        return reverse(
            f"wagtailsettings:{name}",
            args=("tests", model_name, setting.pk),
        )

    def test_show_preview_panel_on_edit_with_single_mode(self):
        edit_url = self.get_url(self.single, "edit")
        preview_url = self.get_url(self.single, "preview_on_edit")
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

        # Should have the checks side panel
        soup = self.get_soup(response.content)
        self.assertIsNotNone(soup.select_one('[data-side-panel="checks"]'))
        toggle_button = soup.find("button", {"data-side-panel-toggle": "checks"})
        self.assertIsNotNone(toggle_button)

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
        edit_url = self.get_url(self.multiple, "edit")
        preview_url = self.get_url(self.multiple, "preview_on_edit")
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
        edit_url = self.get_url(self.single, "edit")
        preview_url = self.get_url(self.single, "preview_on_edit")
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
        edit_url = self.get_url(self.single, "edit")
        preview_url = self.get_url(self.single, "preview_on_edit")
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
