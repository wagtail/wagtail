from django.test import TestCase
from django.urls import reverse

from wagtail.test.utils.wagtail_tests import WagtailTestUtils


class TestModelViewSetGroup(WagtailTestUtils, TestCase):
    def setUp(self):
        self.user = self.login()

    def test_menu_items(self):
        response = self.client.get(reverse("wagtailadmin_home"))
        self.assertEqual(response.status_code, 200)
        # Menu label falls back to the title-cased app label
        self.assertContains(
            response,
            '"name": "tests", "label": "Tests", "icon_name": "folder-open-inverse"',
        )
        # Title-cased from verbose_name_plural
        self.assertContains(response, "Json Stream Models")
        self.assertContains(response, reverse("streammodel:index"))
        self.assertEqual(reverse("streammodel:index"), "/admin/streammodel/")
        # Set on class
        self.assertContains(response, "JSON MinMaxCount StreamModel")
        self.assertContains(response, reverse("minmaxcount_streammodel:index"))
        self.assertEqual(
            reverse("minmaxcount_streammodel:index"),
            "/admin/minmaxcount-streammodel/",
        )
        # Set on instance
        self.assertContains(response, "JSON BlockCounts StreamModel")
        self.assertContains(response, reverse("blockcounts_streammodel:index"))
        self.assertEqual(
            reverse("blockcounts_streammodel:index"),
            "/admin/blockcounts/streammodel/",
        )
