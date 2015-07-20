from django.test import TestCase, override_settings
from django.core.urlresolvers import reverse
from django.core import mail

from wagtail.tests.utils import WagtailTestUtils
from wagtail.wagtailcore.models import Page
from wagtail.wagtailadmin.utils import send_mail


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

    def test_never_cache_header(self):
        # This tests that wagtailadmins global cache settings have been applied correctly
        response = self.client.get(reverse('wagtailadmin_home'))

        self.assertIn('private', response['Cache-Control'])
        self.assertIn('no-cache', response['Cache-Control'])
        self.assertIn('no-store', response['Cache-Control'])
        self.assertIn('max-age=0', response['Cache-Control'])


class TestEditorHooks(TestCase, WagtailTestUtils):
    def setUp(self):
        self.homepage = Page.objects.get(id=2)
        self.login()

    def test_editor_css_and_js_hooks_on_add(self):
        response = self.client.get(reverse('wagtailadmin_pages:create', args=('tests', 'simplepage', self.homepage.id)))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<link rel="stylesheet" href="/path/to/my/custom.css">')
        self.assertContains(response, '<script src="/path/to/my/custom.js"></script>')

    def test_editor_css_and_js_hooks_on_edit(self):
        response = self.client.get(reverse('wagtailadmin_pages:edit', args=(self.homepage.id, )))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<link rel="stylesheet" href="/path/to/my/custom.css">')
        self.assertContains(response, '<script src="/path/to/my/custom.js"></script>')


class TestSendMail(TestCase):
    def test_send_email(self):
        send_mail("Test subject", "Test content", ["nobody@email.com"], "test@email.com")

        # Check that the email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Test subject")
        self.assertEqual(mail.outbox[0].body, "Test content")
        self.assertEqual(mail.outbox[0].to, ["nobody@email.com"])
        self.assertEqual(mail.outbox[0].from_email, "test@email.com")

    @override_settings(WAGTAILADMIN_NOTIFICATION_FROM_EMAIL='anothertest@email.com')
    def test_send_fallback_to_wagtailadmin_notification_from_email_setting(self):
        send_mail("Test subject", "Test content", ["nobody@email.com"])

        # Check that the email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Test subject")
        self.assertEqual(mail.outbox[0].body, "Test content")
        self.assertEqual(mail.outbox[0].to, ["nobody@email.com"])
        self.assertEqual(mail.outbox[0].from_email, "anothertest@email.com")

    @override_settings(DEFAULT_FROM_EMAIL='yetanothertest@email.com')
    def test_send_fallback_to_default_from_email_setting(self):
        send_mail("Test subject", "Test content", ["nobody@email.com"])

        # Check that the email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Test subject")
        self.assertEqual(mail.outbox[0].body, "Test content")
        self.assertEqual(mail.outbox[0].to, ["nobody@email.com"])
        self.assertEqual(mail.outbox[0].from_email, "yetanothertest@email.com")

    def test_send_default_from_email(self):
        send_mail("Test subject", "Test content", ["nobody@email.com"])

        # Check that the email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Test subject")
        self.assertEqual(mail.outbox[0].body, "Test content")
        self.assertEqual(mail.outbox[0].to, ["nobody@email.com"])
        self.assertEqual(mail.outbox[0].from_email, "webmaster@localhost")


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
