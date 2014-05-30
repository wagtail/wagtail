from django.test import TestCase
from wagtail.tests.models import SimplePage, EventPage
from wagtail.tests.utils import login, unittest
from wagtail.wagtailcore.models import Page
from django.core.urlresolvers import reverse


class TestHome(TestCase):
    def setUp(self):
        # Login
        login(self.client)

    def test_status_code(self):
        response = self.client.get(reverse('wagtailadmin_home'))
        self.assertEqual(response.status_code, 200)


class TestEditorHooks(TestCase):
    def setUp(self):
        self.homepage = Page.objects.get(id=2)
        login(self.client)

    def test_editor_css_and_js_hooks_on_add(self):
        response = self.client.get(reverse('wagtailadmin_pages_create', args=('tests', 'simplepage', self.homepage.id)))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<link rel="stylesheet" href="/path/to/my/custom.css">')
        self.assertContains(response, '<script src="/path/to/my/custom.js"></script>')

    def test_editor_css_and_js_hooks_on_edit(self):
        response = self.client.get(reverse('wagtailadmin_pages_edit', args=(self.homepage.id, )))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<link rel="stylesheet" href="/path/to/my/custom.css">')
        self.assertContains(response, '<script src="/path/to/my/custom.js"></script>')
