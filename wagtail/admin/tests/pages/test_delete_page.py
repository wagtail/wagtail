from unittest import mock

from django.contrib.auth.models import Permission
from django.db.models.signals import post_delete, pre_delete
from django.http import HttpRequest, HttpResponse
from django.test import TestCase
from django.urls import reverse

from wagtail.core.models import Page
from wagtail.core.signals import page_unpublished
from wagtail.tests.testapp.models import SimplePage, StandardChild, StandardIndex
from wagtail.tests.utils import WagtailTestUtils


class TestPageDelete(TestCase, WagtailTestUtils):
    def setUp(self):
        # Find root page
        self.root_page = Page.objects.get(id=2)

        # Add child page
        self.child_page = SimplePage(title="Hello world!", slug="hello-world", content="hello")
        self.root_page.add_child(instance=self.child_page)

        # Add a page with child pages of its own
        self.child_index = StandardIndex(title="Hello index", slug='hello-index')
        self.root_page.add_child(instance=self.child_index)
        self.grandchild_page = StandardChild(title="Hello Kitty", slug='hello-kitty')
        self.child_index.add_child(instance=self.grandchild_page)

        # Login
        self.user = self.login()

    def test_page_delete(self):
        response = self.client.get(reverse('wagtailadmin_pages:delete', args=(self.child_page.id, )))
        self.assertEqual(response.status_code, 200)
        # deletion should not actually happen on GET
        self.assertTrue(SimplePage.objects.filter(id=self.child_page.id).exists())

    def test_page_delete_specific_admin_title(self):
        response = self.client.get(reverse('wagtailadmin_pages:delete', args=(self.child_page.id, )))
        self.assertEqual(response.status_code, 200)

        # The admin_display_title specific to ChildPage is shown on the delete confirmation page.
        self.assertContains(response, self.child_page.get_admin_display_title())

    def test_page_delete_bad_permissions(self):
        # Remove privileges from user
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(content_type__app_label='wagtailadmin', codename='access_admin')
        )
        self.user.save()

        # Get delete page
        response = self.client.get(reverse('wagtailadmin_pages:delete', args=(self.child_page.id, )))

        # Check that the user received a 302 redirect response
        self.assertEqual(response.status_code, 302)

        # Check that the deletion has not happened
        self.assertTrue(SimplePage.objects.filter(id=self.child_page.id).exists())

    def test_page_delete_post(self):
        # Connect a mock signal handler to page_unpublished signal
        mock_handler = mock.MagicMock()
        page_unpublished.connect(mock_handler)

        # Post
        response = self.client.post(reverse('wagtailadmin_pages:delete', args=(self.child_page.id, )))

        # Should be redirected to explorer page
        self.assertRedirects(response, reverse('wagtailadmin_explore', args=(self.root_page.id, )))

        # treebeard should report no consistency problems with the tree
        self.assertFalse(any(Page.find_problems()), 'treebeard found consistency problems')

        # Check that the page is gone
        self.assertEqual(Page.objects.filter(path__startswith=self.root_page.path, slug='hello-world').count(), 0)

        # Check that the page_unpublished signal was fired
        self.assertEqual(mock_handler.call_count, 1)
        mock_call = mock_handler.mock_calls[0][2]

        self.assertEqual(mock_call['sender'], self.child_page.specific_class)
        self.assertEqual(mock_call['instance'], self.child_page)
        self.assertIsInstance(mock_call['instance'], self.child_page.specific_class)

    def test_page_delete_notlive_post(self):
        # Same as above, but this makes sure the page_unpublished signal is not fired
        # when if the page is not live when it is deleted

        # Unpublish the page
        self.child_page.live = False
        self.child_page.save()

        # Connect a mock signal handler to page_unpublished signal
        mock_handler = mock.MagicMock()
        page_unpublished.connect(mock_handler)

        # Post
        response = self.client.post(reverse('wagtailadmin_pages:delete', args=(self.child_page.id, )))

        # Should be redirected to explorer page
        self.assertRedirects(response, reverse('wagtailadmin_explore', args=(self.root_page.id, )))

        # treebeard should report no consistency problems with the tree
        self.assertFalse(any(Page.find_problems()), 'treebeard found consistency problems')

        # Check that the page is gone
        self.assertEqual(Page.objects.filter(path__startswith=self.root_page.path, slug='hello-world').count(), 0)

        # Check that the page_unpublished signal was not fired
        self.assertEqual(mock_handler.call_count, 0)

    def test_subpage_deletion(self):
        # Connect mock signal handlers to page_unpublished, pre_delete and post_delete signals
        unpublish_signals_received = []
        pre_delete_signals_received = []
        post_delete_signals_received = []

        def page_unpublished_handler(sender, instance, **kwargs):
            unpublish_signals_received.append((sender, instance.id))

        def pre_delete_handler(sender, instance, **kwargs):
            pre_delete_signals_received.append((sender, instance.id))

        def post_delete_handler(sender, instance, **kwargs):
            post_delete_signals_received.append((sender, instance.id))

        page_unpublished.connect(page_unpublished_handler)
        pre_delete.connect(pre_delete_handler)
        post_delete.connect(post_delete_handler)

        # Post
        response = self.client.post(reverse('wagtailadmin_pages:delete', args=(self.child_index.id, )))

        # Should be redirected to explorer page
        self.assertRedirects(response, reverse('wagtailadmin_explore', args=(self.root_page.id, )))

        # treebeard should report no consistency problems with the tree
        self.assertFalse(any(Page.find_problems()), 'treebeard found consistency problems')

        # Check that the page is gone
        self.assertFalse(StandardIndex.objects.filter(id=self.child_index.id).exists())
        self.assertFalse(Page.objects.filter(id=self.child_index.id).exists())

        # Check that the subpage is also gone
        self.assertFalse(StandardChild.objects.filter(id=self.grandchild_page.id).exists())
        self.assertFalse(Page.objects.filter(id=self.grandchild_page.id).exists())

        # Check that the signals were fired for both pages
        self.assertIn((StandardIndex, self.child_index.id), unpublish_signals_received)
        self.assertIn((StandardChild, self.grandchild_page.id), unpublish_signals_received)

        self.assertIn((StandardIndex, self.child_index.id), pre_delete_signals_received)
        self.assertIn((StandardChild, self.grandchild_page.id), pre_delete_signals_received)

        self.assertIn((StandardIndex, self.child_index.id), post_delete_signals_received)
        self.assertIn((StandardChild, self.grandchild_page.id), post_delete_signals_received)

    def test_before_delete_page_hook(self):
        def hook_func(request, page):
            self.assertIsInstance(request, HttpRequest)
            self.assertEqual(page.id, self.child_page.id)

            return HttpResponse("Overridden!")

        with self.register_hook('before_delete_page', hook_func):
            response = self.client.get(reverse('wagtailadmin_pages:delete', args=(self.child_page.id, )))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")

    def test_before_delete_page_hook_post(self):
        def hook_func(request, page):
            self.assertIsInstance(request, HttpRequest)
            self.assertEqual(page.id, self.child_page.id)

            return HttpResponse("Overridden!")

        with self.register_hook('before_delete_page', hook_func):
            response = self.client.post(reverse('wagtailadmin_pages:delete', args=(self.child_page.id, )))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")

        # page should not be deleted
        self.assertTrue(Page.objects.filter(id=self.child_page.id).exists())

    def test_after_delete_page_hook(self):
        def hook_func(request, page):
            self.assertIsInstance(request, HttpRequest)
            self.assertEqual(page.id, self.child_page.id)

            return HttpResponse("Overridden!")

        with self.register_hook('after_delete_page', hook_func):
            response = self.client.post(reverse('wagtailadmin_pages:delete', args=(self.child_page.id, )))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")

        # page should be deleted
        self.assertFalse(Page.objects.filter(id=self.child_page.id).exists())
