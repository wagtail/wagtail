import datetime
from functools import wraps

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time

from wagtail.admin.staticfiles import versioned_static
from wagtail.admin.views.pages.preview import PreviewOnEdit
from wagtail.models import Page, Site
from wagtail.test.testapp.models import (
    CustomPreviewSizesPage,
    EventCategory,
    MultiPreviewModesPage,
    SimplePage,
    StreamPage,
)
from wagtail.test.utils import WagtailTestUtils


class TestIssue2599(WagtailTestUtils, TestCase):
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


class TestPreview(WagtailTestUtils, TestCase):
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
        self.assertNotContains(response, versioned_static("wagtailadmin/js/icons.js"))

    def test_preview_on_create_with_invalid_data(self):
        preview_url = reverse(
            "wagtailadmin_pages:preview_on_add",
            args=("tests", "eventpage", self.home_page.id),
        )

        preview_session_key = "wagtail-preview-tests-eventpage-{}".format(
            self.home_page.id
        )
        self.assertNotIn(preview_session_key, self.client.session)

        response = self.client.post(
            preview_url,
            {**self.post_data, "date_from": "2025-02-31"},
        )

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
        self.assertNotContains(response, versioned_static("wagtailadmin/js/icons.js"))

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

    def test_preview_on_create_with_incorrect_site_hostname(self):
        # Failing to set a valid hostname in the Site record (as determined by ALLOWED_HOSTS)
        # should not prevent the preview from being generated.
        Site.objects.filter(is_default_site=True).update(hostname="bad.example.com")

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

    def test_preview_on_create_with_deferred_required_fields(self):
        preview_url = reverse(
            "wagtailadmin_pages:preview_on_add",
            args=("tests", "eventpage", self.home_page.id),
        )

        preview_session_key = "wagtail-preview-tests-eventpage-{}".format(
            self.home_page.id
        )
        self.assertNotIn(preview_session_key, self.client.session)

        response = self.client.post(
            preview_url,
            {
                "title": "Bare minimum",
                "slug": "bare-minimum",
                "carousel_items-TOTAL_FORMS": 0,
                "carousel_items-INITIAL_FORMS": 0,
                "speakers-TOTAL_FORMS": 0,
                "speakers-INITIAL_FORMS": 0,
                "related_links-TOTAL_FORMS": 0,
                "related_links-INITIAL_FORMS": 0,
                "head_counts-TOTAL_FORMS": 0,
                "head_counts-INITIAL_FORMS": 0,
            },
        )

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
        self.assertContains(response, "Bare minimum")

    def test_preview_on_create_without_title_and_slug(self):
        preview_url = reverse(
            "wagtailadmin_pages:preview_on_add",
            args=("tests", "eventpage", self.home_page.id),
        )

        preview_session_key = "wagtail-preview-tests-eventpage-{}".format(
            self.home_page.id
        )
        self.assertNotIn(preview_session_key, self.client.session)

        response = self.client.post(
            preview_url,
            {
                "carousel_items-TOTAL_FORMS": 0,
                "carousel_items-INITIAL_FORMS": 0,
                "speakers-TOTAL_FORMS": 0,
                "speakers-INITIAL_FORMS": 0,
                "related_links-TOTAL_FORMS": 0,
                "related_links-INITIAL_FORMS": 0,
                "head_counts-TOTAL_FORMS": 0,
                "head_counts-INITIAL_FORMS": 0,
            },
        )

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
        self.assertContains(response, "Placeholder title")

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
        preview_session_key = f"wagtail-preview-{self.event_page.id}"
        self.assertIn(preview_session_key, self.client.session)

        response = self.client.get(preview_url)

        # Check the HTML response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tests/event_page.html")
        self.assertContains(response, "Beach party")
        self.assertContains(response, "<li>Parties</li>")
        self.assertContains(response, "<li>Holidays</li>")

    def test_preview_on_edit_with_incorrect_site_hostname(self):
        # Failing to set a valid hostname in the Site record (as determined by ALLOWED_HOSTS)
        # should not prevent the preview from being generated.
        Site.objects.filter(is_default_site=True).update(hostname="bad.example.com")

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
        preview_session_key = f"wagtail-preview-{self.event_page.id}"
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
        response = self.client.post(
            preview_url,
            {**self.post_data, "date_to": "1234-56-78"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode(),
            {"is_valid": False, "is_available": True},
        )

        # Check the user can still see the preview with the last valid data
        preview_session_key = f"wagtail-preview-{self.event_page.id}"
        self.assertIn(preview_session_key, self.client.session)

        response = self.client.get(preview_url)

        # Check the HTML response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tests/event_page.html")
        self.assertContains(response, "Beach party")
        self.assertContains(response, "<li>Parties</li>")
        self.assertContains(response, "<li>Holidays</li>")

    def test_preview_on_edit_with_deferred_required_fields(self):
        preview_url = reverse(
            "wagtailadmin_pages:preview_on_edit", args=(self.event_page.id,)
        )

        response = self.client.post(
            preview_url,
            {
                "title": "Bare minimum",
                "slug": "bare-minimum",
                "carousel_items-TOTAL_FORMS": 0,
                "carousel_items-INITIAL_FORMS": 0,
                "speakers-TOTAL_FORMS": 0,
                "speakers-INITIAL_FORMS": 0,
                "related_links-TOTAL_FORMS": 0,
                "related_links-INITIAL_FORMS": 0,
                "head_counts-TOTAL_FORMS": 0,
                "head_counts-INITIAL_FORMS": 0,
            },
        )

        # Check the JSON response
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode(),
            {"is_valid": True, "is_available": True},
        )

        # Check the user can refresh the preview
        preview_session_key = f"wagtail-preview-{self.event_page.id}"
        self.assertIn(preview_session_key, self.client.session)

        response = self.client.get(preview_url)

        # Check the HTML response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tests/event_page.html")
        self.assertContains(response, "Bare minimum")

    def test_preview_on_edit_without_title_and_slug(self):
        preview_url = reverse(
            "wagtailadmin_pages:preview_on_edit", args=(self.event_page.id,)
        )

        response = self.client.post(
            preview_url,
            {
                "carousel_items-TOTAL_FORMS": 0,
                "carousel_items-INITIAL_FORMS": 0,
                "speakers-TOTAL_FORMS": 0,
                "speakers-INITIAL_FORMS": 0,
                "related_links-TOTAL_FORMS": 0,
                "related_links-INITIAL_FORMS": 0,
                "head_counts-TOTAL_FORMS": 0,
                "head_counts-INITIAL_FORMS": 0,
            },
        )

        # Check the JSON response
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode(),
            {"is_valid": True, "is_available": True},
        )

        # Check the user can refresh the preview
        preview_session_key = f"wagtail-preview-{self.event_page.id}"
        self.assertIn(preview_session_key, self.client.session)

        response = self.client.get(preview_url)

        # Check the HTML response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tests/event_page.html")
        self.assertContains(response, "Placeholder title")

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
        self.assertNotContains(response, versioned_static("wagtailadmin/js/icons.js"))

    def test_preview_on_edit_clear_preview_data(self):
        preview_session_key = f"wagtail-preview-{self.event_page.id}"

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
        self.assertNotContains(response, versioned_static("wagtailadmin/js/icons.js"))

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

    def test_preview_sizes(self):
        page = CustomPreviewSizesPage(title="Custom preview size")
        self.home_page.add_child(instance=page)
        edit_url = reverse("wagtailadmin_pages:edit", args=(page.id,))

        response = self.client.get(edit_url)
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


class TestEnablePreview(WagtailTestUtils, TestCase):
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
        create_url = self.get_url_on_add("add", self.multiple)
        preview_url = self.get_url_on_add("preview_on_add", self.multiple)
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
        other_option = mode_select.select_one('option[value="original"]')
        self.assertIsNotNone(other_option)
        self.assertIsNone(other_option.get("selected"))

    def test_show_preview_panel_on_edit_with_single_mode(self):
        edit_url = self.get_url_on_edit("edit", self.single)
        preview_url = self.get_url_on_edit("preview_on_edit", self.single)
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

        # Should show the new tab button with the default mode set
        new_tab_button = controller.select_one('a[data-w-preview-target="newTab"]')
        self.assertIsNotNone(new_tab_button)
        self.assertEqual(new_tab_button["href"], new_tab_url)
        self.assertEqual(new_tab_button["target"], "_blank")

        # Should not show the preview mode selection
        mode_select = controller.select_one('[data-w-preview-target="mode"]')
        self.assertIsNone(mode_select)

    def test_show_preview_panel_on_edit_with_multiple_modes(self):
        edit_url = self.get_url_on_edit("edit", self.multiple)
        preview_url = self.get_url_on_edit("preview_on_edit", self.multiple)
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
        other_option = mode_select.select_one('option[value="original"]')
        self.assertIsNotNone(other_option)
        self.assertIsNone(other_option.get("selected"))

    @override_settings(WAGTAIL_AUTO_UPDATE_PREVIEW_INTERVAL=12345)
    def test_custom_auto_update_interval(self):
        edit_url = self.get_url_on_edit("edit", self.single)
        preview_url = self.get_url_on_edit("preview_on_edit", self.single)
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
        edit_url = self.get_url_on_edit("edit", self.single)
        preview_url = self.get_url_on_edit("preview_on_edit", self.single)
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
        latest_revision = self.single.save_revision(log_action=True)
        history_url = self.get_url_on_edit("history", self.single)
        preview_url = reverse(
            "wagtailadmin_pages:revisions_view",
            args=(self.single.id, latest_revision.id),
        )

        response = self.client.get(history_url)
        soup = self.get_soup(response.content)

        preview_link = soup.find("a", {"href": preview_url})
        self.assertEqual(len(preview_link), 1)
        self.assertEqual("Preview", preview_link.text)


class TestDisablePreviewButton(WagtailTestUtils, TestCase):
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
        self.assertNotContains(response, 'data-controller="w-preview"')
        self.assertNotContains(response, preview_url)

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
        self.assertNotContains(response, 'data-controller="w-preview"')
        self.assertNotContains(response, preview_url)

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

        self.assertNotContains(response, preview_url)

        soup = self.get_soup(response.content)

        preview_link = soup.find("a", {"href": preview_url})
        self.assertIsNone(preview_link)
