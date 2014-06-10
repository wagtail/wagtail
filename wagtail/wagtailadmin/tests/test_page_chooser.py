from django.test import TestCase
from django.core.urlresolvers import reverse

from wagtail.wagtailcore.models import Page
from wagtail.tests.models import SimplePage
from wagtail.tests.utils import login

class TestChooserBrowse(TestCase):
    def setUp(self):
        self.root_page = Page.objects.get(id=2)

        # Add child page
        self.child_page = SimplePage()
        self.child_page.title = "foobarbaz"
        self.child_page.slug = "foobarbaz"
        self.root_page.add_child(instance=self.child_page)

        login(self.client)

    def get(self, params={}):
        return self.client.get(reverse('wagtailadmin_choose_page'), params)

    def test_status_code(self):
        self.assertEqual(self.get().status_code, 200)

    def test_search(self):
        response = self.get({'q': "foobarbaz"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "There is one match")
        self.assertContains(response, "foobarbaz")

    def test_search_no_results(self):
        response = self.get({'q': "quux"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "There are 0 matches")

    def test_get_invalid(self):
        response = self.get({'page_type': 'foo.bar'})
        self.assertEqual(response.status_code, 404)
