from unittest import mock

from django.contrib.auth.models import Permission
from django.http import HttpRequest, HttpResponse
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from wagtail.core.models import Page
from wagtail.core.signals import page_unpublished
from wagtail.tests.testapp.models import SimplePage
from wagtail.tests.utils import WagtailTestUtils


class TestPageUnpublish(TestCase, WagtailTestUtils):
    def setUp(self):
        self.user = self.login()

        # Create a page to unpublish
        self.root_page = Page.objects.get(id=2)
        self.page = SimplePage(
            title="Hello world!",
            slug='hello-world',
            content="hello",
            live=True,
        )
        self.root_page.add_child(instance=self.page)

    def test_unpublish_view(self):
        """
        This tests that the unpublish view responds with an unpublish confirm page
        """
        # Get unpublish page
        response = self.client.get(reverse('wagtailadmin_pages:unpublish', args=(self.page.id, )))

        # Check that the user received an unpublish confirm page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/pages/confirm_unpublish.html')

    def test_unpublish_view_invalid_page_id(self):
        """
        This tests that the unpublish view returns an error if the page id is invalid
        """
        # Get unpublish page
        response = self.client.get(reverse('wagtailadmin_pages:unpublish', args=(12345, )))

        # Check that the user received a 404 response
        self.assertEqual(response.status_code, 404)

    def test_unpublish_view_bad_permissions(self):
        """
        This tests that the unpublish view doesn't allow users without unpublish permissions
        """
        # Remove privileges from user
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(content_type__app_label='wagtailadmin', codename='access_admin')
        )
        self.user.save()

        # Get unpublish page
        response = self.client.get(reverse('wagtailadmin_pages:unpublish', args=(self.page.id, )))

        # Check that the user received a 302 redirected response
        self.assertEqual(response.status_code, 302)

    def test_unpublish_view_post(self):
        """
        This posts to the unpublish view and checks that the page was unpublished
        """
        # Connect a mock signal handler to page_unpublished signal
        mock_handler = mock.MagicMock()
        page_unpublished.connect(mock_handler)

        # Post to the unpublish page
        response = self.client.post(reverse('wagtailadmin_pages:unpublish', args=(self.page.id, )))

        # Should be redirected to explorer page
        self.assertRedirects(response, reverse('wagtailadmin_explore', args=(self.root_page.id, )))

        # Check that the page was unpublished
        self.assertFalse(SimplePage.objects.get(id=self.page.id).live)

        # Check that the page_unpublished signal was fired
        self.assertEqual(mock_handler.call_count, 1)
        mock_call = mock_handler.mock_calls[0][2]

        self.assertEqual(mock_call['sender'], self.page.specific_class)
        self.assertEqual(mock_call['instance'], self.page)
        self.assertIsInstance(mock_call['instance'], self.page.specific_class)

    def test_after_unpublish_page(self):
        def hook_func(request, page):
            self.assertIsInstance(request, HttpRequest)
            self.assertEqual(page.id, self.page.id)

            return HttpResponse("Overridden!")

        with self.register_hook('after_unpublish_page', hook_func):
            post_data = {}
            response = self.client.post(
                reverse('wagtailadmin_pages:unpublish', args=(self.page.id, )), post_data
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")

        self.page.refresh_from_db()
        self.assertEqual(self.page.status_string, _("draft"))

    def test_before_unpublish_page(self):
        def hook_func(request, page):
            self.assertIsInstance(request, HttpRequest)
            self.assertEqual(page.id, self.page.id)

            return HttpResponse("Overridden!")

        with self.register_hook('before_unpublish_page', hook_func):
            post_data = {}
            response = self.client.post(
                reverse('wagtailadmin_pages:unpublish', args=(self.page.id, )), post_data
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")

        # The hook response is served before unpublish is called.
        self.page.refresh_from_db()
        self.assertEqual(self.page.status_string, _("live"))

    def test_unpublish_descendants_view(self):
        """
        This tests that the unpublish view responds with an unpublish confirm page that does not contain the form field 'include_descendants'
        """
        # Get unpublish page
        response = self.client.get(reverse('wagtailadmin_pages:unpublish', args=(self.page.id, )))

        # Check that the user received an unpublish confirm page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/pages/confirm_unpublish.html')
        # Check the form does not contain the checkbox field include_descendants
        self.assertNotContains(response, '<input id="id_include_descendants" name="include_descendants" type="checkbox">')


class TestPageUnpublishIncludingDescendants(TestCase, WagtailTestUtils):
    def setUp(self):
        self.user = self.login()
        # Find root page
        self.root_page = Page.objects.get(id=2)

        # Create a page to unpublish
        self.test_page = self.root_page.add_child(instance=SimplePage(
            title="Hello world!",
            slug='hello-world',
            content="hello",
            live=True,
            has_unpublished_changes=False,
        ))

        # Create a couple of child pages
        self.test_child_page = self.test_page.add_child(instance=SimplePage(
            title="Child page",
            slug='child-page',
            content="hello",
            live=True,
            has_unpublished_changes=True,
        ))

        self.test_another_child_page = self.test_page.add_child(instance=SimplePage(
            title="Another Child page",
            slug='another-child-page',
            content="hello",
            live=True,
            has_unpublished_changes=True,
        ))

    def test_unpublish_descendants_view(self):
        """
        This tests that the unpublish view responds with an unpublish confirm page that contains the form field 'include_descendants'
        """
        # Get unpublish page
        response = self.client.get(reverse('wagtailadmin_pages:unpublish', args=(self.test_page.id, )))

        # Check that the user received an unpublish confirm page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/pages/confirm_unpublish.html')
        # Check the form contains the checkbox field include_descendants
        self.assertContains(response, '<input id="id_include_descendants" name="include_descendants" type="checkbox">')

    def test_unpublish_include_children_view_post(self):
        """
        This posts to the unpublish view and checks that the page and its descendants were unpublished
        """
        # Post to the unpublish page
        response = self.client.post(reverse('wagtailadmin_pages:unpublish', args=(self.test_page.id, )), {'include_descendants': 'on'})

        # Should be redirected to explorer page
        self.assertRedirects(response, reverse('wagtailadmin_explore', args=(self.root_page.id, )))

        # Check that the page was unpublished
        self.assertFalse(SimplePage.objects.get(id=self.test_page.id).live)

        # Check that the descendant pages were unpublished as well
        self.assertFalse(SimplePage.objects.get(id=self.test_child_page.id).live)
        self.assertFalse(SimplePage.objects.get(id=self.test_another_child_page.id).live)

    def test_unpublish_not_include_children_view_post(self):
        """
        This posts to the unpublish view and checks that the page was unpublished but its descendants were not
        """
        # Post to the unpublish page
        response = self.client.post(reverse('wagtailadmin_pages:unpublish', args=(self.test_page.id, )), {})

        # Should be redirected to explorer page
        self.assertRedirects(response, reverse('wagtailadmin_explore', args=(self.root_page.id, )))

        # Check that the page was unpublished
        self.assertFalse(SimplePage.objects.get(id=self.test_page.id).live)

        # Check that the descendant pages were not unpublished
        self.assertTrue(SimplePage.objects.get(id=self.test_child_page.id).live)
        self.assertTrue(SimplePage.objects.get(id=self.test_another_child_page.id).live)
