from django.test import TestCase
from django.core.urlresolvers import reverse
from django.core import mail

from wagtail.tests.utils import WagtailTestUtils
from wagtail.tests.models import EventPage, EventPageRelatedLink
from wagtail.wagtailcore.models import Page
from wagtail.wagtailadmin.tasks import send_email_task
from wagtail.wagtaildocs.models import Document


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


class TestUsageCount(TestCase):
    fixtures = ['wagtail/tests/fixtures/test.json']

    def test_unused_document_usage_count(self):
        doc = Document.objects.get(id=1)
        self.assertEqual(doc.usage_count, 0)

    def test_used_document_usage_count(self):
        doc = Document.objects.get(id=1)
        page = EventPage.objects.get(id=4)
        event_page_related_link = EventPageRelatedLink()
        event_page_related_link.page = page
        event_page_related_link.link_document = doc
        event_page_related_link.save()
        self.assertEqual(doc.usage_count, 1)
