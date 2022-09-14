from django.test import TestCase
from django.urls import reverse
from django.utils.http import urlencode

from wagtail import hooks
from wagtail.admin import widgets as wagtailadmin_widgets
from wagtail.admin.wagtail_hooks import page_header_buttons, page_listing_more_buttons
from wagtail.models import Page
from wagtail.test.testapp.models import SimplePage
from wagtail.test.utils import WagtailTestUtils


class BasePagePerms:
    def can_move(self):
        return False

    def can_copy(self):
        return False

    def can_edit(self):
        return False

    def can_delete(self):
        return False

    def can_unpublish(self):
        return False

    def can_view_revisions(self):
        return False

    def can_reorder_children(self):
        return False

    def can_add_subpage(self):
        return False


class DeleteOnlyPagePerms(BasePagePerms):
    def can_delete(self):
        return True


class DeleteAndUnpublishPagePerms(BasePagePerms):
    def can_delete(self):
        return True

    def can_unpublish(self):
        return True


class ReorderOnlyPagePerms(BasePagePerms):
    def can_reorder_children(self):
        return True


class TestButtonsHooks(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

        self.root_page = Page.objects.get(id=2)
        self.child_page = self.root_page.add_child(
            instance=SimplePage(
                title="Public page",
                content="hello",
                live=True,
            )
        )


class TestPageListingButtonsHooks(TestButtonsHooks):
    def test_register_page_listing_buttons(self):
        def page_listing_buttons(page, page_perms, next_url=None):
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


class TestPageListingMoreButtonsHooks(TestButtonsHooks):
    def test_register_page_listing_more_buttons(self):
        def page_listing_more_buttons(page, page_perms, next_url=None):
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
        def page_custom_listing_buttons(page, page_perms, next_url=None):
            yield wagtailadmin_widgets.ButtonWithDropdownFromHook(
                "One more more button",
                hook_name="register_page_listing_one_more_more_buttons",
                page=page,
                page_perms=page_perms,
                next_url=next_url,
                attrs={"target": "_blank", "rel": "noreferrer"},
                priority=50,
            )

        def page_custom_listing_more_buttons(page, page_perms, next_url=None):
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

    def test_delete_button_with_next_url(self):
        """
        Ensure that the built in delete button supports a next_url provided.
        """

        # page_listing_more_button generator yields only `Delete button` with this permission set
        page_perms = DeleteOnlyPagePerms()
        page = self.root_page
        base_url = reverse("wagtailadmin_pages:delete", args=[page.id])

        next_url = "a/random/url/"
        full_url = base_url + "?" + urlencode({"next": next_url})

        delete_button = next(
            page_listing_more_buttons(page, page_perms, next_url=next_url)
        )

        self.assertEqual(delete_button.url, full_url)

    def test_delete_button_with_invalid_next_url(self):
        """
        Ensure that the built in delete button on page listing will not use
        the next_url provided if that URL is directing the user to edit the page.
        As the page is now deleted and cannot be edited.
        """

        # permissions should yield two buttons, delete and unpublish
        page_perms = DeleteAndUnpublishPagePerms()
        page = self.root_page

        base_url = reverse("wagtailadmin_pages:delete", args=[page.id])
        next_url = reverse("wagtailadmin_explore", args=[page.id])

        buttons = page_listing_more_buttons(page, page_perms, next_url=next_url)

        delete_button = next(buttons)

        # check that the next_url is NOT included as it will not be available after deletion
        self.assertEqual(delete_button.url, base_url)

        # check that any buttons after do correctly still include the next_url
        unpublish_base_url = reverse("wagtailadmin_pages:unpublish", args=[page.id])
        unpublish_button = next(buttons)
        full_url = unpublish_base_url + "?" + urlencode({"next": next_url})
        self.assertEqual(unpublish_button.url, full_url)

    def test_reorder_button_visibility(self):
        page = self.root_page
        page_perms = BasePagePerms()

        # no button returned
        buttons = page_listing_more_buttons(page, page_perms)
        self.assertEqual(len(list(buttons)), 0)

        page_perms = ReorderOnlyPagePerms()
        # page_listing_more_button generator yields only `Sort menu order button`
        reorder_button = next(page_listing_more_buttons(page, page_perms))

        self.assertEqual(reorder_button.url, "?ordering=ord")


class TestPageHeaderButtonsHooks(TestButtonsHooks):
    def test_register_page_header_buttons(self):
        def custom_page_header_buttons(page, page_perms, next_url=None):
            yield wagtailadmin_widgets.Button(
                "Another useless header button", "/custom-url", priority=10
            )

        with hooks.register_temporarily(
            "register_page_header_buttons", custom_page_header_buttons
        ):
            response = self.client.get(
                reverse("wagtailadmin_pages:edit", args=(self.root_page.id,))
            )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "wagtailadmin/pages/listing/_modern_dropdown.html"
        )

        self.assertContains(response, "Another useless header button")

    def test_delete_button_with_next_url(self):
        """
        Ensure that the built in delete button supports a next_url provided.
        """

        # page_listing_more_button generator yields only `Delete button` with this permission set
        page_perms = DeleteOnlyPagePerms()
        page = self.root_page
        base_url = reverse("wagtailadmin_pages:delete", args=[page.id])

        next_url = "a/random/url/"
        full_url = base_url + "?" + urlencode({"next": next_url})

        delete_button = next(page_header_buttons(page, page_perms, next_url=next_url))

        self.assertEqual(delete_button.url, full_url)

    def test_delete_button_with_invalid_next_url(self):
        """
        Ensure that the built in delete button on page edit/home (header button) will not use
        the next_url provided if that URL is directing the user to edit the page.
        As the page is now deleted and cannot be edited.
        """

        # permissions should yield two buttons, delete and unpublish
        page_perms = DeleteAndUnpublishPagePerms()
        page = self.root_page

        base_url = reverse("wagtailadmin_pages:delete", args=[page.id])
        next_url = reverse("wagtailadmin_explore", args=[page.id])

        buttons = page_header_buttons(page, page_perms, next_url=next_url)

        delete_button = next(buttons)

        # check that the next_url is NOT included as it will not be available after deletion (page listing)
        self.assertEqual(delete_button.url, base_url)

        base_url = reverse("wagtailadmin_pages:delete", args=[page.id])
        next_url = reverse("wagtailadmin_pages:edit", args=[page.id])

        buttons = page_header_buttons(page, page_perms, next_url=next_url)

        delete_button = next(buttons)

        # check that the next_url is NOT included as it will not be available after deletion (edit page)
        self.assertEqual(delete_button.url, base_url)

        # check that any buttons after do correctly still include the next_url
        unpublish_base_url = reverse("wagtailadmin_pages:unpublish", args=[page.id])
        unpublish_button = next(buttons)
        full_url = unpublish_base_url + "?" + urlencode({"next": next_url})
        self.assertEqual(unpublish_button.url, full_url)
