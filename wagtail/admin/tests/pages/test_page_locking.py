from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from wagtail.core.models import Page
from wagtail.tests.testapp.models import SimplePage
from wagtail.tests.utils import WagtailTestUtils


class TestLocking(TestCase, WagtailTestUtils):
    def setUp(self):
        # Find root page
        self.root_page = Page.objects.get(id=2)

        # Login
        self.user = self.login()

        # Create a page and submit it for moderation
        self.child_page = SimplePage(
            title="Hello world!",
            slug='hello-world',
            content="hello",
            live=False,
        )
        self.root_page.add_child(instance=self.child_page)

    def test_lock_post(self):
        response = self.client.post(reverse('wagtailadmin_pages:lock', args=(self.child_page.id, )))

        # Check response
        self.assertRedirects(response, reverse('wagtailadmin_explore', args=(self.root_page.id, )))

        # Check that the page is locked
        self.assertTrue(Page.objects.get(id=self.child_page.id).locked)

    def test_lock_get(self):
        response = self.client.get(reverse('wagtailadmin_pages:lock', args=(self.child_page.id, )))

        # Check response
        self.assertEqual(response.status_code, 405)

        # Check that the page is still unlocked
        self.assertFalse(Page.objects.get(id=self.child_page.id).locked)

    def test_lock_post_already_locked(self):
        # Lock the page
        self.child_page.locked = True
        self.child_page.save()

        response = self.client.post(reverse('wagtailadmin_pages:lock', args=(self.child_page.id, )))

        # Check response
        self.assertRedirects(response, reverse('wagtailadmin_explore', args=(self.root_page.id, )))

        # Check that the page is still locked
        self.assertTrue(Page.objects.get(id=self.child_page.id).locked)

    def test_lock_post_with_good_redirect(self):
        response = self.client.post(reverse('wagtailadmin_pages:lock', args=(self.child_page.id, )), {
            'next': reverse('wagtailadmin_pages:edit', args=(self.child_page.id, ))
        })

        # Check response
        self.assertRedirects(response, reverse('wagtailadmin_pages:edit', args=(self.child_page.id, )))

        # Check that the page is locked
        self.assertTrue(Page.objects.get(id=self.child_page.id).locked)

    def test_lock_post_with_bad_redirect(self):
        response = self.client.post(reverse('wagtailadmin_pages:lock', args=(self.child_page.id, )), {
            'next': 'http://www.google.co.uk'
        })

        # Check response
        self.assertRedirects(response, reverse('wagtailadmin_explore', args=(self.root_page.id, )))

        # Check that the page is locked
        self.assertTrue(Page.objects.get(id=self.child_page.id).locked)

    def test_lock_post_bad_page(self):
        response = self.client.post(reverse('wagtailadmin_pages:lock', args=(9999, )))

        # Check response
        self.assertEqual(response.status_code, 404)

        # Check that the page is still unlocked
        self.assertFalse(Page.objects.get(id=self.child_page.id).locked)

    def test_lock_post_bad_permissions(self):
        # Remove privileges from user
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(content_type__app_label='wagtailadmin', codename='access_admin')
        )
        self.user.save()

        response = self.client.post(reverse('wagtailadmin_pages:lock', args=(self.child_page.id, )))

        # Check response
        self.assertEqual(response.status_code, 403)

        # Check that the page is still unlocked
        self.assertFalse(Page.objects.get(id=self.child_page.id).locked)

    def test_unlock_post(self):
        # Lock the page
        self.child_page.locked = True
        self.child_page.save()

        response = self.client.post(reverse('wagtailadmin_pages:unlock', args=(self.child_page.id, )))

        # Check response
        self.assertRedirects(response, reverse('wagtailadmin_explore', args=(self.root_page.id, )))

        # Check that the page is unlocked
        self.assertFalse(Page.objects.get(id=self.child_page.id).locked)

    def test_unlock_get(self):
        # Lock the page
        self.child_page.locked = True
        self.child_page.save()

        response = self.client.get(reverse('wagtailadmin_pages:unlock', args=(self.child_page.id, )))

        # Check response
        self.assertEqual(response.status_code, 405)

        # Check that the page is still locked
        self.assertTrue(Page.objects.get(id=self.child_page.id).locked)

    def test_unlock_post_already_unlocked(self):
        response = self.client.post(reverse('wagtailadmin_pages:unlock', args=(self.child_page.id, )))

        # Check response
        self.assertRedirects(response, reverse('wagtailadmin_explore', args=(self.root_page.id, )))

        # Check that the page is still unlocked
        self.assertFalse(Page.objects.get(id=self.child_page.id).locked)

    def test_unlock_post_with_good_redirect(self):
        # Lock the page
        self.child_page.locked = True
        self.child_page.save()

        response = self.client.post(reverse('wagtailadmin_pages:unlock', args=(self.child_page.id, )), {
            'next': reverse('wagtailadmin_pages:edit', args=(self.child_page.id, ))
        })

        # Check response
        self.assertRedirects(response, reverse('wagtailadmin_pages:edit', args=(self.child_page.id, )))

        # Check that the page is unlocked
        self.assertFalse(Page.objects.get(id=self.child_page.id).locked)

    def test_unlock_post_with_bad_redirect(self):
        # Lock the page
        self.child_page.locked = True
        self.child_page.save()

        response = self.client.post(reverse('wagtailadmin_pages:unlock', args=(self.child_page.id, )), {
            'next': 'http://www.google.co.uk'
        })

        # Check response
        self.assertRedirects(response, reverse('wagtailadmin_explore', args=(self.root_page.id, )))

        # Check that the page is unlocked
        self.assertFalse(Page.objects.get(id=self.child_page.id).locked)

    def test_unlock_post_bad_page(self):
        # Lock the page
        self.child_page.locked = True
        self.child_page.save()

        response = self.client.post(reverse('wagtailadmin_pages:unlock', args=(9999, )))

        # Check response
        self.assertEqual(response.status_code, 404)

        # Check that the page is still locked
        self.assertTrue(Page.objects.get(id=self.child_page.id).locked)

    def test_unlock_post_bad_permissions(self):
        # Remove privileges from user
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(content_type__app_label='wagtailadmin', codename='access_admin')
        )
        self.user.save()

        # Lock the page
        self.child_page.locked = True
        self.child_page.save()

        response = self.client.post(reverse('wagtailadmin_pages:unlock', args=(self.child_page.id, )))

        # Check response
        self.assertEqual(response.status_code, 403)

        # Check that the page is still locked
        self.assertTrue(Page.objects.get(id=self.child_page.id).locked)
