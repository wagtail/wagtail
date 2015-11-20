"""
Contains view unit tests.
"""
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.test import TestCase

from wagtail.wagtailcore.models import (
    Page
)
from wagtail.tests.testapp.models import (
    SimplePage
)
from wagtail.tests.utils import WagtailTestUtils


class TestPageRevisionsView(TestCase, WagtailTestUtils):
    def setUp(self):
        # Login.
        self.user = self.login()

        # Find root page.
        self.root_page = Page.objects.get(id=2)

        # Add child page.
        self.child_page = SimplePage(
            title   = 'Test Page',
            slug    = 'test-page',
        )
        self.root_page.add_child(instance=self.child_page)

        # Create revisions.
        for i in range(20):
            self.child_page.save_revision(
                user                        = self.user,
                submitted_for_moderation    = False,
                approved_go_live_at         = None
            )

    def get_get_permission_denied(self):
        self.client.logout()

        with self.assertRaises(PermissionDenied):
            self.client.get(self.get_url())

    def get(self, params=None):
        if not params:
            params = {}

        return self.client.get(
            reverse('wagtailrollbacks:page_revisions', args=(self.child_page.id,)),
            params
        )

    def test_pagination(self):
        # Generate the response.
        page_num    = 2
        response    = self.get({'p': 2})

        # Check assertions.
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            'wagtailrollbacks/edit_handlers/revisions.html'
        )
        self.assertEqual(response.context['revisions'].number, page_num)
        self.assertContains(response, 'Page {0} of '.format(page_num))

    def test_pagination_invalid(self):
        # Generate the response.
        response = self.get({'p': 'fake'})

        # Check assertions.
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            'wagtailrollbacks/edit_handlers/revisions.html'
        )
        self.assertEqual(response.context['revisions'].number, 1)

    def test_pagination_out_of_range(self):
        # Generate the response.
        response = self.get({'p': 99999})

        # Check assertions.
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            'wagtailrollbacks/edit_handlers/revisions.html'
        )
        self.assertEqual(
            response.context['revisions'].number,
           response.context['revisions'].paginator.num_pages
        )

class TestRevisionPreviewView(TestCase, WagtailTestUtils):
    def setUp(self):
        # Login.
        self.user = self.login()

        # Find root page.
        self.root_page = Page.objects.get(id=2)

        # Add child page.
        self.child_page = SimplePage(
            title   = 'Test Page',
            slug    = 'test-page',
        )
        self.root_page.add_child(instance=self.child_page)

        # Create revisions.
        for i in range(20):
            self.child_page.save_revision(
                user                        = self.user,
                submitted_for_moderation    = False,
                approved_go_live_at         = None
            )

    def get_url(self):
        return reverse(
            'wagtailrollbacks:preview_page_version',
            args=(self.child_page.get_latest_revision().id,)
        )

    def get_get_permission_denied(self):
        self.client.logout()

        with self.assertRaises(PermissionDenied):
            self.client.get(self.get_url())

    def test_get(self):
        # Generate the response.
        response = self.client.get(self.get_url())

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tests/simple_page.html')

class TestConfirmPageReversionView(TestCase, WagtailTestUtils):
    def setUp(self):
        # Login.
        self.user = self.login()

        # Find root page.
        self.root_page = Page.objects.get(id=2)

        # Add child page.
        self.child_page = SimplePage(
            title   = 'Test Page',
            slug    = 'test-page',
        )
        self.root_page.add_child(instance=self.child_page)

        # Create revisions.
        for i in range(20):
            self.child_page.save_revision(
                user                        = self.user,
                submitted_for_moderation    = False,
                approved_go_live_at         = None
            )

    def get_url(self):
        return reverse(
            'wagtailrollbacks:confirm_page_reversion',
            args=(self.child_page.get_latest_revision().id,)
        )

    def get_get_permission_denied(self):
        self.client.logout()

        with self.assertRaises(PermissionDenied):
            self.client.get(self.get_url())

    def test_page_is_locked(self):
        self.child_page.locked = True
        Page.objects.filter(pk=self.child_page.pk).update(locked=True)

        response = self.client.get(self.get_url())

        self.assertRedirects(
            response,
            reverse('wagtailadmin_pages:edit', args=(self.child_page.id,))
        )

    def test_get(self):
        response = self.client.get(self.get_url())

        self.assertTemplateUsed(
            response,
            'wagtailrollbacks/pages/confirm_reversion.html'
        )

    def test_post_draft(self):
        response = self.client.post(self.get_url(), {'fake': 'data'})

        self.assertRedirects(
            response,
            reverse('wagtailadmin_explore', args=(self.child_page.get_parent().id,))
        )

    def test_post_publish(self):
        post_data   = {'action-publish': True}
        response    = self.client.post(self.get_url(), post_data)

        self.assertRedirects(
            response,
            reverse('wagtailadmin_explore', args=(self.child_page.get_parent().id,))
        )

    def test_post_submit(self):
        post_data   = {'action-submit': True}
        response    = self.client.post(self.get_url(), post_data)

        self.assertRedirects(
            response,
            reverse('wagtailadmin_explore', args=(self.child_page.get_parent().id,))
        )
