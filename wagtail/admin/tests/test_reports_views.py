from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from wagtail.core.models import Page
from wagtail.tests.utils import WagtailTestUtils


class TestLockedPagesView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.user = self.login()

    def get(self, params={}):
        return self.client.get(reverse('wagtailadmin_reports:locked_pages'), params)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/reports/locked_pages.html')

        # Initially there should be no locked pages
        self.assertContains(response, "No locked pages found.")

        self.page = Page.objects.first()
        self.page.locked = True
        self.page.locked_by = self.user
        self.page.locked_at = timezone.now()
        self.page.save()

        # Now the listing should contain our locked page
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/reports/locked_pages.html')
        self.assertNotContains(response, "No locked pages found.")
        self.assertContains(response, self.page.title)
