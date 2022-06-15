from django.test import TestCase
from django.urls import reverse
from django.utils.http import urlencode

from wagtail import hooks
from wagtail.admin import widgets as wagtailadmin_widgets
from wagtail.admin.wagtail_hooks import page_listing_more_buttons
from wagtail.models import Page
from wagtail.test.utils import WagtailTestUtils


class BasePagePerms:
    def can_move(self):
        return False

    def can_copy(self):
        return False

    def can_delete(self):
        return False

    def can_unpublish(self):
        return False

    def can_view_revisions(self):
        return False

    def can_reorder_children(self):
        return False


class DeleteOnlyPagePerms(BasePagePerms):
    def can_delete(self):
        return True


class ReorderOnlyPagePerms(BasePagePerms):
    def can_reorder_children(self):
        return True


class TestButtonsHooks(TestCase, WagtailTestUtils):
    def setUp(self):
        self.root_page = Page.objects.get(id=2)
        self.login()

    def test_register_page_listing_buttons(self):
        def page_listing_buttons(page, page_perms, is_parent=False, next_url=None):
            yield wagtailadmin_widgets.PageListingButton(
                "Another useless page listing button", "/custom-url", priority=10
            )

        with hooks.register_temporarily(
            "register_page_listing_buttons", page_listing_buttons
        ):
            response = self.client.get(
                reverse("wagtailadmin_explore", args=(self.root_page.id,))
            )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "wagtailadmin/pages/listing/_button_with_dropdown.html"
        )
        self.assertTemplateUsed(response, "wagtailadmin/pages/listing/_buttons.html")

        self.assertContains(response, "Another useless page listing button")

    def test_register_page_listing_more_buttons(self):
        def page_listing_more_buttons(page, page_perms, is_parent=False, next_url=None):
            yield wagtailadmin_widgets.Button(
                'Another useless button in default "More" dropdown',
                "/custom-url",
                priority=10,
            )

        with hooks.register_temporarily(
            "register_page_listing_more_buttons", page_listing_more_buttons
        ):
            response = self.client.get(
                reverse("wagtailadmin_explore", args=(self.root_page.id,))
            )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "wagtailadmin/pages/listing/_button_with_dropdown.html"
        )
        self.assertTemplateUsed(response, "wagtailadmin/pages/listing/_buttons.html")

        self.assertContains(
            response, "Another useless button in default &quot;More&quot; dropdown"
        )

    def test_custom_button_with_dropdown(self):
        def page_custom_listing_buttons(
            page, page_perms, is_parent=False, next_url=None
        ):
            yield wagtailadmin_widgets.ButtonWithDropdownFromHook(
                "One more more button",
                hook_name="register_page_listing_one_more_more_buttons",
                page=page,
                page_perms=page_perms,
                is_parent=is_parent,
                next_url=next_url,
                attrs={"target": "_blank", "rel": "noreferrer"},
                priority=50,
            )

        def page_custom_listing_more_buttons(
            page, page_perms, is_parent=False, next_url=None
        ):
            yield wagtailadmin_widgets.Button(
                'Another useless dropdown button in "One more more button" dropdown',
                "/custom-url",
                priority=10,
            )

        with hooks.register_temporarily(
            "register_page_listing_buttons", page_custom_listing_buttons
        ), hooks.register_temporarily(
            "register_page_listing_one_more_more_buttons",
            page_custom_listing_more_buttons,
        ):
            response = self.client.get(
                reverse("wagtailadmin_explore", args=(self.root_page.id,))
            )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "wagtailadmin/pages/listing/_button_with_dropdown.html"
        )
        self.assertTemplateUsed(response, "wagtailadmin/pages/listing/_buttons.html")

        self.assertContains(response, "One more more button")
        self.assertContains(
            response,
            "Another useless dropdown button in &quot;One more more button&quot; dropdown",
        )

    def test_register_page_header_buttons(self):
        def page_header_buttons(page, page_perms, next_url=None):
            yield wagtailadmin_widgets.Button(
                "Another useless header button", "/custom-url", priority=10
            )

        with hooks.register_temporarily(
            "register_page_header_buttons", page_header_buttons
        ):
            response = self.client.get(
                reverse("wagtailadmin_pages:edit", args=(self.root_page.id,))
            )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "wagtailadmin/pages/listing/_modern_dropdown.html"
        )

        self.assertContains(response, "Another useless header button")

    def test_delete_button_next_url(self):
        page_perms = DeleteOnlyPagePerms()
        page = self.root_page
        base_url = reverse("wagtailadmin_pages:delete", args=[page.id])

        next_url = "a/random/url/"
        full_url = base_url + "?" + urlencode({"next": next_url})

        # page_listing_more_button generator yields only `Delete button`
        delete_button = next(
            page_listing_more_buttons(
                page, page_perms, is_parent=False, next_url=next_url
            )
        )

        self.assertEqual(delete_button.url, full_url)

        next_url = reverse("wagtailadmin_explore", args=[page.id])
        delete_button = next(
            page_listing_more_buttons(
                page, page_perms, is_parent=False, next_url=next_url
            )
        )

        self.assertEqual(delete_button.url, base_url)

    def test_reorder_button_visibility(self):
        page = self.root_page
        page_perms = BasePagePerms()

        # no button returned
        buttons = page_listing_more_buttons(page, page_perms, is_parent=True)
        self.assertEqual(len(list(buttons)), 0)

        page_perms = ReorderOnlyPagePerms()
        # page_listing_more_button generator yields only `Sort menu order button`
        reorder_button = next(
            page_listing_more_buttons(page, page_perms, is_parent=True)
        )

        self.assertEqual(reorder_button.url, "?ordering=ord")
