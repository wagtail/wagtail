from django.test import TestCase
from django.urls import reverse

from wagtail.snippets.widgets import (
    AdminSnippetChooser,
    SnippetChooserAdapter,
)
from wagtail.test.testapp.models import Advert
from wagtail.test.utils import WagtailTestUtils


class TestAdminSnippetChooserWidget(WagtailTestUtils, TestCase):
    def setUp(self):
        self.advert = Advert.objects.create(text="test advert")

    def test_adapt(self):
        widget = AdminSnippetChooser(Advert)

        js_args = SnippetChooserAdapter().js_args(widget)

        self.assertEqual(len(js_args), 3)
        self.assertInHTML(
            '<input type="hidden" name="__NAME__" id="__ID__">', js_args[0]
        )
        self.assertIn("Choose advert", js_args[0])
        self.assertEqual(js_args[1], "__ID__")

    def test_edit_url_hidden_for_user_without_edit_permission(self):
        user = self.create_user("editor-without-advert-permissions")
        widget = AdminSnippetChooser(Advert, user=user)

        value_data = widget.get_value_data_from_instance(self.advert)

        self.assertIsNone(value_data["edit_url"])

    def test_edit_url_shown_for_user_with_edit_permission(self):
        user = self.create_user("editor", permissions=["change_advert"])
        widget = AdminSnippetChooser(Advert, user=user)

        value_data = widget.get_value_data_from_instance(self.advert)

        self.assertEqual(
            value_data["edit_url"],
            reverse("wagtailsnippets_tests_advert:edit", args=[self.advert.pk]),
        )
