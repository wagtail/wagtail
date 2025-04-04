from django.db import models
from django.test import TestCase

from wagtail.images.forms import get_image_form
from wagtail.images.models import AbstractImage, Image


class CustomImageWithBooleanField(AbstractImage):
    watermark = models.BooleanField(default=True)

    admin_form_fields = Image.admin_form_fields + ("watermark",)


class TestImageFormBooleanDefaults(TestCase):
    def test_boolean_field_default_respected(self):
        # Get the form class for our custom model
        ImageForm = get_image_form(CustomImageWithBooleanField)

        # Create a new form instance (no instance passed, so it's for a new image)
        form = ImageForm()
        self.assertTrue(form.initial.get("watermark"))

        # Check with an explicit instance too
        instance = CustomImageWithBooleanField()
        form_with_instance = ImageForm(instance=instance)
        self.assertTrue(form_with_instance.initial.get("watermark"))
