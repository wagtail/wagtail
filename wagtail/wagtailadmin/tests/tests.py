from django.test import TestCase
from wagtail.tests.models import SimplePage, EventPage
from wagtail.tests.utils import unittest, WagtailTestUtils
from wagtail.wagtailcore.models import Page
from wagtail.wagtailadmin.tasks import send_email_task
from django.core.urlresolvers import reverse
from django.core import mail


class TestHome(TestCase, WagtailTestUtils):
    def setUp(self):
        # Login
        self.login()

    def test_simple(self):
        response = self.client.get(reverse('wagtailadmin_home'))
        self.assertEqual(response.status_code, 200)


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
