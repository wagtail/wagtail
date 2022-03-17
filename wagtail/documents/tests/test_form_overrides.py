from django import forms
from django.test import TestCase, override_settings

from wagtail.admin import widgets
from wagtail.admin.widgets import AdminDateTimeInput
from wagtail.documents import models
from wagtail.documents.forms import (
    BaseDocumentForm,
    get_document_base_form,
    get_document_form,
    get_document_multi_form,
)
from wagtail.test.testapp.media_forms import AlternateDocumentForm, OverriddenWidget


class TestDocumentFormOverride(TestCase):
    def test_get_document_base_form(self):
        self.assertIs(get_document_base_form(), BaseDocumentForm)

    def test_get_document_form(self):
        bases = get_document_form(models.Document).__bases__
        self.assertIn(BaseDocumentForm, bases)
        self.assertNotIn(AlternateDocumentForm, bases)

    def test_get_document_form_widgets(self):
        form_cls = get_document_form(models.Document)
        form = form_cls()
        self.assertIsInstance(form.fields["tags"].widget, widgets.AdminTagWidget)
        self.assertIsInstance(form.fields["file"].widget, forms.FileInput)

    @override_settings(
        WAGTAILDOCS_DOCUMENT_FORM_BASE="wagtail.test.testapp.media_forms.AlternateDocumentForm"
    )
    def test_overridden_base_form(self):
        self.assertIs(get_document_base_form(), AlternateDocumentForm)

    @override_settings(
        WAGTAILDOCS_DOCUMENT_FORM_BASE="wagtail.test.testapp.media_forms.AlternateDocumentForm"
    )
    def test_get_overridden_document_form(self):
        bases = get_document_form(models.Document).__bases__
        self.assertNotIn(BaseDocumentForm, bases)
        self.assertIn(AlternateDocumentForm, bases)

    @override_settings(
        WAGTAILDOCS_DOCUMENT_FORM_BASE="wagtail.test.testapp.media_forms.AlternateDocumentForm"
    )
    def test_get_overridden_document_multi_form(self):
        bases = get_document_multi_form(models.Document).__bases__
        self.assertNotIn(BaseDocumentForm, bases)
        self.assertIn(AlternateDocumentForm, bases)

    @override_settings(
        WAGTAILDOCS_DOCUMENT_FORM_BASE="wagtail.test.testapp.media_forms.AlternateDocumentForm"
    )
    def test_get_overridden_document_form_widgets(self):
        form_cls = get_document_form(models.Document)
        form = form_cls()

        self.assertIsInstance(form.fields["tags"].widget, OverriddenWidget)
        self.assertIsInstance(form.fields["file"].widget, OverriddenWidget)

        self.assertIn("form_only_field", form.fields)
        self.assertIs(form.Meta.widgets["form_only_field"], AdminDateTimeInput)
