from django.test import TestCase
from django.utils import translation
from django.utils.translation import gettext

from wagtail.snippets.widgets import (
    AdminSnippetChooser,
    SnippetChooserAdapter,
)
from wagtail.test.testapp.models import Advert
from wagtail.test.utils import WagtailTestUtils


class TestAdminSnippetChooserWidget(WagtailTestUtils, TestCase):
    def test_adapt(self):
        widget = AdminSnippetChooser(Advert)

        js_args = SnippetChooserAdapter().js_args(widget)

        self.assertEqual(len(js_args), 3)
        self.assertInHTML(
            '<input type="hidden" name="__NAME__" id="__ID__">', js_args[0]
        )
        self.assertIn("Choose advert", js_args[0])
        self.assertEqual(js_args[1], "__ID__")

    def test_labels_translated_at_render_time(self):
        # The widget can outlive the request that created it, so the language
        # active on construction may differ from the one active on render.
        with translation.override("en"):
            widget = AdminSnippetChooser(Advert)

        with translation.override("fr"):
            html = widget.render_html("test", None, attrs={"id": "test-id"})
            choose_one = gettext("Choose %(object)s") % {"object": "advert"}
            choose_another = gettext("Choose another %(object)s") % {"object": "advert"}
            edit_this = gettext("Edit this %(object)s") % {"object": "advert"}

        # Ensure we have French strings without tests failing if translations change
        self.assertNotEqual(choose_one, "Choose advert")
        self.assertNotEqual(choose_another, "Choose another advert")
        self.assertNotEqual(edit_this, "Edit this advert")

        self.assertIn(choose_one, html)
        self.assertIn(choose_another, html)
        self.assertIn(edit_this, html)
