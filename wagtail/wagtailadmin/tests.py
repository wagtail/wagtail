from django.test import TestCase
import unittest
from wagtail.tests.models import TestPage
from wagtail.tests.utils import login, get_host
from wagtail.wagtailcore.models import Page
from django.core.urlresolvers import reverse


class TestPageExplorer(TestCase):
    def setUp(self):
        # Find root page
        self.root_page = Page.objects.get(id=2)

        # Add child page
        self.child_page = TestPage()
        self.child_page.title = "Hello world!"
        self.child_page.slug = "hello-world"
        self.root_page.add_child(self.child_page)

        # Login
        login(self.client)

    def test_explore(self):
        response = self.client.get(reverse('wagtailadmin_explore', args=(self.root_page.id, )), HTTP_HOST=get_host())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.root_page, response.context['parent_page'])
        self.assertTrue(response.context['pages'].filter(id=self.child_page.id).exists())


class TestPageCreation(TestCase):
    def setUp(self):
        # Find root page
        self.root_page = Page.objects.get(id=2)

        # Login
        login(self.client)

    def test_select_type(self):
        response = self.client.get(reverse('wagtailadmin_pages_select_type'), HTTP_HOST=get_host())
        self.assertEqual(response.status_code, 200)

    @unittest.expectedFailure # For some reason, this returns a 302...
    def test_select_location_testpage(self):
        response = self.client.get(reverse('wagtailadmin_pages_select_location', args=('tests', 'testpage')), HTTP_HOST=get_host())
        self.assertEqual(response.status_code, 200)

    def test_select_location_nonexistanttype(self):
        response = self.client.get(reverse('wagtailadmin_pages_select_location', args=('notanapp', 'notamodel')), HTTP_HOST=get_host())
        self.assertEqual(response.status_code, 404)

    def test_select_location_nonpagetype(self):
        response = self.client.get(reverse('wagtailadmin_pages_select_location', args=('wagtailimages', 'image')), HTTP_HOST=get_host())
        self.assertEqual(response.status_code, 404)

    def test_add_subpage_root(self):
        response = self.client.get(reverse('wagtailadmin_pages_add_subpage', args=(self.root_page.id, )), HTTP_HOST=get_host())
        self.assertEqual(response.status_code, 200)

    def test_add_subpage_nonexistant(self):
        response = self.client.get(reverse('wagtailadmin_pages_add_subpage', args=(100000, )), HTTP_HOST=get_host())
        self.assertEqual(response.status_code, 404)

    def test_create_testpage_root(self):
        response = self.client.get(reverse('wagtailadmin_pages_create', args=('tests', 'testpage', self.root_page.id)), HTTP_HOST=get_host())
        self.assertEqual(response.status_code, 200)

    def test_create_testpage_nonexistantparent(self):
        response = self.client.get(reverse('wagtailadmin_pages_create', args=('tests', 'testpage', 100000)), HTTP_HOST=get_host())
        self.assertEqual(response.status_code, 404)

    @unittest.expectedFailure # FIXME: Crashes!
    def test_create_nonpagetype(self):
        response = self.client.get(reverse('wagtailadmin_pages_create', args=('wagtailimages', 'image', self.root_page.id)), HTTP_HOST=get_host())
        self.assertEqual(response.status_code, 404)


class TestPageEditDelete(TestCase):
    def setUp(self):
        # Find root page
        self.root_page = Page.objects.get(id=2)

        # Add child page
        self.child_page = TestPage()
        self.child_page.title = "Hello world!"
        self.child_page.slug = "hello-world"
        self.root_page.add_child(self.child_page)

        # Login
        login(self.client)

    def test_edit(self):
         response = self.client.get(reverse('wagtailadmin_pages_edit', args=(self.child_page.id, )), HTTP_HOST=get_host())
         self.assertEqual(response.status_code, 200)

    def test_delete(self):
         response = self.client.get(reverse('wagtailadmin_pages_delete', args=(self.child_page.id, )), HTTP_HOST=get_host())
         self.assertEqual(response.status_code, 200)
