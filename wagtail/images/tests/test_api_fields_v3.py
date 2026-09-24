from django.test import TestCase

from wagtail.images.api.v3.fields import ImageRenditionField

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

    def test_source_resolution(self):
        field = ImageRenditionField("width-400", source="feed_image")
        field.bind("thumbnail")

        class Page:
            feed_image = self.image
            different_image = None

        representation = field.to_representation(field.get_attribute(Page()))
        self.assertEqual(
            representation["width"], self.image.get_rendition("width-400").width
        )

    def test_source_resolution_none(self):
        field = ImageRenditionField("width-400", source="feed_image")
        field.bind("thumbnail")

        class Page:
            feed_image = None

        self.assertIsNone(field.get_attribute(Page()))

    def test_star_source(self):
        field = ImageRenditionField("width-400", source="*")
        field.bind("thumbnail")

        self.assertEqual(field.get_attribute(self.image), self.image)

    def test_defaults_to_field_name(self):
        field = ImageRenditionField("width-400")
        field.bind("feed_image")

        class Page:
            feed_image = self.image

        self.assertEqual(field.get_attribute(Page()), self.image)
