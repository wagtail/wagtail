import datetime

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time

from wagtail.admin.staticfiles import versioned_static
from wagtail.admin.views.generic.preview import PreviewOnEdit
from wagtail.models import Page, Site
from wagtail.test.testapp.models import PreviewableSiteSetting
from wagtail.test.utils import WagtailTestUtils


class TestPreview(WagtailTestUtils, TestCase):
    def setUp(self):
        self.user = self.login()

        self.default_site = Site.objects.get(is_default_site=True)
        self.setting = PreviewableSiteSetting.objects.create(
            text="A previewable site setting", site=self.default_site
        )

        self.preview_on_edit_url = reverse(
            "wagtailsettings:preview_on_edit",
            args=("tests", "previewablesitesetting", self.setting.pk),
        )
        self.session_key_prefix = "wagtail-preview-tests-previewablesitesetting"
        self.edit_session_key = f"{self.session_key_prefix}-{self.setting.pk}"

        self.post_data = {
            "text": "An edited previewable site setting",
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
        self.assertContains(response, "An edited previewable site setting")

    def test_preview_on_edit_expiry(self):
        initial_datetime = timezone.now()
        expiry_datetime = initial_datetime + datetime.timedelta(
            seconds=PreviewOnEdit.preview_expiration_timeout + 1
        )
        other_site = Site.objects.create(
            hostname="example.com", root_page=Page.objects.get(pk=2)
        )
        other_site_setting = PreviewableSiteSetting.objects.create(
            text="A new previewable site setting",
            site=other_site,
        )

        with freeze_time(initial_datetime) as frozen_datetime:
            response = self.client.post(self.preview_on_edit_url, self.post_data)
            self.assertEqual(response.status_code, 200)
            response = self.client.get(self.preview_on_edit_url)
            self.assertEqual(response.status_code, 200)

            frozen_datetime.move_to(expiry_datetime)

            preview_url = reverse(
                "wagtailsettings:preview_on_edit",
                args=("tests", "previewablesitesetting", other_site_setting.pk),
            )

            response = self.client.post(preview_url, self.post_data)
            self.assertEqual(response.status_code, 200)
            response = self.client.get(preview_url)
            self.assertEqual(response.status_code, 200)

            # Stale preview data should be removed from the session
            self.assertNotIn(self.edit_session_key, self.client.session)
            self.assertIn(
                f"{self.session_key_prefix}-{other_site_setting.pk}",
                self.client.session,
            )

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


class TestEnablePreview(WagtailTestUtils, TestCase):
    def setUp(self):
        self.user = self.login()
        self.default_site = Site.objects.get(is_default_site=True)
        self.other_site = Site.objects.create(
            hostname="example.com", root_page=Page.objects.get(pk=2)
        )
        self.single = PreviewableSiteSetting.objects.create(
            text="Single preview mode", site=self.default_site
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
