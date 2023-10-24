from django.contrib.auth.models import AbstractBaseUser, Group
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from django.utils.http import urlencode

from wagtail import hooks
from wagtail.admin import widgets as wagtailadmin_widgets
from wagtail.admin.wagtail_hooks import page_header_buttons, page_listing_more_buttons
from wagtail.admin.widgets.button import Button
from wagtail.models import Page
from wagtail.test.testapp.models import SimplePage
from wagtail.test.utils import WagtailTestUtils
from wagtail.utils.deprecation import RemovedInWagtail60Warning


class TestButtonsHooks(WagtailTestUtils, TestCase):
    def setUp(self):
        self.user = self.login()

        self.root_page = Page.objects.get(id=2)
        self.child_page = self.root_page.add_child(
            instance=SimplePage(
                title="Public page",
                content="hello",
                live=True,
            )
        )


class TestPageListingButtonsHooks(TestButtonsHooks):
    def test_register_page_listing_buttons_old_signature(self):
        def page_listing_buttons_old_signature(page, page_perms, next_url=None):
            yield wagtailadmin_widgets.PageListingButton(
                "Another useless page listing button", "/custom-url", priority=10
            )

        with hooks.register_temporarily(
            "register_page_listing_buttons", page_listing_buttons_old_signature
        ):
            with self.assertWarnsMessage(
                RemovedInWagtail60Warning,
                "`register_page_listing_buttons` hook functions should accept a `user` argument instead of `page_perms`",
            ):
                response = self.client.get(
                    reverse("wagtailadmin_explore", args=(self.root_page.id,))
                )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "wagtailadmin/pages/listing/_button_with_dropdown.html"
        )
        self.assertTemplateUsed(response, "wagtailadmin/shared/buttons.html")

        self.assertContains(response, "Another useless page listing button")

    def test_register_page_listing_buttons_new_signature(self):
        def page_listing_buttons_new_signature(page, user, next_url=None):
            if not isinstance(user, AbstractBaseUser):
                raise TypeError("expected a user instance")

            yield wagtailadmin_widgets.PageListingButton(
                "Another useless page listing button", "/custom-url", priority=10
            )

        with hooks.register_temporarily(
            "register_page_listing_buttons", page_listing_buttons_new_signature
        ):
            response = self.client.get(
                reverse("wagtailadmin_explore", args=(self.root_page.id,))
            )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "wagtailadmin/pages/listing/_button_with_dropdown.html"
        )
        self.assertTemplateUsed(response, "wagtailadmin/shared/buttons.html")

        self.assertContains(response, "Another useless page listing button")


class TestPageListingMoreButtonsHooks(TestButtonsHooks):
    def test_register_page_listing_more_buttons_with_old_signature(self):
        def page_listing_more_buttons(page, page_perms, next_url=None):
            yield wagtailadmin_widgets.Button(
                'Another useless button in default "More" dropdown',
                "/custom-url",
                priority=10,
            )

        with hooks.register_temporarily(
            "register_page_listing_more_buttons", page_listing_more_buttons
        ), self.assertWarnsMessage(
            RemovedInWagtail60Warning,
            "`register_page_listing_more_buttons` hook functions should accept a `user` argument instead of `page_perms`",
        ):
            response = self.client.get(
                reverse("wagtailadmin_explore", args=(self.root_page.id,))
            )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "wagtailadmin/pages/listing/_button_with_dropdown.html"
        )
        self.assertTemplateUsed(response, "wagtailadmin/shared/buttons.html")

        self.assertContains(
            response, "Another useless button in default &quot;More&quot; dropdown"
        )

    def test_register_page_listing_more_buttons_with_new_signature(self):
        def page_listing_more_buttons(page, user, next_url=None):
            if not isinstance(user, AbstractBaseUser):
                raise TypeError("expected a user instance")

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
        self.assertTemplateUsed(response, "wagtailadmin/shared/buttons.html")

        self.assertContains(
            response, "Another useless button in default &quot;More&quot; dropdown"
        )

    def test_button_with_dropdown_from_hook_accepts_page_perms_argument(self):
        page = self.root_page

        with self.assertWarnsMessage(
            RemovedInWagtail60Warning,
            "ButtonWithDropdownFromHook should be passed a `user` argument instead of `page_perms`",
        ):
            button = wagtailadmin_widgets.ButtonWithDropdownFromHook(
                "One more more button",
                hook_name="register_page_listing_one_more_more_buttons",
                page=page,
                page_perms=page.permissions_for_user(self.user),
                next_url="/custom-url",
                attrs={"target": "_blank", "rel": "noreferrer"},
                priority=50,
            )

        self.assertEqual(button.user, self.user)

    def test_custom_button_with_dropdown_with_old_signature(self):
        def page_custom_listing_buttons(page, user, next_url=None):
            yield wagtailadmin_widgets.ButtonWithDropdownFromHook(
                "One more more button",
                hook_name="register_page_listing_one_more_more_buttons",
                page=page,
                user=user,
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
        ), self.assertWarnsMessage(
            RemovedInWagtail60Warning,
            "`register_page_listing_one_more_more_buttons` hook functions should accept a `user` argument instead of `page_perms`",
        ):
            response = self.client.get(
                reverse("wagtailadmin_explore", args=(self.root_page.id,))
            )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "wagtailadmin/pages/listing/_button_with_dropdown.html"
        )
        self.assertTemplateUsed(response, "wagtailadmin/shared/buttons.html")

        self.assertContains(response, "One more more button")
        self.assertContains(
            response,
            "Another useless dropdown button in &quot;One more more button&quot; dropdown",
        )

    def test_custom_button_with_dropdown_with_new_signature(self):
        def page_custom_listing_buttons(page, user, next_url=None):
            yield wagtailadmin_widgets.ButtonWithDropdownFromHook(
                "One more more button",
                hook_name="register_page_listing_one_more_more_buttons",
                page=page,
                user=user,
                next_url=next_url,
                attrs={"target": "_blank", "rel": "noreferrer"},
                priority=50,
            )

        def page_custom_listing_more_buttons(page, user, next_url=None):
            if not isinstance(user, AbstractBaseUser):
                raise TypeError("expected a user instance")

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
        self.assertTemplateUsed(response, "wagtailadmin/shared/buttons.html")

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
        page = self.root_page
        base_url = reverse("wagtailadmin_pages:delete", args=[page.id])

        next_url = "a/random/url/"
        full_url = base_url + "?" + urlencode({"next": next_url})

        buttons = page_listing_more_buttons(page, user=self.user, next_url=next_url)
        delete_button = next(button for button in buttons if button.label == "Delete")

        self.assertEqual(delete_button.url, full_url)

    def test_delete_button_with_invalid_next_url(self):
        """
        Ensure that the built in delete button on page listing will not use
        the next_url provided if that URL is directing the user to edit the page.
        As the page is now deleted and cannot be edited.
        """

        page = self.root_page

        base_url = reverse("wagtailadmin_pages:delete", args=[page.id])
        next_url = reverse("wagtailadmin_explore", args=[page.id])

        buttons = page_listing_more_buttons(page, user=self.user, next_url=next_url)

        delete_button = next(button for button in buttons if button.label == "Delete")

        # check that the next_url is NOT included as it will not be available after deletion
        self.assertEqual(delete_button.url, base_url)

        # check that the unpublish button does correctly still include the next_url
        unpublish_base_url = reverse("wagtailadmin_pages:unpublish", args=[page.id])
        unpublish_button = next(
            button for button in buttons if button.label == "Unpublish"
        )
        full_url = unpublish_base_url + "?" + urlencode({"next": next_url})
        self.assertEqual(unpublish_button.url, full_url)

    def test_reorder_button_visibility(self):
        page = self.root_page

        # Test with a user with no publish permission (and thus no ability to reorder)
        editor = self.create_user(username="editor", password="password")
        editor.groups.add(Group.objects.get(name="Editors"))

        # no button returned
        buttons = [
            button
            for button in page_listing_more_buttons(page, user=editor)
            if button.show
        ]
        self.assertEqual(
            len([button for button in buttons if button.label == "Sort menu order"]), 0
        )

        # Test with a user with publish permission
        publisher = self.create_user(username="publisher", password="password")
        publisher.groups.add(Group.objects.get(name="Moderators"))

        # page_listing_more_button generator yields `Sort menu order button`
        buttons = [
            button
            for button in page_listing_more_buttons(page, user=publisher)
            if button.show
        ]
        reorder_button = next(
            button for button in buttons if button.label == "Sort menu order"
        )

        self.assertEqual(reorder_button.url, "/admin/pages/%d/?ordering=ord" % page.id)


class TestPageHeaderButtonsHooks(TestButtonsHooks):
    def test_register_page_header_buttons_old_signature(self):
        def custom_page_header_buttons(page, page_perms, next_url=None):
            yield wagtailadmin_widgets.Button(
                "Another useless header button", "/custom-url", priority=10
            )

        with hooks.register_temporarily(
            "register_page_header_buttons", custom_page_header_buttons
        ), self.assertWarnsMessage(
            RemovedInWagtail60Warning,
            "`register_page_header_buttons` hook functions should accept a `user` argument instead of `page_perms`",
        ):
            response = self.client.get(
                reverse("wagtailadmin_pages:edit", args=(self.root_page.id,))
            )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "wagtailadmin/pages/listing/_page_header_buttons.html"
        )

        self.assertContains(response, "Another useless header button")

    def test_register_page_header_buttons_new_signature(self):
        def custom_page_header_buttons(page, user, view_name, next_url=None):
            if not isinstance(user, AbstractBaseUser):
                raise TypeError("expected a user instance")

            if view_name != "edit":
                raise ValueError("expected view_name to be 'edit'")

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
            response, "wagtailadmin/pages/listing/_page_header_buttons.html"
        )

        self.assertContains(response, "Another useless header button")

    def test_delete_button_with_next_url(self):
        """
        Ensure that the built in delete button supports a next_url provided.
        """

        page = self.root_page
        base_url = reverse("wagtailadmin_pages:delete", args=[page.id])

        next_url = "a/random/url/"
        full_url = base_url + "?" + urlencode({"next": next_url})

        buttons = page_header_buttons(
            page, self.user, view_name="index", next_url=next_url
        )
        delete_button = next(button for button in buttons if button.label == "Delete")

        self.assertEqual(delete_button.url, full_url)

    def test_delete_button_with_invalid_next_url(self):
        """
        Ensure that the built in delete button on page edit/home (header button) will not use
        the next_url provided if that URL is directing the user to edit the page.
        As the page is now deleted and cannot be edited.
        """

        page = self.root_page

        base_url = reverse("wagtailadmin_pages:delete", args=[page.id])
        next_url = reverse("wagtailadmin_explore", args=[page.id])

        buttons = page_header_buttons(
            page, self.user, view_name="index", next_url=next_url
        )

        delete_button = next(button for button in buttons if button.label == "Delete")

        # check that the next_url is NOT included as it will not be available after deletion (page listing)
        self.assertEqual(delete_button.url, base_url)

        base_url = reverse("wagtailadmin_pages:delete", args=[page.id])
        next_url = reverse("wagtailadmin_pages:edit", args=[page.id])

        buttons = page_header_buttons(
            page, self.user, view_name="index", next_url=next_url
        )

        delete_button = next(button for button in buttons if button.label == "Delete")

        # check that the next_url is NOT included as it will not be available after deletion (edit page)
        self.assertEqual(delete_button.url, base_url)

        # check that any buttons after do correctly still include the next_url
        unpublish_base_url = reverse("wagtailadmin_pages:unpublish", args=[page.id])
        unpublish_button = next(
            button for button in buttons if button.label == "Unpublish"
        )
        full_url = unpublish_base_url + "?" + urlencode({"next": next_url})
        self.assertEqual(unpublish_button.url, full_url)


class ButtonComparisonTestCase(SimpleTestCase):
    """Tests the comparison functions."""

    def setUp(self):
        self.button1 = Button(
            "Label 1", "/url1", classname="class1 class2", priority=100
        )
        self.button2 = Button(
            "Label 2", "/url2", classname="class2 class3", priority=200
        )
        self.button3 = Button(
            "Label 1", "/url3", classname="class1 class2", priority=300
        )
        self.button4 = Button(
            "Label 1", "/url1", classname="class1 class2", priority=100
        )

    def test_eq(self):
        # Same properties, should be equal
        self.assertTrue(self.button1 == self.button4)

        # Different priority, should not be equal
        self.assertFalse(self.button1 == self.button2)

        # Different URL, should not be equal
        self.assertFalse(self.button1 == self.button3)

        # Not a Button, should not be equal
        self.assertFalse(self.button1 == "Something")

    def test_lt(self):
        # Less priority, should be True
        self.assertTrue(self.button1 < self.button2)

        # Same label, but less priority, should be True
        self.assertTrue(self.button1 < self.button3)

        # Greater priority, should be False
        self.assertFalse(self.button2 < self.button1)

        # Not a Button, should raise TypeError
        with self.assertRaises(TypeError):
            self.button1 < "Something"

    def test_le(self):
        # Less priority, should be True
        self.assertTrue(self.button1 <= self.button2)

        # Same label, but less priority, should be True
        self.assertTrue(self.button1 <= self.button3)

        # Same object, should be True
        self.assertTrue(self.button1 <= self.button1)

        # Same label and priority, should be True
        self.assertTrue(self.button1 <= self.button4)

        # Greater priority, should be False
        self.assertFalse(self.button2 <= self.button1)

        # Not a Button, should raise TypeError
        with self.assertRaises(TypeError):
            self.button1 <= "Something"

    def test_gt(self):
        # Greater priority, should be True
        self.assertTrue(self.button2 > self.button1)

        # Same label, but greater priority, should be True
        self.assertTrue(self.button3 > self.button1)

        # Less priority, should be False
        self.assertFalse(self.button1 > self.button2)

        # Not a Button, should raise TypeError
        with self.assertRaises(TypeError):
            self.button1 > "Something"

    def test_ge(self):
        # Greater priority, should be True
        self.assertTrue(self.button2 >= self.button1)

        # Same label, but greater priority, should be True
        self.assertTrue(self.button3 >= self.button1)

        # Same object, should be True
        self.assertTrue(self.button1 >= self.button1)

        # Same label and priority, should be True
        self.assertTrue(self.button1 >= self.button4)

        # Less priority, should be False
        self.assertFalse(self.button1 >= self.button2)
