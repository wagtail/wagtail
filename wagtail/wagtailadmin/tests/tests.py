from django.test import TestCase
from django.core.urlresolvers import reverse
from django.core import mail

from wagtail.tests.utils import WagtailTestUtils
from wagtail.wagtailcore.models import Page
from wagtail.wagtailadmin.tasks import send_email_task


class TestHome(TestCase, WagtailTestUtils):
    def setUp(self):
        # Login
        self.login()

    def test_simple(self):
        response = self.client.get(reverse('wagtailadmin_home'))
        self.assertEqual(response.status_code, 200)

    def test_admin_menu(self):
        response = self.client.get(reverse('wagtailadmin_home'))
        self.assertEqual(response.status_code, 200)
        # check that media attached to menu items is correctly pulled in
        self.assertContains(response, '<script type="text/javascript" src="/static/wagtailadmin/js/explorer-menu.js"></script>')
        # check that custom menu items (including classname / attrs parameters) are pulled in
        self.assertContains(response, '<a href="http://www.tomroyal.com/teaandkittens/" class="icon icon-kitten" data-fluffy="yes">Kittens!</a>')

        # check that is_shown is respected on menu items
        response = self.client.get(reverse('wagtailadmin_home') + '?hide-kittens=true')
        self.assertNotContains(response, '<a href="http://www.tomroyal.com/teaandkittens/" class="icon icon-kitten" data-fluffy="yes">Kittens!</a>')


class TestEditorHooks(TestCase, WagtailTestUtils):
    def setUp(self):
        self.homepage = Page.objects.get(id=2)
        self.login()

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


class TestExplorerNavView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.homepage = Page.objects.get(id=2).specific
        self.login()

    def test_explorer_nav_view(self):
        response = self.client.get(reverse('wagtailadmin_explorer_nav'))

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed('wagtailadmin/shared/explorer_nav.html')
        self.assertEqual(response.context['nodes'][0][0], self.homepage)
