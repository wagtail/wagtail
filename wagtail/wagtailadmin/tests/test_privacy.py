from itertools import count
from django.contrib.auth.models import Group
from django.test import TestCase
from django.core.urlresolvers import reverse

from wagtail.wagtailcore.models import Page, PageViewRestriction
from wagtail.tests.models import SimplePage
from wagtail.tests.utils import WagtailTestUtils


class TestSetPrivacyView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

        # Create some pages
        self.homepage = Page.objects.get(id=2)

        self.public_page = self.homepage.add_child(instance=SimplePage(
            title="Public page",
            slug='public-page',
            live=True,
        ))

        self.private_page = self.homepage.add_child(instance=SimplePage(
            title="Private page",
            slug='private-page',
            live=True,
        ))
        PageViewRestriction.objects.create(page=self.private_page, password='password123')

        self.private_child_page = self.private_page.add_child(instance=SimplePage(
            title="Private child page",
            slug='private-child-page',
            live=True,
        ))

        self.private_groups_page = self.homepage.add_child(instance=SimplePage(
            title="Private groups page",
            slug='private-groups-page',
            live=True,
        ))
        restriction = PageViewRestriction.objects.create(page=self.private_groups_page, password='')
        self.group = Group.objects.create(name='Private page group')
        self.group2 = Group.objects.create(name='Private page group2')
        restriction.groups.add(self.group)
        restriction.groups.add(self.group2)

        self.private_groups_child_page = self.private_groups_page.add_child(instance=SimplePage(
            title="Private groups child page",
            slug='private-groups-child-page',
            live=True,
        ))

    def test_get_public(self):
        """
        This tests that a blank form is returned when a user opens the set_privacy view on a public page
        """
        response = self.client.get(reverse('wagtailadmin_pages_set_privacy', args=(self.public_page.id, )))

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/page_privacy/set_privacy.html')
        self.assertEqual(response.context['page'].specific, self.public_page)

        # Check form attributes
        self.assertEqual(response.context['form']['restriction_type'].value(), 'none')

    def test_get_private(self):
        """
        This tests that the restriction type and password fields as set correctly when a user opens the set_privacy view on a public page
        """
        response = self.client.get(reverse('wagtailadmin_pages_set_privacy', args=(self.private_page.id, )))

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/page_privacy/set_privacy.html')
        self.assertEqual(response.context['page'].specific, self.private_page)

        # Check form attributes
        self.assertEqual(response.context['form']['restriction_type'].value(), 'password')
        self.assertEqual(response.context['form']['password'].value(), 'password123')
        self.assertEqual(response.context['form']['groups'].value(), [])

    def test_get_private_child(self):
        """
        This tests that the set_privacy view tells the user that the password restriction has been applied to an ancestor
        """
        response = self.client.get(reverse('wagtailadmin_pages_set_privacy', args=(self.private_child_page.id, )))

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/page_privacy/ancestor_privacy.html')
        self.assertEqual(response.context['page_with_restriction'].specific, self.private_page)

    def test_set_password_restriction(self):
        """
        This tests that setting a password restriction using the set_privacy view works
        """
        post_data = {
            'restriction_type': 'password',
            'password': 'helloworld',
            'groups': [],
        }
        response = self.client.post(reverse('wagtailadmin_pages_set_privacy', args=(self.public_page.id, )), post_data)

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "modal.respond('setPermission', false);")

        # Check that a page restriction has been created
        self.assertTrue(PageViewRestriction.objects.filter(page=self.public_page).exists())

        # Check that the password is set correctly
        self.assertEqual(PageViewRestriction.objects.get(page=self.public_page).password, 'helloworld')

        # Be sure there are no groups set
        self.assertEqual(PageViewRestriction.objects.get(page=self.public_page).groups.all().count(), 0)

    def test_set_password_restriction_password_unset(self):
        """
        This tests that the password field on the form is validated correctly
        """
        post_data = {
            'restriction_type': 'password',
            'password': '',
            'groups': [],
        }
        response = self.client.post(reverse('wagtailadmin_pages_set_privacy', args=(self.public_page.id, )), post_data)

        # Check response
        self.assertEqual(response.status_code, 200)

        # Check that a form error was raised
        self.assertFormError(response, 'form', 'password', "This field is required.")

    def test_unset_password_restriction(self):
        """
        This tests that removing a password restriction using the set_privacy view works
        """
        post_data = {
            'restriction_type': 'none',
            'password': '',
            'groups': [],
        }
        response = self.client.post(reverse('wagtailadmin_pages_set_privacy', args=(self.private_page.id, )), post_data)

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "modal.respond('setPermission', true);")

        # Check that the page restriction has been deleted
        self.assertFalse(PageViewRestriction.objects.filter(page=self.private_page).exists())


    def test_get_private_groups(self):
        """
        This tests that the restriction type and group fields as set correctly when a user opens the set_privacy view on a public page
        """
        response = self.client.get(reverse('wagtailadmin_pages_set_privacy', args=(self.private_groups_page.id, )))

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/page_privacy/set_privacy.html')
        self.assertEqual(response.context['page'].specific, self.private_groups_page)

        # Check form attributes
        self.assertEqual(response.context['form']['restriction_type'].value(), 'group')
        self.assertEqual(response.context['form']['password'].value(), '')
        self.assertEqual(response.context['form']['groups'].value(), [self.group.id, self.group2.id])

    def test_set_group_restriction(self):
        """
        This tests that setting a group restriction using the set_privacy view works
        """
        post_data = {
            'restriction_type': 'group',
            'password': '',
            'groups': [self.group.id, self.group2.id],
        }
        response = self.client.post(reverse('wagtailadmin_pages_set_privacy', args=(self.public_page.id, )), post_data)

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "modal.respond('setPermission', false);")

        # Check that a page restriction has been created
        self.assertTrue(PageViewRestriction.objects.filter(page=self.public_page).exists())

        # Be sure there is no password set
        self.assertEqual(PageViewRestriction.objects.get(page=self.public_page).password, '')

        # Check that the groups are set correctly
        self.assertEqual(PageViewRestriction.objects.get(page=self.public_page).groups.all()[0], self.group)
        self.assertEqual(PageViewRestriction.objects.get(page=self.public_page).groups.all()[1], self.group2)
        self.assertEqual(PageViewRestriction.objects.get(page=self.public_page).groups.all().count(), 2)

    def test_set_group_restriction_password_unset(self):
        """
        This tests that the group fields on the form are validated correctly
        """
        post_data = {
            'restriction_type': 'group',
            'password': '',
            'groups': [],
        }
        response = self.client.post(reverse('wagtailadmin_pages_set_privacy', args=(self.public_page.id, )), post_data)

        # Check response
        self.assertEqual(response.status_code, 200)

        # Check that a form error was raised
        self.assertFormError(response, 'form', 'groups', "This field is required.")

    def test_unset_group_restriction(self):
        """
        This tests that removing a groups restriction using the set_privacy view works
        This is currently the same as testing for unset password.
        """
        post_data = {
            'restriction_type': 'none',
            'password': '',
            'groups': [],
        }
        response = self.client.post(reverse('wagtailadmin_pages_set_privacy', args=(self.private_page.id, )), post_data)

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "modal.respond('setPermission', true);")

        # Check that the page restriction has been deleted
        self.assertFalse(PageViewRestriction.objects.filter(page=self.private_page).exists())


class TestPrivacyIndicators(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

        # Create some pages
        self.homepage = Page.objects.get(id=2)

        self.public_page = self.homepage.add_child(instance=SimplePage(
            title="Public page",
            slug='public-page',
            live=True,
        ))

        self.private_page = self.homepage.add_child(instance=SimplePage(
            title="Private page",
            slug='private-page',
            live=True,
        ))
        PageViewRestriction.objects.create(page=self.private_page, password='password123')

        self.private_child_page = self.private_page.add_child(instance=SimplePage(
            title="Private child page",
            slug='private-child-page',
            live=True,
        ))

    def test_explorer_public(self):
        """
        This tests that the privacy indicator on the public pages explore view is set to "PUBLIC"
        """
        response = self.client.get(reverse('wagtailadmin_explore', args=(self.public_page.id, )))

        # Check the response
        self.assertEqual(response.status_code, 200)

        # Check the privacy indicator is public
        self.assertTemplateUsed(response, 'wagtailadmin/pages/_privacy_indicator.html')
        self.assertContains(response, '<div class="privacy-indicator public">')
        self.assertNotContains(response, '<div class="privacy-indicator private">')

    def test_explorer_private(self):
        """
        This tests that the privacy indicator on the private pages explore view is set to "PRIVATE"
        """
        response = self.client.get(reverse('wagtailadmin_explore', args=(self.private_page.id, )))

        # Check the response
        self.assertEqual(response.status_code, 200)

        # Check the privacy indicator is public
        self.assertTemplateUsed(response, 'wagtailadmin/pages/_privacy_indicator.html')
        self.assertContains(response, '<div class="privacy-indicator private">')
        self.assertNotContains(response, '<div class="privacy-indicator public">')

    def test_explorer_private_child(self):
        """
        This tests that the privacy indicator on the private child pages explore view is set to "PRIVATE"
        """
        response = self.client.get(reverse('wagtailadmin_explore', args=(self.private_child_page.id, )))

        # Check the response
        self.assertEqual(response.status_code, 200)

        # Check the privacy indicator is public
        self.assertTemplateUsed(response, 'wagtailadmin/pages/_privacy_indicator.html')
        self.assertContains(response, '<div class="privacy-indicator private">')
        self.assertNotContains(response, '<div class="privacy-indicator public">')

    def test_explorer_list_homepage(self):
        """
        This tests that there is a padlock displayed next to the private page in the homepages explorer listing
        """
        response = self.client.get(reverse('wagtailadmin_explore', args=(self.homepage.id, )))

        # Check the response
        self.assertEqual(response.status_code, 200)

        # Must have one privacy icon (next to the private page)
        self.assertContains(response, "<span class=\"indicator privacy-indicator icon icon-no-view\"", count=1)

    def test_explorer_list_private(self):
        """
        This tests that there is a padlock displayed next to the private child page in the private pages explorer listing
        """
        response = self.client.get(reverse('wagtailadmin_explore', args=(self.private_page.id, )))

        # Check the response
        self.assertEqual(response.status_code, 200)

        # Must have one privacy icon (next to the private child page)
        self.assertContains(response, "<span class=\"indicator privacy-indicator icon icon-no-view\"", count=1)

    def test_edit_public(self):
        """
        This tests that the privacy indicator on the public pages edit view is set to "PUBLIC"
        """
        response = self.client.get(reverse('wagtailadmin_pages_edit', args=(self.public_page.id, )))

        # Check the response
        self.assertEqual(response.status_code, 200)

        # Check the privacy indicator is public
        self.assertTemplateUsed(response, 'wagtailadmin/pages/_privacy_indicator.html')
        self.assertContains(response, '<div class="privacy-indicator public">')
        self.assertNotContains(response, '<div class="privacy-indicator private">')

    def test_edit_private(self):
        """
        This tests that the privacy indicator on the private pages edit view is set to "PRIVATE"
        """
        response = self.client.get(reverse('wagtailadmin_pages_edit', args=(self.private_page.id, )))

        # Check the response
        self.assertEqual(response.status_code, 200)

        # Check the privacy indicator is public
        self.assertTemplateUsed(response, 'wagtailadmin/pages/_privacy_indicator.html')
        self.assertContains(response, '<div class="privacy-indicator private">')
        self.assertNotContains(response, '<div class="privacy-indicator public">')

    def test_edit_private_child(self):
        """
        This tests that the privacy indicator on the private child pages edit view is set to "PRIVATE"
        """
        response = self.client.get(reverse('wagtailadmin_pages_edit', args=(self.private_child_page.id, )))

        # Check the response
        self.assertEqual(response.status_code, 200)

        # Check the privacy indicator is public
        self.assertTemplateUsed(response, 'wagtailadmin/pages/_privacy_indicator.html')
        self.assertContains(response, '<div class="privacy-indicator private">')
        self.assertNotContains(response, '<div class="privacy-indicator public">')
