from django.test import TestCase
from django.core.urlresolvers import reverse

from wagtail.wagtailcore.models import Page, PageViewRestriction
from wagtail.tests.testapp.models import SimplePage
from wagtail.tests.utils import WagtailTestUtils


class TestSetPrivacyView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

        # Create some pages
        self.homepage = Page.objects.get(id=2)

        self.public_page = self.homepage.add_child(instance=SimplePage(
            title="Public page",
            content="hello",
            live=True,
        ))

        self.private_page = self.homepage.add_child(instance=SimplePage(
            title="Private page",
            content="hello",
            live=True,
        ))
        PageViewRestriction.objects.create(page=self.private_page, password='password123')

        self.private_child_page = self.private_page.add_child(instance=SimplePage(
            title="Private child page",
            content="hello",
            live=True,
        ))

    def test_get_public(self):
        """
        This tests that a blank form is returned when a user opens the set_privacy view on a public page
        """
        response = self.client.get(reverse('wagtailadmin_pages:set_privacy', args=(self.public_page.id, )))

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/page_privacy/set_privacy.html')
        self.assertEqual(response.context['page'].specific, self.public_page)

        # Check form attributes
        self.assertEqual(response.context['form']['restriction_type'].value(), 'none')

    def test_get_private(self):
        """
        This tests that the restriction type and password fields as set correctly
        when a user opens the set_privacy view on a public page
        """
        response = self.client.get(reverse('wagtailadmin_pages:set_privacy', args=(self.private_page.id, )))

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/page_privacy/set_privacy.html')
        self.assertEqual(response.context['page'].specific, self.private_page)

        # Check form attributes
        self.assertEqual(response.context['form']['restriction_type'].value(), 'password')
        self.assertEqual(response.context['form']['password'].value(), 'password123')

    def test_get_private_child(self):
        """
        This tests that the set_privacy view tells the user
        that the password restriction has been applied to an ancestor
        """
        response = self.client.get(reverse('wagtailadmin_pages:set_privacy', args=(self.private_child_page.id, )))

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
        }
        response = self.client.post(reverse('wagtailadmin_pages:set_privacy', args=(self.public_page.id, )), post_data)

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "modal.respond('setPermission', false);")

        # Check that a page restriction has been created
        self.assertTrue(PageViewRestriction.objects.filter(page=self.public_page).exists())

        # Check that the password is set correctly
        self.assertEqual(PageViewRestriction.objects.get(page=self.public_page).password, 'helloworld')

    def test_set_password_restriction_password_unset(self):
        """
        This tests that the password field on the form is validated correctly
        """
        post_data = {
            'restriction_type': 'password',
            'password': '',
        }
        response = self.client.post(reverse('wagtailadmin_pages:set_privacy', args=(self.public_page.id, )), post_data)

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
        }
        response = self.client.post(reverse('wagtailadmin_pages:set_privacy', args=(self.private_page.id, )), post_data)

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
            content="hello",
            live=True,
        ))

        self.private_page = self.homepage.add_child(instance=SimplePage(
            title="Private page",
            content="hello",
            live=True,
        ))
        PageViewRestriction.objects.create(page=self.private_page, password='password123')

        self.private_child_page = self.private_page.add_child(instance=SimplePage(
            title="Private child page",
            content="hello",
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
        self.assertTemplateUsed(response, 'wagtailadmin/pages/_privacy_switch.html')
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
        self.assertTemplateUsed(response, 'wagtailadmin/pages/_privacy_switch.html')
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
        self.assertTemplateUsed(response, 'wagtailadmin/pages/_privacy_switch.html')
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
        This tests that there is a padlock displayed
        next to the private child page in the private pages explorer listing
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
        response = self.client.get(reverse('wagtailadmin_pages:edit', args=(self.public_page.id, )))

        # Check the response
        self.assertEqual(response.status_code, 200)

        # Check the privacy indicator is public
        self.assertTemplateUsed(response, 'wagtailadmin/pages/_privacy_switch.html')
        self.assertContains(response, '<div class="privacy-indicator public">')
        self.assertNotContains(response, '<div class="privacy-indicator private">')

    def test_edit_private(self):
        """
        This tests that the privacy indicator on the private pages edit view is set to "PRIVATE"
        """
        response = self.client.get(reverse('wagtailadmin_pages:edit', args=(self.private_page.id, )))

        # Check the response
        self.assertEqual(response.status_code, 200)

        # Check the privacy indicator is public
        self.assertTemplateUsed(response, 'wagtailadmin/pages/_privacy_switch.html')
        self.assertContains(response, '<div class="privacy-indicator private">')
        self.assertNotContains(response, '<div class="privacy-indicator public">')

    def test_edit_private_child(self):
        """
        This tests that the privacy indicator on the private child pages edit view is set to "PRIVATE"
        """
        response = self.client.get(reverse('wagtailadmin_pages:edit', args=(self.private_child_page.id, )))

        # Check the response
        self.assertEqual(response.status_code, 200)

        # Check the privacy indicator is public
        self.assertTemplateUsed(response, 'wagtailadmin/pages/_privacy_switch.html')
        self.assertContains(response, '<div class="privacy-indicator private">')
        self.assertNotContains(response, '<div class="privacy-indicator public">')
