import datetime

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time

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

    def test_preview_on_create_with_invalid_data(self):
        self.assertNotIn(self.session_key_prefix, self.client.session)

        response = self.client.post(self.preview_on_add_url, {"text": ""})

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
            self.preview_on_edit_url, {**self.post_data, "text": ""}
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

        # Should show the preview panel
        self.assertContains(response, 'data-side-panel-toggle="preview"')
        self.assertContains(response, 'data-side-panel="preview"')
        self.assertContains(response, 'data-action="%s"' % preview_url)

        # Should show the iframe
        self.assertContains(
            response,
            '<iframe loading="lazy" title="Preview" class="preview-panel__iframe" data-preview-iframe aria-describedby="preview-panel-error-banner">',
        )

        # Should show the new tab button with the default mode set
        self.assertContains(response, f'href="{new_tab_url}" target="_blank"')

        # Should not show the preview mode selection
        self.assertNotContains(
            response,
            '<select id="id_preview_mode" name="preview_mode" class="preview-panel__mode-select" data-preview-mode-select>',
        )

    def test_show_preview_panel_on_create_with_multiple_modes(self):
        create_url = self.get_url(self.multiple, "add")
        preview_url = self.get_url(self.multiple, "preview_on_add")
        new_tab_url = preview_url + "?mode=alt%231"
        response = self.client.get(create_url)

        self.assertEqual(response.status_code, 200)

        # Should show the preview panel
        self.assertContains(response, 'data-side-panel-toggle="preview"')
        self.assertContains(response, 'data-side-panel="preview"')
        self.assertContains(response, 'data-action="%s"' % preview_url)

        # Should show the iframe
        self.assertContains(
            response,
            '<iframe loading="lazy" title="Preview" class="preview-panel__iframe" data-preview-iframe aria-describedby="preview-panel-error-banner">',
        )

        # Should show the new tab button with the default mode set and correctly quoted
        self.assertContains(response, f'href="{new_tab_url}" target="_blank"')

        # should show the preview mode selection
        self.assertContains(
            response,
            '<select id="id_preview_mode" name="preview_mode" class="preview-panel__mode-select" data-preview-mode-select>',
        )
        self.assertContains(response, '<option value="">Normal</option>')

        # Should respect the default_preview_mode
        self.assertContains(
            response, '<option value="alt#1" selected>Alternate</option>'
        )

    def test_show_preview_panel_on_edit_with_single_mode(self):
        edit_url = self.get_url(self.single, "edit", args=(self.single.pk,))
        preview_url = self.get_url(
            self.single, "preview_on_edit", args=(self.multiple.pk,)
        )
        new_tab_url = preview_url + "?mode="
        response = self.client.get(edit_url)

        self.assertEqual(response.status_code, 200)

        # Should show the preview panel
        self.assertContains(response, 'data-side-panel-toggle="preview"')
        self.assertContains(response, 'data-side-panel="preview"')
        self.assertContains(response, 'data-action="%s"' % preview_url)

        # Should show the iframe
        self.assertContains(
            response,
            '<iframe loading="lazy" title="Preview" class="preview-panel__iframe" data-preview-iframe aria-describedby="preview-panel-error-banner">',
        )

        # Should show the new tab button with the default mode set
        self.assertContains(response, f'href="{new_tab_url}" target="_blank"')

        # Should not show the preview mode selection
        self.assertNotContains(
            response,
            '<select id="id_preview_mode" name="preview_mode" class="preview-panel__mode-select" data-preview-mode-select>',
        )

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
        self.assertContains(response, 'data-action="%s"' % preview_url)

        # Should show the iframe
        self.assertContains(
            response,
            '<iframe loading="lazy" title="Preview" class="preview-panel__iframe" data-preview-iframe aria-describedby="preview-panel-error-banner">',
        )

        # Should show the new tab button with the default mode set and correctly quoted
        self.assertContains(response, f'href="{new_tab_url}" target="_blank"')

        # should show the preview mode selection
        self.assertContains(
            response,
            '<select id="id_preview_mode" name="preview_mode" class="preview-panel__mode-select" data-preview-mode-select>',
        )
        self.assertContains(response, '<option value="">Normal</option>')

        # Should respect the default_preview_mode
        self.assertContains(
            response, '<option value="alt#1" selected>Alternate</option>'
        )

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
        self.assertNotContains(response, 'data-action="%s"' % preview_url)

    def test_disable_preview_on_edit(self):
        response = self.client.get(self.get_url("edit", args=(self.snippet.pk,)))
        self.assertEqual(response.status_code, 200)

        preview_url = self.get_url("preview_on_edit", args=(self.snippet.pk,))
        self.assertNotContains(response, 'data-side-panel-toggle="preview"')
        self.assertNotContains(response, 'data-side-panel="preview"')
        self.assertNotContains(response, 'data-action="%s"' % preview_url)

    def test_disable_preview_on_revisions_list(self):
        latest_revision = self.snippet.save_revision(log_action=True)

        response = self.client.get(self.get_url("history", args=(self.snippet.pk,)))
        preview_url = self.get_url(
            "revisions_view", args=(self.snippet.pk, latest_revision.id)
        )
        self.assertNotContains(response, "Preview")
        self.assertNotContains(response, preview_url)


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
