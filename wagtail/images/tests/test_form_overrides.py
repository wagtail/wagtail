from django import forms
from django.test import TestCase, override_settings

from wagtail.admin import widgets
from wagtail.admin.widgets import AdminDateTimeInput
from wagtail.images import models
from wagtail.images.forms import BaseImageForm, get_image_base_form, get_image_form
from wagtail.tests.testapp.media_forms import AlternateImageForm, OverriddenWidget


class TestImageFormOverride(TestCase):
    def test_get_image_base_form(self):
        self.assertIs(get_image_base_form(), BaseImageForm)

    def test_get_image_form(self):
        bases = get_image_form(models.Image).__bases__
        self.assertIn(BaseImageForm, bases)
        self.assertNotIn(AlternateImageForm, bases)

    def test_get_image_form_widgets(self):
        form_cls = get_image_form(models.Image)
        form = form_cls()
        self.assertIsInstance(form.fields["tags"].widget, widgets.AdminTagWidget)
        self.assertIsInstance(form.fields["file"].widget, forms.FileInput)
        self.assertIsInstance(form.fields["focal_point_x"].widget, forms.HiddenInput)

    @override_settings(WAGTAILIMAGES_IMAGE_FORM_BASE="wagtail.tests.testapp.media_forms.AlternateImageForm")
    def test_overridden_base_form(self):
        self.assertIs(get_image_base_form(), AlternateImageForm)

    @override_settings(WAGTAILIMAGES_IMAGE_FORM_BASE="wagtail.tests.testapp.media_forms.AlternateImageForm")
    def test_get_overridden_image_form(self):
        bases = get_image_form(models.Image).__bases__
        self.assertNotIn(BaseImageForm, bases)
        self.assertIn(AlternateImageForm, bases)

    @override_settings(WAGTAILIMAGES_IMAGE_FORM_BASE="wagtail.tests.testapp.media_forms.AlternateImageForm")
    def test_get_overridden_image_form_widgets(self):
        form_cls = get_image_form(models.Image)
        form = form_cls()
        self.assertIsInstance(form.fields["tags"].widget, OverriddenWidget)
        self.assertIsInstance(form.fields["file"].widget, OverriddenWidget)
        self.assertIsInstance(form.fields["focal_point_x"].widget, forms.HiddenInput)

        self.assertIn("form_only_field", form.fields)
        self.assertIs(form.Meta.widgets["form_only_field"], AdminDateTimeInput)
