from django.contrib.auth.models import Permission
from django.contrib.messages import constants as message_constants
from django.http import HttpRequest, HttpResponse
from django.test import TestCase
from django.urls import reverse

from wagtail.core.models import Page
from wagtail.tests.testapp.models import SimplePage
from wagtail.tests.utils import WagtailTestUtils


class TestPageMove(TestCase, WagtailTestUtils):
    def setUp(self):
        # Find root page
        self.root_page = Page.objects.get(id=2)

        # Create three sections
        self.section_a = SimplePage(title="Section A", slug="section-a", content="hello")
        self.root_page.add_child(instance=self.section_a)

        self.section_b = SimplePage(title="Section B", slug="section-b", content="hello")
        self.root_page.add_child(instance=self.section_b)

        self.section_c = SimplePage(title="Section C", slug="section-c", content="hello")
        self.root_page.add_child(instance=self.section_c)

        # Add test page A into section A
        self.test_page_a = SimplePage(title="Hello world!", slug="hello-world", content="hello")
        self.section_a.add_child(instance=self.test_page_a)

        # Add test page B into section C
        self.test_page_b = SimplePage(title="Hello world!", slug="hello-world", content="hello")
        self.section_c.add_child(instance=self.test_page_b)

        # Login
        self.user = self.login()

    def test_page_move(self):
        response = self.client.get(reverse('wagtailadmin_pages:move', args=(self.test_page_a.id, )))
        self.assertEqual(response.status_code, 200)

    def test_page_move_bad_permissions(self):
        # Remove privileges from user
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(content_type__app_label='wagtailadmin', codename='access_admin')
        )
        self.user.save()

        # Get move page
        response = self.client.get(reverse('wagtailadmin_pages:move', args=(self.test_page_a.id, )))

        # Check that the user received a 403 response
        self.assertEqual(response.status_code, 403)

    def test_page_move_confirm(self):
        response = self.client.get(
            reverse('wagtailadmin_pages:move_confirm', args=(self.test_page_a.id, self.section_b.id))
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.get(
            reverse('wagtailadmin_pages:move_confirm', args=(self.test_page_b.id, self.section_a.id))
        )
        # Duplicate slugs triggers a redirect with an error message.
        self.assertEqual(response.status_code, 302)

        response = self.client.get(reverse('wagtailadmin_home'))
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].level, message_constants.ERROR)
        # Slug should be in error message.
        self.assertIn("{}".format(self.test_page_b.slug), messages[0].message)

    def test_page_set_page_position(self):
        response = self.client.get(reverse('wagtailadmin_pages:set_page_position', args=(self.test_page_a.id, )))
        self.assertEqual(response.status_code, 200)

    def test_before_move_page_hook(self):
        def hook_func(request, page, destination):
            self.assertIsInstance(request, HttpRequest)
            self.assertIsInstance(page.specific, SimplePage)
            self.assertIsInstance(destination.specific, SimplePage)

            return HttpResponse("Overridden!")

        with self.register_hook('before_move_page', hook_func):
            response = self.client.get(reverse('wagtailadmin_pages:move_confirm', args=(self.test_page_a.id, self.section_b.id)))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")

    def test_before_move_page_hook_post(self):
        def hook_func(request, page, destination):
            self.assertIsInstance(request, HttpRequest)
            self.assertIsInstance(page.specific, SimplePage)
            self.assertIsInstance(destination.specific, SimplePage)

            return HttpResponse("Overridden!")

        with self.register_hook('before_move_page', hook_func):
            response = self.client.post(reverse('wagtailadmin_pages:move_confirm', args=(self.test_page_a.id, self.section_b.id)))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")

        # page should not be moved
        self.assertEqual(
            Page.objects.get(id=self.test_page_a.id).get_parent().id,
            self.section_a.id
        )

    def test_after_move_page_hook(self):
        def hook_func(request, page):
            self.assertIsInstance(request, HttpRequest)
            self.assertIsInstance(page.specific, SimplePage)

            return HttpResponse("Overridden!")

        with self.register_hook('after_move_page', hook_func):
            response = self.client.post(reverse('wagtailadmin_pages:move_confirm', args=(self.test_page_a.id, self.section_b.id)))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")

        # page should be moved
        self.assertEqual(
            Page.objects.get(id=self.test_page_a.id).get_parent().id,
            self.section_b.id
        )
