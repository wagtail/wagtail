from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from wagtail.test.utils.wagtail_tests import WagtailTestUtils


class TestBaseViewSet(WagtailTestUtils, TestCase):
    def setUp(self):
        self.user = self.login()

    def test_menu_items(self):
        response = self.client.get(reverse("wagtailadmin_home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Miscellaneous")
        self.assertContains(response, "The Calendar")
        self.assertContains(response, "The Greetings")

    def test_calendar_index_view(self):
        url = reverse("calendar:index")
        response = self.client.get(url)
        now = timezone.now()
        self.assertEqual(url, "/admin/calendar/")
        self.assertContains(response, f"{now.year} calendar")

    def test_calendar_month_view(self):
        url = reverse("calendar:month")
        response = self.client.get(url)
        now = timezone.now()
        self.assertEqual(url, "/admin/calendar/month/")
        self.assertContains(response, f"{now.year}/{now.month} calendar")

    def test_greetings_view(self):
        self.user.first_name = "Gordon"
        self.user.last_name = "Freeman"
        self.user.save()
        url = reverse("greetings:index")
        response = self.client.get(url)
        self.assertEqual(url, "/admin/greetingz/")
        self.assertContains(response, "Greetings")
        self.assertContains(response, "Welcome to this greetings page, Gordon Freeman!")
