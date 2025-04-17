from django.contrib.auth.models import Group
from django.test import TestCase, override_settings
from django.urls import reverse

from wagtail.admin.staticfiles import versioned_static
from wagtail.models import Page, PageViewRestriction
from wagtail.test.testapp.models import SimplePage
from wagtail.test.utils import WagtailTestUtils


class TestSetPrivacyView(WagtailTestUtils, TestCase):
    def setUp(self):
        self.login()

        # Create some pages
        self.homepage = Page.objects.get(id=2)

        self.public_page = self.homepage.add_child(
            instance=SimplePage(
                title="Public page",
                content="hello",
                live=True,
            )
        )

        self.private_page = self.homepage.add_child(
            instance=SimplePage(
                title="Private page",
                content="hello",
                live=True,
            )
        )
        PageViewRestriction.objects.create(
            page=self.private_page, restriction_type="password", password="password123"
        )

        self.private_child_page = self.private_page.add_child(
            instance=SimplePage(
                title="Private child page",
                content="hello",
                live=True,
            )
        )

        self.private_groups_page = self.homepage.add_child(
            instance=SimplePage(
                title="Private groups page",
                content="hello",
                live=True,
            )
        )
        restriction = PageViewRestriction.objects.create(
            page=self.private_groups_page, restriction_type="groups"
        )
        self.group = Group.objects.create(name="Private page group")
        self.group2 = Group.objects.create(name="Private page group2")
        restriction.groups.add(self.group)
        restriction.groups.add(self.group2)

        self.private_groups_child_page = self.private_groups_page.add_child(
            instance=SimplePage(
                title="Private groups child page",
                content="hello",
                live=True,
            )
        )

    def test_get_public(self):
        """
        This tests that a blank form is returned when a user opens the set_privacy view on a public page
        """
        response = self.client.get(
            reverse("wagtailadmin_pages:set_privacy", args=(self.public_page.id,))
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/page_privacy/set_privacy.html")
        self.assertEqual(response.context["page"].specific, self.public_page)

        # Check form attributes
        self.assertEqual(response.context["form"]["restriction_type"].value(), "none")

    def test_get_private(self):
        """
        This tests that the restriction type and password fields as set correctly
        when a user opens the set_privacy view on a public page
        """
        response = self.client.get(
            reverse("wagtailadmin_pages:set_privacy", args=(self.private_page.id,))
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/page_privacy/set_privacy.html")
        self.assertEqual(response.context["page"].specific, self.private_page)

        # Check form attributes
        self.assertEqual(
            response.context["form"]["restriction_type"].value(), "password"
        )
        self.assertEqual(response.context["form"]["password"].value(), "password123")
        self.assertEqual(response.context["form"]["groups"].value(), [])

    def test_get_private_child(self):
        """
        This tests that the set_privacy view tells the user
        that the password restriction has been applied to an ancestor
        """
        response = self.client.get(
            reverse(
                "wagtailadmin_pages:set_privacy", args=(self.private_child_page.id,)
            )
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        parent_edit_url = reverse(
            "wagtailadmin_pages:edit",
            args=(self.private_page.pk,),
        )
        html = response.json()["html"]
        self.assertIn(
            f"<span>Privacy is inherited from the ancestor page - "
            f'<a href="{parent_edit_url}">Private page (simple page)</a></span>',
            html,
        )

    def test_set_password_restriction(self):
        """
        This tests that setting a password restriction using the set_privacy view works
        """
        post_data = {
            "restriction_type": "password",
            "password": "helloworld",
            "groups": [],
        }
        response = self.client.post(
            reverse("wagtailadmin_pages:set_privacy", args=(self.public_page.id,)),
            post_data,
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '"is_public": false')

        # Check that a page restriction has been created
        self.assertTrue(
            PageViewRestriction.objects.filter(page=self.public_page).exists()
        )
        restriction = PageViewRestriction.objects.get(page=self.public_page)

        # Check that the password is set correctly
        self.assertEqual(restriction.password, "helloworld")

        # Check that the restriction_type is set correctly
        self.assertEqual(restriction.restriction_type, "password")

        # Be sure there are no groups set
        self.assertEqual(restriction.groups.count(), 0)

    def test_set_password_restriction_password_unset(self):
        """
        This tests that the password field on the form is validated correctly
        """
        post_data = {
            "restriction_type": "password",
            "password": "",
            "groups": [],
        }
        response = self.client.post(
            reverse("wagtailadmin_pages:set_privacy", args=(self.public_page.id,)),
            post_data,
        )

        # Check response
        self.assertEqual(response.status_code, 200)

        # Check that a form error was raised
        self.assertFormError(
            response.context["form"], "password", "This field is required."
        )

    def test_unset_password_restriction(self):
        """
        This tests that removing a password restriction using the set_privacy view works
        """
        post_data = {
            "restriction_type": "none",
            "password": "",
            "groups": [],
        }
        response = self.client.post(
            reverse("wagtailadmin_pages:set_privacy", args=(self.private_page.id,)),
            post_data,
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '"is_public": true')

        # Check that the page restriction has been deleted
        self.assertFalse(
            PageViewRestriction.objects.filter(page=self.private_page).exists()
        )

        history_url = reverse(
            "wagtailadmin_pages:history", kwargs={"page_id": self.private_page.id}
        )
        history_response = self.client.get(history_url)

        # Check that the expected log message is present
        expected_log_message = "Removed the &#x27;Private, accessible with a shared password&#x27; view restriction. The page is public."
        self.assertContains(
            history_response,
            expected_log_message,
        )

    def test_set_shared_password_page(self):
        response = self.client.get(
            reverse("wagtailadmin_pages:set_privacy", args=(self.public_page.id,)),
        )

        input_el = self.get_soup(response.content).select_one("[data-field-input]")
        self.assertEqual(response.status_code, 200)

        # check that input option for password is visible
        self.assertIn("password", response.context["form"].fields)

        # check that the option for password is visible
        self.assertIsNotNone(input_el)

    @override_settings(WAGTAIL_PRIVATE_PAGE_OPTIONS={"SHARED_PASSWORD": False})
    def test_unset_shared_password_page(self):
        response = self.client.get(
            reverse("wagtailadmin_pages:set_privacy", args=(self.public_page.id,)),
        )
        self.assertEqual(response.status_code, 200)

        # check that input option for password is not visible
        self.assertNotIn("password", response.context["form"].fields)
        self.assertFalse(
            response.context["form"]
            .fields["restriction_type"]
            .valid_value(PageViewRestriction.PASSWORD)
        )

        # check that the option for password is not visible
        self.assertNotContains(
            response, '<div class="w-field__input" data-field-input>'
        )

    def test_get_private_groups(self):
        """
        This tests that the restriction type and group fields as set correctly when a user opens the set_privacy view on a public page
        """
        response = self.client.get(
            reverse(
                "wagtailadmin_pages:set_privacy", args=(self.private_groups_page.id,)
            )
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/page_privacy/set_privacy.html")
        self.assertEqual(response.context["page"].specific, self.private_groups_page)

        # Check form attributes
        self.assertEqual(response.context["form"]["restriction_type"].value(), "groups")
        self.assertEqual(response.context["form"]["password"].value(), "")
        self.assertEqual(
            response.context["form"]["groups"].value(), [self.group.id, self.group2.id]
        )

    def test_set_group_restriction(self):
        """
        This tests that setting a group restriction using the set_privacy view works
        """
        post_data = {
            "restriction_type": "groups",
            "password": "",
            "groups": [self.group.id, self.group2.id],
        }
        response = self.client.post(
            reverse("wagtailadmin_pages:set_privacy", args=(self.public_page.id,)),
            post_data,
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '"is_public": false')

        # Check that a page restriction has been created
        self.assertTrue(
            PageViewRestriction.objects.filter(page=self.public_page).exists()
        )

        restriction = PageViewRestriction.objects.get(page=self.public_page)

        # restriction_type should be 'groups'
        self.assertEqual(restriction.restriction_type, "groups")

        # Be sure there is no password set
        self.assertEqual(restriction.password, "")

        # Check that the groups are set correctly
        self.assertEqual(
            set(PageViewRestriction.objects.get(page=self.public_page).groups.all()),
            {self.group, self.group2},
        )

    def test_set_group_restriction_password_unset(self):
        """
        This tests that the group fields on the form are validated correctly
        """
        post_data = {
            "restriction_type": "groups",
            "password": "",
            "groups": [],
        }
        response = self.client.post(
            reverse("wagtailadmin_pages:set_privacy", args=(self.public_page.id,)),
            post_data,
        )

        # Check response
        self.assertEqual(response.status_code, 200)

        # Check that a form error was raised
        self.assertFormError(
            response.context["form"], "groups", "Please select at least one group."
        )

    def test_unset_group_restriction(self):
        """
        This tests that removing a groups restriction using the set_privacy view works
        """
        post_data = {
            "restriction_type": "none",
            "password": "",
            "groups": [],
        }
        response = self.client.post(
            reverse("wagtailadmin_pages:set_privacy", args=(self.private_page.id,)),
            post_data,
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '"is_public": true')

        # Check that the page restriction has been deleted
        self.assertFalse(
            PageViewRestriction.objects.filter(page=self.private_page).exists()
        )


class TestPrivacyIndicators(WagtailTestUtils, TestCase):
    def setUp(self):
        self.login()

        # Create some pages
        self.homepage = Page.objects.get(id=2)

        self.public_page = self.homepage.add_child(
            instance=SimplePage(
                title="Public page",
                content="hello",
                live=True,
            )
        )

        self.private_page = self.homepage.add_child(
            instance=SimplePage(
                title="Private page",
                content="hello",
                live=True,
            )
        )
        PageViewRestriction.objects.create(
            page=self.private_page, restriction_type="password", password="password123"
        )

        self.private_child_page = self.private_page.add_child(
            instance=SimplePage(
                title="Private child page",
                content="hello",
                live=True,
            )
        )

    def test_explorer_public(self):
        """
        This tests that the privacy indicator on the public pages explore view is set to "PUBLIC"
        """
        response = self.client.get(
            reverse("wagtailadmin_explore", args=(self.public_page.id,))
        )

        # Check the response
        self.assertEqual(response.status_code, 200)

        soup = self.get_soup(response.content)

        public_link = soup.select_one('[data-w-zone-switch-key-value="isPublic"]')
        private_link = soup.select_one('[data-w-zone-switch-key-value="!isPublic"]')

        # Check the privacy indicator is public
        self.assertEqual(private_link["class"], ["page-status-tag", "w-hidden"])

        # Check the privacy indicator is private
        self.assertEqual(public_link["class"], ["page-status-tag"])

    def test_explorer_private(self):
        """
        This tests that the privacy indicator on the private pages explore view is set to "PRIVATE"
        """
        response = self.client.get(
            reverse("wagtailadmin_explore", args=(self.private_page.id,))
        )

        # Check the response
        self.assertEqual(response.status_code, 200)

        soup = self.get_soup(response.content)

        public_link = soup.select_one('[data-w-zone-switch-key-value="isPublic"]')
        private_link = soup.select_one('[data-w-zone-switch-key-value="!isPublic"]')

        # Check the private privacy indicator is visible
        self.assertEqual(private_link["class"], ["page-status-tag"])

        # Check the public privacy indicator is hidden
        self.assertEqual(public_link["class"], ["page-status-tag", "w-hidden"])

    def test_explorer_private_child(self):
        """
        This tests that the privacy indicator on the private child pages explore view is set to "PRIVATE"
        """
        response = self.client.get(
            reverse("wagtailadmin_explore", args=(self.private_child_page.id,))
        )

        # Check the response
        self.assertEqual(response.status_code, 200)

        soup = self.get_soup(response.content)

        public_link = soup.select_one('[data-w-zone-switch-key-value="isPublic"]')
        private_link = soup.select_one('[data-w-zone-switch-key-value="!isPublic"]')

        # Check the privacy indicator is private
        self.assertEqual(private_link["class"], ["page-status-tag"])

        # Check the public privacy indicator is hidden
        self.assertEqual(public_link["class"], ["page-status-tag", "w-hidden"])

    def test_explorer_list_homepage(self):
        """
        This tests that there is a padlock displayed next to the private page in the homepages explorer listing
        """
        response = self.client.get(
            reverse("wagtailadmin_explore", args=(self.homepage.id,))
        )

        # Check the response
        self.assertEqual(response.status_code, 200)

        # Must have one privacy icon (next to the private page)
        self.assertContains(
            response,
            'class="indicator privacy-indicator"',
            count=1,
        )

    def test_explorer_list_private(self):
        """
        This tests that there is a padlock displayed
        next to the private child page in the private pages explorer listing
        """
        response = self.client.get(
            reverse("wagtailadmin_explore", args=(self.private_page.id,))
        )

        # Check the response
        self.assertEqual(response.status_code, 200)

        # Must have one privacy icon (next to the private child page)
        self.assertContains(
            response,
            'class="indicator privacy-indicator"',
            count=1,
        )

    def test_edit_public(self):
        """
        This tests that the privacy indicator on the public pages edit view is set to "PUBLIC"
        """
        response = self.client.get(
            reverse("wagtailadmin_pages:edit", args=(self.public_page.id,))
        )

        # Check the response
        self.assertEqual(response.status_code, 200)

        soup = self.get_soup(response.content)

        privacy_switch_js = versioned_static("wagtailadmin/js/privacy-switch.js")

        public_link = soup.select_one('[data-w-zone-switch-key-value="isPublic"]')
        private_link = soup.select_one('[data-w-zone-switch-key-value="!isPublic"]')
        scripts = soup.select(f"script[src='{privacy_switch_js}']")

        self.assertEqual(len(scripts), 1)
        # Check the privacy indicator is public
        self.assertEqual(public_link["class"], ["page-status-tag"])

        self.assertEqual(private_link["class"], ["page-status-tag", "w-hidden"])

    def test_edit_private(self):
        """
        This tests that the privacy indicator on the private pages edit view is set to "PRIVATE"
        """
        response = self.client.get(
            reverse("wagtailadmin_pages:edit", args=(self.private_page.id,))
        )

        # Check the response
        self.assertEqual(response.status_code, 200)

        soup = self.get_soup(response.content)

        privacy_switch_js = versioned_static("wagtailadmin/js/privacy-switch.js")

        public_link = soup.select_one('[data-w-zone-switch-key-value="isPublic"]')
        private_link = soup.select_one('[data-w-zone-switch-key-value="!isPublic"]')
        scripts = soup.select(f"script[src='{privacy_switch_js}']")

        self.assertEqual(len(scripts), 1)

        # Check the privacy indicator is private
        self.assertEqual(private_link["class"], ["page-status-tag"])

        self.assertEqual(public_link["class"], ["page-status-tag", "w-hidden"])

    def test_edit_private_child(self):
        """
        This tests that the privacy indicator on the private child pages edit view is set to "PRIVATE"
        """
        response = self.client.get(
            reverse("wagtailadmin_pages:edit", args=(self.private_child_page.id,))
        )

        # Check the response
        self.assertEqual(response.status_code, 200)

        # Check the privacy indicator is private
        soup = self.get_soup(response.content)

        public_link = soup.select_one('[data-w-zone-switch-key-value="isPublic"]')
        private_link = soup.select_one('[data-w-zone-switch-key-value="!isPublic"]')

        # Check the privacy indicator is private
        self.assertEqual(private_link["class"], ["page-status-tag"])

        self.assertEqual(public_link["class"], ["page-status-tag", "w-hidden"])

    def test_private_page_options_only_password_groups(self):
        # change the private_page_options to password and login
        original_private_page_options = self.public_page.private_page_options
        self.public_page.specific.__class__.private_page_options = [
            "password",
            "groups",
        ]

        response = self.client.get(
            reverse("wagtailadmin_pages:set_privacy", args=(self.public_page.id,))
        )

        restriction_types = [
            choice[0]
            for choice in response.context["form"].fields["restriction_type"].choices
        ]

        # Check response
        self.assertListEqual(restriction_types, ["none", "password", "groups"])

        # Reset the private_page_options to previous value
        self.public_page.specific.__class__.private_page_options = (
            original_private_page_options
        )

    def test_private_page_options_only_password_login(self):
        # change the private_page_options to password and login
        original_private_page_options = self.public_page.private_page_options
        self.public_page.specific.__class__.private_page_options = ["password", "login"]

        response = self.client.get(
            reverse("wagtailadmin_pages:set_privacy", args=(self.public_page.id,))
        )

        restriction_types = [
            choice[0]
            for choice in response.context["form"].fields["restriction_type"].choices
        ]

        # Check response
        self.assertListEqual(restriction_types, ["none", "password", "login"])

        # Reset the private_page_options to previous value
        self.public_page.specific.__class__.private_page_options = (
            original_private_page_options
        )

    def test_private_page_no_options(self):
        # change the private_page_options to empty list
        original_private_page_options = self.public_page.private_page_options
        self.public_page.specific.__class__.private_page_options = []

        response = self.client.get(
            reverse("wagtailadmin_pages:set_privacy", args=(self.public_page.id,))
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/page_privacy/no_privacy.html")

        # Reset the private_page_options to previous value
        self.public_page.specific.__class__.private_page_options = (
            original_private_page_options
        )
