import json

from django.test import TestCase, override_settings
from django.urls import reverse

from wagtail.admin import widgets
from wagtail.models import Locale
from wagtail.test.snippets.models import TranslatableSnippet
from wagtail.test.testapp.models import Advert
from wagtail.test.testapp.views import AdvertChooserWidget
from wagtail.test.utils.wagtail_tests import WagtailTestUtils


class TestChooserViewSetWithFilteredObjects(WagtailTestUtils, TestCase):
    @classmethod
    def setUpTestData(cls):
        Advert.objects.create(text="Head On, apply directly to the forehead")

        advert2 = Advert.objects.create(
            url="https://quiznos.com", text="We like the subs"
        )
        advert2.tags.add("animated")

    def setUp(self):
        self.user = self.login()

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

    @override_settings(WAGTAIL_I18N_ENABLED=True)
    def test_filter_by_locale(self):
        fr_locale = Locale.objects.create(language_code="fr")

        TranslatableSnippet.objects.create(text="English snippet")
        TranslatableSnippet.objects.create(text="French snippet", locale=fr_locale)

        chooser_url = reverse(
            "wagtailsnippetchoosers_snippetstests_translatablesnippet:choose"
        )
        response = self.client.get(chooser_url)
        self.assertEqual(response.status_code, 200)
        soup = self.get_soup(json.loads(response.content)["html"])

        options = soup.select("select[name=locale] option")
        self.assertEqual(len(options), 3)
        self.assertListEqual(
            [(option["value"], option.text) for option in options],
            [("", "All"), ("en", "English"), ("fr", "French")],
        )

        self.assertEqual(len(response.context["results"]), 2)
        self.assertEqual(response.context["results"][0].text, "English snippet")
        self.assertEqual(response.context["results"][1].text, "French snippet")

        response = self.client.get(f"{chooser_url}?locale=en")
        self.assertEqual(len(response.context["results"]), 1)
        self.assertEqual(response.context["results"][0].text, "English snippet")
