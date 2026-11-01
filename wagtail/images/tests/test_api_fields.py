from typing import get_type_hints
from unittest import mock

from django.test import TestCase
from pydantic import TypeAdapter

from wagtail.images.api.fields import ImageRenditionField
from wagtail.images.models import SourceImageIOError

from .utils import Image, get_test_image_file


class TestImageRenditionField(TestCase):
    def setUp(self):
        self.image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(),
        )

    def test_api_representation(self):
        rendition = self.image.get_rendition("width-400")
        representation = ImageRenditionField("width-400").to_representation(self.image)
        self.assertEqual(
            set(representation.keys()), {"url", "full_url", "width", "height", "alt"}
        )
        self.assertEqual(representation["url"], rendition.url)
        self.assertEqual(representation["full_url"], rendition.full_url)
        self.assertEqual(representation["width"], rendition.width)
        self.assertEqual(representation["height"], rendition.height)
        self.assertEqual(representation["alt"], rendition.alt)

    def test_api_representation_source_image_error(self):
        with mock.patch.object(Image, "get_rendition", side_effect=SourceImageIOError):
            representation = ImageRenditionField("width-400").to_representation(
                self.image
            )
        self.assertEqual(representation, {"error": "SourceImageIOError"})

    def test_api_representation_matches_return_annotation(self):
        adapter = TypeAdapter(
            get_type_hints(ImageRenditionField.to_representation)["return"]
        )
        field = ImageRenditionField("width-400")
        adapter.validate_python(field.to_representation(self.image))
        with mock.patch.object(Image, "get_rendition", side_effect=SourceImageIOError):
            adapter.validate_python(field.to_representation(self.image))
