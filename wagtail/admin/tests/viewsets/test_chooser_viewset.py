import json

from django.test import TestCase

from wagtail.admin import widgets
from wagtail.test.testapp.models import Advert
from wagtail.test.testapp.views import AdvertChooserWidget
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

    def test_adapt_widget_with_linked_fields(self):
        widget = AdvertChooserWidget(linked_fields={"url": "#id_cool_url"})

        js_args = widgets.BaseChooserAdapter().js_args(widget)
        self.assertInHTML(
            """<input id="__ID__" name="__NAME__" type="hidden" />""", js_args[0]
        )
        self.assertIn("Choose", js_args[0])
        self.assertEqual(js_args[1], "__ID__")
        self.assertEqual(
            js_args[2],
            {
                "modalUrl": "/admin/animated_advert_chooser/",
                "linkedFields": {"url": "#id_cool_url"},
            },
        )
