import json

from django.test import TestCase

from wagtail.test.testapp.models import Advert
from wagtail.test.utils.wagtail_tests import WagtailTestUtils


class TestChooserViewSetWithFilteredObjects(WagtailTestUtils, TestCase):
    def setUp(self):
        self.user = self.login()

        Advert.objects.create(text="Head On, apply directly to the forehead")

        advert2 = Advert.objects.create(
            url="https://quiznos.com", text="We like the subs"
        )
        advert2.tags.add("animated")

    def test_get(self):
        response = self.client.get("/admin/animated_advert_chooser/")
        response_html = json.loads(response.content)["html"]
        self.assertIn("We like the subs", response_html)
        self.assertNotIn("Head On, apply directly to the forehead", response_html)

    def test_filter_by_url(self):
        response = self.client.get(
            "/admin/animated_advert_chooser/", {"url": "https://quiznos.com"}
        )
        response_html = json.loads(response.content)["html"]
        self.assertIn("We like the subs", response_html)

        response = self.client.get(
            "/admin/animated_advert_chooser/", {"url": "https://subway.com"}
        )
        response_html = json.loads(response.content)["html"]
        self.assertNotIn("We like the subs", response_html)
