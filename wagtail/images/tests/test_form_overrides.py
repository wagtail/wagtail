from django import forms
from django.test import TestCase, override_settings
from taggit import models as taggit_models

from wagtail.admin import widgets
from wagtail.admin.widgets import AdminDateTimeInput
from wagtail.images import models
from wagtail.images.forms import BaseImageForm, get_image_base_form, get_image_form
from wagtail.test.testapp.media_forms import AlternateImageForm, OverriddenWidget
from wagtail.test.testapp.models import CustomRestaurantImage, RestaurantTag


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
        self.assertEqual(form.fields["tags"].widget.tag_model, taggit_models.Tag)
        self.assertIsInstance(form.fields["file"].widget, forms.FileInput)
        self.assertIsInstance(form.fields["focal_point_x"].widget, forms.HiddenInput)

    def test_tags_widget_with_custom_tag_model(self):
        form_cls = get_image_form(CustomRestaurantImage)
        form = form_cls()
        self.assertIsInstance(form.fields["tags"].widget, widgets.AdminTagWidget)
        self.assertEqual(form.fields["tags"].widget.tag_model, RestaurantTag)

    @override_settings(
        WAGTAILIMAGES_IMAGE_FORM_BASE="wagtail.test.testapp.media_forms.AlternateImageForm"
    )
    def test_overridden_base_form(self):
        self.assertIs(get_image_base_form(), AlternateImageForm)

    @override_settings(
        WAGTAILIMAGES_IMAGE_FORM_BASE="wagtail.test.testapp.media_forms.AlternateImageForm"
    )
    def test_get_overridden_image_form(self):
        bases = get_image_form(models.Image).__bases__
        self.assertNotIn(BaseImageForm, bases)
        self.assertIn(AlternateImageForm, bases)

    @override_settings(
        WAGTAILIMAGES_IMAGE_FORM_BASE="wagtail.test.testapp.media_forms.AlternateImageForm"
    )
    def test_get_overridden_image_form_widgets(self):
        form_cls = get_image_form(models.Image)
        form = form_cls()
        self.assertIsInstance(form.fields["tags"].widget, OverriddenWidget)
        self.assertIsInstance(form.fields["file"].widget, OverriddenWidget)
        self.assertIsInstance(form.fields["focal_point_x"].widget, forms.HiddenInput)

        self.assertIn("form_only_field", form.fields)
        self.assertIs(form.Meta.widgets["form_only_field"], AdminDateTimeInput)
