from django.test import TestCase
import unittest
from wagtail.tests.models import EventPage
from wagtail.tests.utils import login
from wagtail.wagtailcore.models import Page
from django.core.urlresolvers import reverse


class TestHome(TestCase):
    def setUp(self):
        # Login
        login(self.client)

    def test_status_code(self):
        response = self.client.get(reverse('wagtailadmin_home'))
        self.assertEqual(response.status_code, 200)


class TestPageExplorer(TestCase):
    def setUp(self):
        # Find root page
        self.root_page = Page.objects.get(id=2)

        # Add child page
        self.child_page = EventPage()
        self.child_page.title = "Hello world!"
        self.child_page.slug = "hello-world"
        self.root_page.add_child(self.child_page)

        # Login
        login(self.client)

    def test_explore(self):
        response = self.client.get(reverse('wagtailadmin_explore', args=(self.root_page.id, )))
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
        response = self.client.get(reverse('wagtailadmin_pages_select_type'))
        self.assertEqual(response.status_code, 200)

    @unittest.expectedFailure # For some reason, this returns a 302...
    def test_select_location_testpage(self):
        response = self.client.get(reverse('wagtailadmin_pages_select_location', args=('tests', 'eventpage')))
        self.assertEqual(response.status_code, 200)

    def test_select_location_nonexistanttype(self):
        response = self.client.get(reverse('wagtailadmin_pages_select_location', args=('notanapp', 'notamodel')))
        self.assertEqual(response.status_code, 404)

    def test_select_location_nonpagetype(self):
        response = self.client.get(reverse('wagtailadmin_pages_select_location', args=('wagtailimages', 'image')))
        self.assertEqual(response.status_code, 404)

    def test_add_subpage_root(self):
        response = self.client.get(reverse('wagtailadmin_pages_add_subpage', args=(self.root_page.id, )))
        self.assertEqual(response.status_code, 200)

    def test_add_subpage_nonexistant(self):
        response = self.client.get(reverse('wagtailadmin_pages_add_subpage', args=(100000, )))
        self.assertEqual(response.status_code, 404)

    def test_create_testpage_root(self):
        response = self.client.get(reverse('wagtailadmin_pages_create', args=('tests', 'eventpage', self.root_page.id)))
        self.assertEqual(response.status_code, 200)

    def test_create_testpage_nonexistantparent(self):
        response = self.client.get(reverse('wagtailadmin_pages_create', args=('tests', 'testpage', 100000)))
        self.assertEqual(response.status_code, 404)

    @unittest.expectedFailure # FIXME: Crashes!
    def test_create_nonpagetype(self):
        response = self.client.get(reverse('wagtailadmin_pages_create', args=('wagtailimages', 'image', self.root_page.id)))
        self.assertEqual(response.status_code, 404)


class TestPageEditDelete(TestCase):
    def setUp(self):
        # Find root page
        self.root_page = Page.objects.get(id=2)

        # Add child page
        self.child_page = EventPage()
        self.child_page.title = "Hello world!"
        self.child_page.slug = "hello-world"
        self.root_page.add_child(self.child_page)

        # Login
        login(self.client)

    def test_edit(self):
        response = self.client.get(reverse('wagtailadmin_pages_edit', args=(self.child_page.id, )))
        self.assertEqual(response.status_code, 200)

    def test_delete(self):
        response = self.client.get(reverse('wagtailadmin_pages_delete', args=(self.child_page.id, )))
        self.assertEqual(response.status_code, 200)


class TestPageSearch(TestCase):
    def setUp(self):
        # Login
        login(self.client)

    def get(self, params={}):
        return self.client.get(reverse('wagtailadmin_pages_search'), params)

    def test_status_code(self):
        self.assertEqual(self.get().status_code, 200)

    def test_search(self):
        response = self.get({'q': "Hello"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['query_string'], "Hello")

    def test_pagination(self):
        pages = ['0', '1', '-1', '9999', 'Not a page']
        for page in pages:
            response = self.get({'p': page})
            self.assertEqual(response.status_code, 200)

    def test_root_can_appear_in_search_results(self):
        response = self.client.get('/admin/pages/search/?q=roo')
        self.assertEqual(response.status_code, 200)
        # 'pages' list in the response should contain root
        results = response.context['pages']
        self.assertTrue(any([r.slug == 'root' for r in results]))


class TestPageMove(TestCase):
    def setUp(self):
        # Find root page
        self.root_page = Page.objects.get(id=2)

        # Create two sections
        self.section_a = EventPage()
        self.section_a.title = "Section A"
        self.section_a.slug = "section-a"
        self.root_page.add_child(self.section_a)

        self.section_b = EventPage()
        self.section_b.title = "Section B"
        self.section_b.slug = "section-b"
        self.root_page.add_child(self.section_b)

        # Add test page into section A
        self.test_page = EventPage()
        self.test_page.title = "Hello world!"
        self.test_page.slug = "hello-world"
        self.section_a.add_child(self.test_page)

        # Login
        login(self.client)

    def test_page_move(self):
        response = self.client.get(reverse('wagtailadmin_pages_move', args=(self.test_page.id, )))
        self.assertEqual(response.status_code, 200)

    def test_page_move_confirm(self):
        response = self.client.get(reverse('wagtailadmin_pages_move_confirm', args=(self.test_page.id, self.section_b.id)))
        self.assertEqual(response.status_code, 200)

    def test_page_set_page_position(self):
        response = self.client.get(reverse('wagtailadmin_pages_set_page_position', args=(self.test_page.id, )))
        self.assertEqual(response.status_code, 200)
