import datetime
from functools import wraps

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time

from wagtail.admin.views.pages.preview import PreviewOnEdit
from wagtail.models import Page
from wagtail.test.testapp.models import (
    EventCategory,
    MultiPreviewModesPage,
    SimplePage,
    StreamPage,
)
from wagtail.test.utils import WagtailTestUtils


class TestIssue2599(TestCase, WagtailTestUtils):
    """
    When previewing a page on creation, we need to assign it a path value consistent with its
    (future) position in the tree. The naive way of doing this is to give it an index number
    one more than numchild - however, index numbers are not reassigned on page deletion, so
    this can result in a path that collides with an existing page (which is invalid).
    """

    def test_issue_2599(self):
        homepage = Page.objects.get(id=2)

        child1 = Page(title="child1")
        homepage.add_child(instance=child1)
        child2 = Page(title="child2")
        homepage.add_child(instance=child2)

        child1.delete()

        self.login()
        post_data = {
            "title": "New page!",
            "content": "Some content",
            "slug": "hello-world",
            "action-submit": "Submit",
        }
        preview_url = reverse(
            "wagtailadmin_pages:preview_on_add",
            args=("tests", "simplepage", homepage.id),
        )
        response = self.client.post(preview_url, post_data)

        # Check the JSON response
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode(),
            {"is_valid": True, "is_available": True},
        )

        response = self.client.get(preview_url)

        # Check the HTML response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tests/simple_page.html")
        self.assertContains(response, "New page!")

        # Check that the treebeard attributes were set correctly on the page object
        self.assertEqual(response.context["self"].depth, homepage.depth + 1)
        self.assertTrue(response.context["self"].path.startswith(homepage.path))
        self.assertEqual(response.context["self"].get_parent(), homepage)


def clear_edit_handler(page_cls):
    def decorator(fn):
        @wraps(fn)
        def decorated(*args, **kwargs):
            # Clear any old panel definitions generated
            page_cls.get_edit_handler.cache_clear()
            try:
                fn(*args, **kwargs)
            finally:
                # Clear the bad panel definition generated just now
                page_cls.get_edit_handler.cache_clear()

        return decorated

    return decorator


class TestPreview(TestCase, WagtailTestUtils):
    fixtures = ["test.json"]

    def setUp(self):
        self.meetings_category = EventCategory.objects.create(name="Meetings")
        self.parties_category = EventCategory.objects.create(name="Parties")
        self.holidays_category = EventCategory.objects.create(name="Holidays")

        self.home_page = Page.objects.get(url_path="/home/")
        self.event_page = Page.objects.get(url_path="/home/events/christmas/")

        self.user = self.login()

        self.post_data = {
            "title": "Beach party",
            "slug": "beach-party",
            "body": """{"entityMap": {},"blocks": [
                {"inlineStyleRanges": [], "text": "party on wayne", "depth": 0, "type": "unstyled", "key": "00000", "entityRanges": []}
            ]}""",
            "date_from": "2017-08-01",
            "audience": "public",
            "location": "the beach",
            "cost": "six squid",
            "carousel_items-TOTAL_FORMS": 0,
            "carousel_items-INITIAL_FORMS": 0,
            "carousel_items-MIN_NUM_FORMS": 0,
            "carousel_items-MAX_NUM_FORMS": 0,
            "speakers-TOTAL_FORMS": 0,
            "speakers-INITIAL_FORMS": 0,
            "speakers-MIN_NUM_FORMS": 0,
            "speakers-MAX_NUM_FORMS": 0,
            "related_links-TOTAL_FORMS": 0,
            "related_links-INITIAL_FORMS": 0,
            "related_links-MIN_NUM_FORMS": 0,
            "related_links-MAX_NUM_FORMS": 0,
            "head_counts-TOTAL_FORMS": 0,
            "head_counts-INITIAL_FORMS": 0,
            "head_counts-MIN_NUM_FORMS": 0,
            "head_counts-MAX_NUM_FORMS": 0,
            "categories": [self.parties_category.id, self.holidays_category.id],
            "comments-TOTAL_FORMS": 0,
            "comments-INITIAL_FORMS": 0,
            "comments-MIN_NUM_FORMS": 0,
            "comments-MAX_NUM_FORMS": 1000,
        }

    def test_preview_on_create_with_no_session_data(self):
        preview_url = reverse(
            "wagtailadmin_pages:preview_on_add",
            args=("tests", "eventpage", self.home_page.id),
        )

        preview_session_key = "wagtail-preview-tests-eventpage-{}".format(
            self.home_page.id
        )
        self.assertNotIn(preview_session_key, self.client.session)

        response = self.client.get(preview_url)

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
        preview_url = reverse(
            "wagtailadmin_pages:preview_on_add",
            args=("tests", "eventpage", self.home_page.id),
        )

        preview_session_key = "wagtail-preview-tests-eventpage-{}".format(
            self.home_page.id
        )
        self.assertNotIn(preview_session_key, self.client.session)

        response = self.client.post(preview_url, {**self.post_data, "title": ""})

        # Check the JSON response
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode(),
            {"is_valid": False, "is_available": False},
        )

        # The invalid data should not be saved in the session
        self.assertNotIn(preview_session_key, self.client.session)

        response = self.client.get(preview_url)

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
        preview_url = reverse(
            "wagtailadmin_pages:preview_on_add",
            args=("tests", "eventpage", self.home_page.id),
        )
        response = self.client.post(preview_url, self.post_data)

        # Check the JSON response
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode(),
            {"is_valid": True, "is_available": True},
        )

        # Check the user can refresh the preview
        preview_session_key = "wagtail-preview-tests-eventpage-{}".format(
            self.home_page.id
        )
        self.assertIn(preview_session_key, self.client.session)

        response = self.client.get(preview_url)

        # Check the HTML response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tests/event_page.html")
        self.assertContains(response, "Beach party")
        self.assertContains(response, "<li>Parties</li>")
        self.assertContains(response, "<li>Holidays</li>")

    def test_preview_on_edit_with_m2m_field(self):
        preview_url = reverse(
            "wagtailadmin_pages:preview_on_edit", args=(self.event_page.id,)
        )
        response = self.client.post(preview_url, self.post_data)

        # Check the JSON response
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode(),
            {"is_valid": True, "is_available": True},
        )

        # Check the user can refresh the preview
        preview_session_key = "wagtail-preview-{}".format(self.event_page.id)
        self.assertIn(preview_session_key, self.client.session)

        response = self.client.get(preview_url)

        # Check the HTML response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tests/event_page.html")
        self.assertContains(response, "Beach party")
        self.assertContains(response, "<li>Parties</li>")
        self.assertContains(response, "<li>Holidays</li>")

    def test_preview_on_edit_with_valid_then_invalid_data(self):
        preview_url = reverse(
            "wagtailadmin_pages:preview_on_edit", args=(self.event_page.id,)
        )
        response = self.client.post(preview_url, self.post_data)

        # Check the JSON response
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode(),
            {"is_valid": True, "is_available": True},
        )

        # Send an invalid update request
        response = self.client.post(preview_url, {**self.post_data, "title": ""})
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode(),
            {"is_valid": False, "is_available": True},
        )

        # Check the user can still see the preview with the last valid data
        preview_session_key = "wagtail-preview-{}".format(self.event_page.id)
        self.assertIn(preview_session_key, self.client.session)

        response = self.client.get(preview_url)

        # Check the HTML response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tests/event_page.html")
        self.assertContains(response, "Beach party")
        self.assertContains(response, "<li>Parties</li>")
        self.assertContains(response, "<li>Holidays</li>")

    def test_preview_on_edit_expiry(self):
        initial_datetime = timezone.now()
        expiry_datetime = initial_datetime + datetime.timedelta(
            seconds=PreviewOnEdit.preview_expiration_timeout + 1
        )

        with freeze_time(initial_datetime) as frozen_datetime:
            preview_url = reverse(
                "wagtailadmin_pages:preview_on_edit", args=(self.event_page.id,)
            )
            response = self.client.post(preview_url, self.post_data)

            # Check the JSON response
            self.assertEqual(response.status_code, 200)

            response = self.client.get(preview_url)

            # Check the HTML response
            self.assertEqual(response.status_code, 200)

            frozen_datetime.move_to(expiry_datetime)

            preview_url = reverse(
                "wagtailadmin_pages:preview_on_edit", args=(self.home_page.id,)
            )
            response = self.client.post(preview_url, self.post_data)
            self.assertEqual(response.status_code, 200)
            response = self.client.get(preview_url)
            self.assertEqual(response.status_code, 200)

    def test_preview_on_create_clear_preview_data(self):
        preview_session_key = "wagtail-preview-tests-eventpage-{}".format(
            self.home_page.id
        )

        # Set a fake preview session data for the page
        self.client.session[preview_session_key] = "test data"

        preview_url = reverse(
            "wagtailadmin_pages:preview_on_add",
            args=("tests", "eventpage", self.home_page.id),
        )
        response = self.client.delete(preview_url)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode(),
            {"success": True},
        )

        # The data should no longer exist in the session
        self.assertNotIn(preview_session_key, self.client.session)

        response = self.client.get(preview_url)

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
        preview_session_key = "wagtail-preview-{}".format(self.event_page.id)

        # Set a fake preview session data for the page
        self.client.session[preview_session_key] = "test data"

        preview_url = reverse(
            "wagtailadmin_pages:preview_on_edit", args=(self.event_page.id,)
        )
        response = self.client.delete(preview_url)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode(),
            {"success": True},
        )

        # The data should no longer exist in the session
        self.assertNotIn(preview_session_key, self.client.session)

        response = self.client.get(preview_url)

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

    def test_preview_modes(self):
        preview_url = reverse(
            "wagtailadmin_pages:preview_on_add",
            args=("tests", "multipreviewmodespage", self.home_page.id),
        )

        response = self.client.post(preview_url, data={"title": "Test", "slug": "test"})
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode(),
            {"is_valid": True, "is_available": True},
        )

        cases = [
            ("", "tests/simple_page_alt.html"),
            ("?mode=original", "tests/simple_page.html"),
            ("?mode=alt%231", "tests/simple_page_alt.html"),
        ]

        for params, template in cases:
            with self.subTest(params=params, template=template):
                response = self.client.get(preview_url + params)
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, template)


class TestEnablePreview(TestCase, WagtailTestUtils):
    def setUp(self):
        self.root_page = Page.objects.get(id=2)
        self.user = self.login()

        # SimplePage only has one preview mode
        self.single = SimplePage(title="Single preview mode", content="foo")
        # MultiPreviewModesPage has two preview modes
        self.multiple = MultiPreviewModesPage(title="Multiple preview modes")

        self.root_page.add_child(instance=self.single)
        self.root_page.add_child(instance=self.multiple)

    def get_url_on_add(self, name, page):
        model_name = type(page)._meta.model_name
        return reverse(
            f"wagtailadmin_pages:{name}",
            args=("tests", model_name, self.root_page.id),
        )

    def get_url_on_edit(self, name, page):
        return reverse(f"wagtailadmin_pages:{name}", args=(page.id,))

    def test_show_preview_panel_on_create_with_single_mode(self):
        create_url = self.get_url_on_add("add", self.single)
        preview_url = self.get_url_on_add("preview_on_add", self.single)
        iframe_url = preview_url + "?in_preview_panel=true&mode="
        response = self.client.get(create_url)

        self.assertEqual(response.status_code, 200)

        # Should show the preview panel
        self.assertContains(response, 'data-side-panel-toggle="preview"')
        self.assertContains(response, 'data-side-panel="preview"')
        self.assertContains(response, 'data-action="%s"' % preview_url)

        # Should show the iframe
        self.assertContains(
            response,
            f'<iframe title="Preview" class="preview-panel__iframe" data-preview-iframe src="{iframe_url}" aria-describedby="preview-panel-error-banner">',
        )

        # Should not show the preview mode selection
        self.assertNotContains(
            response,
            '<select id="id_preview_mode" name="preview_mode" class="preview-panel__mode-select" data-preview-mode-select>',
        )

    def test_show_preview_panel_on_create_with_multiple_modes(self):
        create_url = self.get_url_on_add("add", self.multiple)
        preview_url = self.get_url_on_add("preview_on_add", self.multiple)
        iframe_url = preview_url + "?in_preview_panel=true&mode=alt%231"
        response = self.client.get(create_url)

        self.assertEqual(response.status_code, 200)

        # Should show the preview panel
        self.assertContains(response, 'data-side-panel-toggle="preview"')
        self.assertContains(response, 'data-side-panel="preview"')
        self.assertContains(response, 'data-action="%s"' % preview_url)

        # Should show the iframe with the default mode set and correctly quoted
        self.assertContains(
            response,
            f'<iframe title="Preview" class="preview-panel__iframe" data-preview-iframe src="{iframe_url}" aria-describedby="preview-panel-error-banner">',
        )

        # should show the preview mode selection
        self.assertContains(
            response,
            '<select id="id_preview_mode" name="preview_mode" class="preview-panel__mode-select" data-preview-mode-select>',
        )
        self.assertContains(response, '<option value="original">Original</option>')

        # Should respect the default_preview_mode
        self.assertContains(
            response, '<option value="alt#1" selected>Alternate</option>'
        )

    def test_show_preview_panel_on_edit_with_single_mode(self):
        edit_url = self.get_url_on_edit("edit", self.single)
        preview_url = self.get_url_on_edit("preview_on_edit", self.single)
        iframe_url = preview_url + "?in_preview_panel=true&mode="
        response = self.client.get(edit_url)

        self.assertEqual(response.status_code, 200)

        # Should show the preview panel
        self.assertContains(response, 'data-side-panel-toggle="preview"')
        self.assertContains(response, 'data-side-panel="preview"')
        self.assertContains(response, 'data-action="%s"' % preview_url)

        # Should show the iframe
        self.assertContains(
            response,
            f'<iframe title="Preview" class="preview-panel__iframe" data-preview-iframe src="{iframe_url}" aria-describedby="preview-panel-error-banner">',
        )

        # Should not show the preview mode selection
        self.assertNotContains(
            response,
            '<select id="id_preview_mode" name="preview_mode" class="preview-panel__mode-select" data-preview-mode-select>',
        )

    def test_show_preview_panel_on_edit_with_multiple_modes(self):
        edit_url = self.get_url_on_edit("edit", self.multiple)
        preview_url = self.get_url_on_edit("preview_on_edit", self.multiple)
        iframe_url = preview_url + "?in_preview_panel=true&mode=alt%231"
        response = self.client.get(edit_url)

        self.assertEqual(response.status_code, 200)

        # Should show the preview panel
        self.assertContains(response, 'data-side-panel-toggle="preview"')
        self.assertContains(response, 'data-side-panel="preview"')
        self.assertContains(response, 'data-action="%s"' % preview_url)

        # Should show the iframe with the default mode set and correctly quoted
        self.assertContains(
            response,
            f'<iframe title="Preview" class="preview-panel__iframe" data-preview-iframe src="{iframe_url}" aria-describedby="preview-panel-error-banner">',
        )

        # should show the preview mode selection
        self.assertContains(
            response,
            '<select id="id_preview_mode" name="preview_mode" class="preview-panel__mode-select" data-preview-mode-select>',
        )
        self.assertContains(response, '<option value="original">Original</option>')

        # Should respect the default_preview_mode
        self.assertContains(
            response, '<option value="alt#1" selected>Alternate</option>'
        )

    def test_show_preview_on_revisions_list(self):
        latest_revision = self.single.save_revision(log_action=True)
        history_url = self.get_url_on_edit("history", self.single)
        preview_url = reverse(
            "wagtailadmin_pages:revisions_view",
            args=(self.single.id, latest_revision.id),
        )

        response = self.client.get(history_url)
        self.assertContains(response, "Preview")
        self.assertContains(response, preview_url)


class TestDisablePreviewButton(TestCase, WagtailTestUtils):
    """
    Test that preview button can be disabled by setting preview_modes to an empty list
    """

    def setUp(self):
        # Find root page
        self.root_page = Page.objects.get(id=2)

        # Login
        self.user = self.login()

    def test_disable_preview_on_create(self):
        # StreamPage has preview_modes = []
        response = self.client.get(
            reverse(
                "wagtailadmin_pages:add",
                args=("tests", "streampage", self.root_page.id),
            )
        )
        self.assertEqual(response.status_code, 200)

        preview_url = reverse(
            "wagtailadmin_pages:preview_on_add",
            args=("tests", "streampage", self.root_page.id),
        )
        self.assertNotContains(response, 'data-side-panel-toggle="preview"')
        self.assertNotContains(response, 'data-side-panel="preview"')
        self.assertNotContains(response, 'data-action="%s"' % preview_url)

    def test_disable_preview_on_edit(self):
        stream_page = StreamPage(title="stream page", body=[("text", "hello")])
        self.root_page.add_child(instance=stream_page)

        # StreamPage has preview_modes = []
        response = self.client.get(
            reverse("wagtailadmin_pages:edit", args=(stream_page.id,))
        )
        self.assertEqual(response.status_code, 200)

        preview_url = reverse(
            "wagtailadmin_pages:preview_on_edit", args=(stream_page.id,)
        )
        self.assertNotContains(response, 'data-side-panel-toggle="preview"')
        self.assertNotContains(response, 'data-side-panel="preview"')
        self.assertNotContains(response, 'data-action="%s"' % preview_url)

    def test_disable_preview_on_revisions_list(self):
        stream_page = StreamPage(title="stream page", body=[("text", "hello")])
        self.root_page.add_child(instance=stream_page)
        latest_revision = stream_page.save_revision(log_action=True)

        # StreamPage has preview_modes = []
        response = self.client.get(
            reverse("wagtailadmin_pages:history", args=(stream_page.id,))
        )
        preview_url = reverse(
            "wagtailadmin_pages:revisions_view",
            args=(stream_page.id, latest_revision.id),
        )
        self.assertNotContains(response, "Preview")
        self.assertNotContains(response, preview_url)

    def disable_preview_in_moderation_list(self):
        stream_page = StreamPage(title="stream page", body=[("text", "hello")])
        self.root_page.add_child(instance=stream_page)
        latest_revision = stream_page.save_revision(
            user=self.user, submitted_for_moderation=True
        )

        response = self.client.get(reverse("wagtailadmin_home"))
        preview_url = reverse(
            "wagtailadmin_pages:preview_for_moderation", args=(latest_revision.id,)
        )
        self.assertNotContains(response, '<li class="preview">')
        self.assertNotContains(response, 'data-action="%s"' % preview_url)
