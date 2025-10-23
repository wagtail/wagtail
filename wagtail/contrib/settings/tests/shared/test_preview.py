from django.test import TestCase
from django.urls import reverse

from wagtail.admin.staticfiles import versioned_static
from wagtail.models import Site
from wagtail.test.testapp.models import (
    PreviewableGenericSetting,
    PreviewableSiteSetting,
)
from wagtail.test.utils import WagtailTestUtils


class TestGenericSiteSettingPreview(WagtailTestUtils, TestCase):
    model = PreviewableGenericSetting
    other_model = PreviewableSiteSetting

    def setUp(self):
        self.user = self.login()
        site = Site.objects.get(is_default_site=True)

        PreviewableGenericSetting.objects.create(
            text="An initial previewable generic setting"
        )
        PreviewableSiteSetting.objects.create(
            text="An initial previewable site setting",
            site=site,
        )

        self.setting = self.model.objects.first()
        self.app_label = self.model._meta.app_label
        self.model_name = self.model._meta.model_name
        self.verbose_name = self.model._meta.verbose_name
        url_pk = getattr(self.setting, "site_id", self.setting.pk)
        self.preview_on_edit_url = reverse(
            "wagtailsettings:preview_on_edit",
            args=(self.app_label, self.model_name, url_pk),
        )
        self.session_key_prefix = f"wagtail-preview-{self.app_label}-{self.model_name}"
        self.edit_session_key = f"{self.session_key_prefix}-{self.setting.pk}"

        self.post_data = {
            "text": f"An edited {self.verbose_name}",
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
        soup = self.get_soup(response.content)
        # This value is accessed using the default `object` context variable
        current = soup.select_one("#current-object")
        self.assertIsNotNone(current)
        self.assertEqual(current.text.strip(), f"An edited {self.verbose_name}")
        # This value is accessed using the context processor, and it's the
        # setting being previewed
        injected = soup.select_one(f"#{self.model_name}")
        self.assertIsNotNone(injected)
        self.assertEqual(injected.text.strip(), f"An edited {self.verbose_name}")
        # The other setting is accessed using the context processor and it
        # should not be affected and still have the initial value
        other_setting = soup.select_one(f"#{self.other_model._meta.model_name}")
        self.assertIsNotNone(other_setting)
        self.assertEqual(
            other_setting.text.strip(),
            f"An initial {self.other_model._meta.verbose_name}",
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


class TestSiteSettingPreview(TestGenericSiteSettingPreview):
    model = PreviewableSiteSetting
    other_model = PreviewableGenericSetting


class TestEnablePreviewGenericSetting(WagtailTestUtils, TestCase):
    model = PreviewableGenericSetting

    def setUp(self):
        self.user = self.login()
        site = Site.objects.get(is_default_site=True)
        PreviewableGenericSetting.objects.create(
            text="An initial previewable generic setting"
        )
        PreviewableSiteSetting.objects.create(
            text="An initial previewable site setting",
            site=site,
        )
        self.setting = self.model.objects.first()
        self.url_pk = getattr(self.setting, "site_id", self.setting.pk)

    def get_url(self, name):
        return reverse(
            f"wagtailsettings:{name}",
            args=("tests", self.setting._meta.model_name, self.url_pk),
        )

    def test_show_preview_panel_on_edit(self):
        edit_url = self.get_url("edit")
        preview_url = self.get_url("preview_on_edit")
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


class TestEnablePreviewSiteSetting(TestEnablePreviewGenericSetting):
    model = PreviewableSiteSetting
