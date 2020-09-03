from django.test import TestCase
from django.urls import reverse
from django.utils.http import urlencode

from wagtail.tests.testapp.models import EventPage
from wagtail.tests.utils import WagtailTestUtils


class TestContentTypeUse(TestCase, WagtailTestUtils):
    fixtures = ['test.json']

    def setUp(self):
        self.user = self.login()
        self.christmas_page = EventPage.objects.get(title="Christmas")

    def test_content_type_use(self):
        # Get use of event page
        request_url = reverse('wagtailadmin_pages:type_use', args=('tests', 'eventpage'))
        response = self.client.get(request_url)

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/pages/content_type_use.html')
        self.assertContains(response, "Christmas")

        # Links to 'delete' etc should include a 'next' URL parameter pointing back here
        delete_url = (
            reverse('wagtailadmin_pages:delete', args=(self.christmas_page.id,))
            + '?' + urlencode({'next': request_url})
        )
        self.assertContains(response, delete_url)
