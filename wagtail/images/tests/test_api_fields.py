from django.test import TestCase

from wagtail.images.api.fields import ImageRenditionField

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
