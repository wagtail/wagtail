from django.test import TestCase
from wagtail.tests.models import SimplePage, EventPage
from wagtail.tests.utils import login, unittest
from wagtail.wagtailcore.models import Page
from wagtail.wagtailadmin.tasks import send_email_task
from django.core.urlresolvers import reverse
from django.core import mail


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


class TestSendEmailTask(TestCase):
    def test_send_email(self):
        send_email_task("Test subject", "Test content", ["nobody@email.com"], "test@email.com")

        # Check that the email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Test subject")
        self.assertEqual(mail.outbox[0].body, "Test content")
        self.assertEqual(mail.outbox[0].to, ["nobody@email.com"])


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


class TestChooserBrowseChild(TestCase):
    def setUp(self):
        self.root_page = Page.objects.get(id=2)

        # Add child page
        self.child_page = SimplePage()
        self.child_page.title = "foobarbaz"
        self.child_page.slug = "foobarbaz"
        self.root_page.add_child(instance=self.child_page)

        login(self.client)

    def get(self, params={}):
        return self.client.get(reverse('wagtailadmin_choose_page_child',
                                       args=(self.root_page.id,)), params)

    def get_invalid(self, params={}):
        return self.client.get(reverse('wagtailadmin_choose_page_child',
                                       args=(9999999,)), params)

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
        self.assertEqual(self.get_invalid().status_code, 404)


class TestChooserExternalLink(TestCase):
    def setUp(self):
        login(self.client)

    def get(self, params={}):
        return self.client.get(reverse('wagtailadmin_choose_page_external_link'), params)

    def post(self, post_data={}):
        return self.client.post(reverse('wagtailadmin_choose_page_external_link'), post_data)

    def test_status_code(self):
        self.assertEqual(self.get().status_code, 200)

    def test_get_with_param(self):
        self.assertEqual(self.get({'prompt_for_link_text': 'foo'}).status_code, 200)

    def test_create_link(self):
        request = self.post({'url': 'http://www.example.com'})
        self.assertContains(request, "'url': 'http://www.example.com/',")
        self.assertContains(request, "'title': 'http://www.example.com/'")


class TestChooserEmailLink(TestCase):
    def setUp(self):
        login(self.client)

    def get(self, params={}):
        return self.client.get(reverse('wagtailadmin_choose_page_email_link'), params)

    def post(self, post_data={}):
        return self.client.post(reverse('wagtailadmin_choose_page_email_link'), post_data)

    def test_status_code(self):
        self.assertEqual(self.get().status_code, 200)

    def test_get_with_param(self):
        self.assertEqual(self.get({'prompt_for_link_text': 'foo'}).status_code, 200)

    def test_create_link(self):
        request = self.post({'email_address': 'example@example.com'})
        self.assertContains(request, "'url': 'mailto:example@example.com',")
        self.assertContains(request, "'title': 'example@example.com'")
