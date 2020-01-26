from django.test import TestCase
from django.urls import reverse

from wagtail.tests.utils import WagtailTestUtils


class TestContentTypeUse(TestCase, WagtailTestUtils):
    fixtures = ['test.json']

    def setUp(self):
        self.user = self.login()

    def test_content_type_use(self):
        # Get use of event page
        response = self.client.get(reverse('wagtailadmin_pages:type_use', args=('tests', 'eventpage')))

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/pages/content_type_use.html')
        self.assertContains(response, "Christmas")
