from django.test import TestCase

from wagtail.test.utils import WagtailTestUtils
from wagtail.test.utils.template_tests import AdminTemplateTestUtils


class TestCustomListing(AdminTemplateTestUtils, WagtailTestUtils, TestCase):
    fixtures = ["test.json"]

    def test_get(self):
        self.login()
        response = self.client.get("/admin/event_pages/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/pages/index.html")
        self.assertContains(response, "Event pages")
        self.assertContains(response, "Christmas")
        self.assertContains(response, "Saint Patrick")
        self.assertNotContains(response, "Welcome to the Wagtail test site!")
        self.assertBreadcrumbsItemsRendered(
            [{"url": "", "label": "Event pages"}],
            response.content,
        )
        soup = self.get_soup(response.content)
        breadcrumbs_icon = soup.select_one(".w-breadcrumbs__icon")
        self.assertIsNotNone(breadcrumbs_icon)
        use = breadcrumbs_icon.select_one("use")
        self.assertIsNotNone(use)
        self.assertEqual(use["href"], "#icon-calendar")

    def test_filter(self):
        self.login()
        response = self.client.get("/admin/event_pages/", {"audience": "private"})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/pages/index.html")
        self.assertContains(response, "Event pages")
        self.assertNotContains(response, "Christmas")
        self.assertContains(response, "Saint Patrick")
