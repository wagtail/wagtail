from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, TestCase

from wagtail.admin.panels import FieldPanel, ObjectList, get_edit_handler
from wagtail.snippets.widgets import AdminSnippetChooser
from wagtail.test.testapp.models import (
    Advert,
    AdvertWithCustomPrimaryKey,
    SnippetChooserModel,
    SnippetChooserModelWithCustomPrimaryKey,
)
from wagtail.test.utils import WagtailTestUtils


class TestSnippetChooserPanel(WagtailTestUtils, TestCase):
    fixtures = ["test.json"]

    def setUp(self):
        self.request = RequestFactory().get("/")
        user = AnonymousUser()  # technically, Anonymous users cannot access the admin
        self.request.user = user

        model = SnippetChooserModel
        self.advert_text = "Test advert text"
        test_snippet = model.objects.create(
            advert=Advert.objects.create(text=self.advert_text)
        )

        self.edit_handler = get_edit_handler(model)
        self.form_class = self.edit_handler.get_form_class()
        form = self.form_class(instance=test_snippet)
        edit_handler = self.edit_handler.get_bound_panel(
            instance=test_snippet, form=form, request=self.request
        )

        self.snippet_chooser_panel = [
            panel
            for panel in edit_handler.children
            if getattr(panel, "field_name", None) == "advert"
        ][0]

    def test_render_html(self):
        field_html = self.snippet_chooser_panel.render_html()
        self.assertIn(self.advert_text, field_html)
        self.assertIn("Choose advert", field_html)
        self.assertIn("Choose another advert", field_html)
        self.assertIn("icon icon-snippet icon", field_html)

    def test_render_as_empty_field(self):
        test_snippet = SnippetChooserModel()
        form = self.form_class(instance=test_snippet)
        edit_handler = self.edit_handler.get_bound_panel(
            instance=test_snippet, form=form, request=self.request
        )

        snippet_chooser_panel = [
            panel
            for panel in edit_handler.children
            if getattr(panel, "field_name", None) == "advert"
        ][0]

        field_html = snippet_chooser_panel.render_html()
        self.assertIn("Choose advert", field_html)
        self.assertIn("Choose another advert", field_html)

    def test_render_js(self):
        self.assertIn(
            'new SnippetChooser("id_advert", {"modalUrl": "/admin/snippets/choose/tests/advert/"});',
            self.snippet_chooser_panel.render_html(),
        )

    def test_target_model_autodetected(self):
        edit_handler = ObjectList([FieldPanel("advert")]).bind_to_model(
            SnippetChooserModel
        )
        form_class = edit_handler.get_form_class()
        form = form_class()
        widget = form.fields["advert"].widget
        self.assertIsInstance(widget, AdminSnippetChooser)
        self.assertEqual(widget.model, Advert)


class TestSnippetChooserPanelWithCustomPrimaryKey(WagtailTestUtils, TestCase):
    fixtures = ["test.json"]

    def setUp(self):
        self.request = RequestFactory().get("/")
        user = AnonymousUser()  # technically, Anonymous users cannot access the admin
        self.request.user = user

        model = SnippetChooserModelWithCustomPrimaryKey
        self.advert_text = "Test advert text"
        test_snippet = model.objects.create(
            advertwithcustomprimarykey=AdvertWithCustomPrimaryKey.objects.create(
                advert_id="advert/02", text=self.advert_text
            )
        )

        self.edit_handler = get_edit_handler(model)
        self.form_class = self.edit_handler.get_form_class()
        form = self.form_class(instance=test_snippet)
        edit_handler = self.edit_handler.get_bound_panel(
            instance=test_snippet, form=form, request=self.request
        )

        self.snippet_chooser_panel = [
            panel
            for panel in edit_handler.children
            if getattr(panel, "field_name", None) == "advertwithcustomprimarykey"
        ][0]

    def test_render_html(self):
        field_html = self.snippet_chooser_panel.render_html()
        self.assertIn(self.advert_text, field_html)
        self.assertIn("Choose advert with custom primary key", field_html)
        self.assertIn("Choose another advert with custom primary key", field_html)

    def test_render_as_empty_field(self):
        test_snippet = SnippetChooserModelWithCustomPrimaryKey()
        form = self.form_class(instance=test_snippet)
        edit_handler = self.edit_handler.get_bound_panel(
            instance=test_snippet, form=form, request=self.request
        )

        snippet_chooser_panel = [
            panel
            for panel in edit_handler.children
            if getattr(panel, "field_name", None) == "advertwithcustomprimarykey"
        ][0]

        field_html = snippet_chooser_panel.render_html()
        self.assertIn("Choose advert with custom primary key", field_html)
        self.assertIn("Choose another advert with custom primary key", field_html)

    def test_render_js(self):
        self.assertIn(
            'new SnippetChooser("id_advertwithcustomprimarykey", {"modalUrl": "/admin/snippets/choose/tests/advertwithcustomprimarykey/"});',
            self.snippet_chooser_panel.render_html(),
        )

    def test_target_model_autodetected(self):
        edit_handler = ObjectList(
            [FieldPanel("advertwithcustomprimarykey")]
        ).bind_to_model(SnippetChooserModelWithCustomPrimaryKey)
        form_class = edit_handler.get_form_class()
        form = form_class()
        widget = form.fields["advertwithcustomprimarykey"].widget
        self.assertIsInstance(widget, AdminSnippetChooser)
        self.assertEqual(widget.model, AdvertWithCustomPrimaryKey)
