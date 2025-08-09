import json

from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

from wagtail.admin import widgets
from wagtail.admin.ui.tables import TitleColumn
from wagtail.admin.views.generic.chooser import BaseChooseView
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
        self.rf = RequestFactory()

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

    def test_title_column_uses_edit_url_for_href(self):
        """Test that generic chooser title_column uses edit URL for href and chooser URL in data attribute."""
        advert = Advert.objects.create(text="Test advert", url="https://example.com")
        request = self.rf.get("/admin/test_chooser/")
        request.user = self.user

        # mock chooser view
        class MockChooserView(BaseChooseView):
            model = Advert
            chosen_url_name = "test:chosen"
            is_multiple_choice = False

            def append_preserved_url_parameters(self, url):
                return url

        view = MockChooserView()
        view.request = request

        # Test the helper methods
        edit_url = view._get_edit_url_for_object(advert)
        self.assertIsNotNone(edit_url)

        title_column = view.title_column
        self.assertIsInstance(title_column, TitleColumn)

        # Test this is set to the edit URL
        self.assertEqual(title_column._get_url_func, view._get_edit_url_for_object)

        # Test that link_attrs is callable
        self.assertTrue(callable(title_column.link_attrs))

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
