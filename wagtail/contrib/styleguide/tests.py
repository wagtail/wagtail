from django.test import TestCase
from django.urls import reverse

from wagtail.admin.staticfiles import versioned_static
from wagtail.test.utils import WagtailTestUtils


class TestStyleGuide(WagtailTestUtils, TestCase):
    def setUp(self):
        self.login()

    def test_styleguide(self):
        response = self.client.get(reverse("wagtailstyleguide"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailstyleguide/base.html")

        custom_css = versioned_static("wagtailstyleguide/css/animate-progress.css")
        widget_css = versioned_static("wagtailadmin/css/panels/draftail.css")
        widget_js = versioned_static("wagtailadmin/js/draftail.js")
        self.assertContains(response, custom_css)
        self.assertContains(response, widget_css)
        self.assertContains(response, widget_js)

    def test_icons(self):
        def register_icons(icons):
            return icons + [
                "tests/icons/single-quotes.svg",  # id='icon-single-quotes'
            ]

        with self.register_hook("register_icons", register_icons):
            response = self.client.get(reverse("wagtailstyleguide"))

        self.assertEqual(response.status_code, 200)
        # Should render the icons in the table
        self.assertContains(
            response,
            '<use href="#icon-single-quotes"></use>',
            html=True,
        )
        self.assertContains(
            response,
            "<td>Custom icon with single quotes for the id</td>",
            html=True,
        )
        # Built-in icon, not from the above hook
        self.assertContains(
            response,
            '<use href="#icon-h1"></use>',
            html=True,
        )
        self.assertContains(
            response,
            "<td>Custom icon</td>",
            html=True,
        )
