from django.test import TestCase

from wagtail.models import Page, Site
from wagtail.test.testapp.models import EventIndex


class AllowedHttpMethodsTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        site = Site.objects.select_related("root_page").get(is_default_site=True)
        cls.page = Page(title="Page", slug="page")
        site.root_page.add_child(instance=cls.page)
        cls.event_index_page = EventIndex(title="Event index", slug="event-index")
        site.root_page.add_child(instance=cls.event_index_page)

    def test_options_request_for_default_page(self):
        response = self.client.options(self.page.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Allow"], "DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT"
        )

    def test_options_request_for_restricted_page(self):
        response = self.client.options(self.event_index_page.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Allow"], "GET, OPTIONS")

    def test_invalid_request_method_for_restricted_page(self):
        response = self.client.post(self.event_index_page.url)
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response["Allow"], "GET, OPTIONS")
