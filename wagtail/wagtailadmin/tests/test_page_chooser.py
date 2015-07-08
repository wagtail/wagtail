from django.test import TestCase
from django.core.urlresolvers import reverse

from wagtail.wagtailcore.models import Page
from wagtail.tests.testapp.models import SimplePage
from wagtail.tests.utils import WagtailTestUtils


class TestChooserBrowse(TestCase, WagtailTestUtils):
    def setUp(self):
        self.root_page = Page.objects.get(id=2)

        # Add child page
        self.child_page = SimplePage()
        self.child_page.title = "foobarbaz"
        self.child_page.slug = "foobarbaz"
        self.root_page.add_child(instance=self.child_page)

        self.login()

    def get(self, params={}):
        return self.client.get(reverse('wagtailadmin_choose_page'), params)

    def search(self, params={}):
        return self.client.get(reverse('wagtailadmin_choose_page_search'), params)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/chooser/browse.html')

    def test_search(self):
        response = self.search({'q': "foobarbaz"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "There is one match")
        self.assertContains(response, "foobarbaz")

    def test_search_no_results(self):
        response = self.search({'q': "quux"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "There are 0 matches")

    def test_get_invalid(self):
        response = self.search({'page_type': 'foo.bar'})
        self.assertEqual(response.status_code, 404)


class TestChooserBrowseChild(TestCase, WagtailTestUtils):
    def setUp(self):
        self.root_page = Page.objects.get(id=2)

        # Add child page
        self.child_page = SimplePage()
        self.child_page.title = "foobarbaz"
        self.child_page.slug = "foobarbaz"
        self.root_page.add_child(instance=self.child_page)

        self.login()

    def get(self, params={}):
        return self.client.get(reverse('wagtailadmin_choose_page_child',
                                       args=(self.root_page.id,)), params)

    def get_invalid(self, params={}):
        return self.client.get(reverse('wagtailadmin_choose_page_child',
                                       args=(9999999,)), params)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/chooser/browse.html')

    def test_get_invalid(self):
        self.assertEqual(self.get_invalid().status_code, 404)


class TestChooserExternalLink(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

    def get(self, params={}):
        return self.client.get(reverse('wagtailadmin_choose_page_external_link'), params)

    def post(self, post_data={}):
        return self.client.post(reverse('wagtailadmin_choose_page_external_link'), post_data)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/chooser/external_link.html')

    def test_get_with_param(self):
        self.assertEqual(self.get({'prompt_for_link_text': 'foo'}).status_code, 200)

    def test_create_link(self):
        response = self.post({'url': 'http://www.example.com/'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "'onload'")  # indicates success / post back to calling page
        self.assertContains(response, "'url': 'http://www.example.com/',")
        self.assertContains(response, "'title': 'http://www.example.com/'")

    def test_invalid_url(self):
        response = self.post({'url': 'ntp://www.example.com'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "'html'")  # indicates failure / show error message
        self.assertContains(response, "Enter a valid URL.")

    def test_allow_local_url(self):
        response = self.post({'url': '/admin/'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "'onload'")  # indicates success / post back to calling page
        self.assertContains(response, "'url': '/admin/',")
        self.assertContains(response, "'title': '/admin/'")


class TestChooserEmailLink(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

    def get(self, params={}):
        return self.client.get(reverse('wagtailadmin_choose_page_email_link'), params)

    def post(self, post_data={}):
        return self.client.post(reverse('wagtailadmin_choose_page_email_link'), post_data)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/chooser/email_link.html')

    def test_get_with_param(self):
        self.assertEqual(self.get({'prompt_for_link_text': 'foo'}).status_code, 200)

    def test_create_link(self):
        request = self.post({'email_address': 'example@example.com'})
        self.assertContains(request, "'url': 'mailto:example@example.com',")
        self.assertContains(request, "'title': 'example@example.com'")
