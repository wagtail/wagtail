from django.test import TestCase

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
