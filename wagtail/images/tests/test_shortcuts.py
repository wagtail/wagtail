# coding=utf-8
from django.test import TestCase

from wagtail.images.shortcuts import get_rendition_or_not_found

from .utils import Image, get_test_image_file


class TestShortcuts(TestCase):

    fixtures = ["test.json"]

    def test_fallback_to_not_found(self):
        bad_image = Image.objects.get(id=1)
        good_image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(),
        )

        rendition = get_rendition_or_not_found(good_image, "width-400")
        self.assertEqual(rendition.width, 400)

        rendition = get_rendition_or_not_found(bad_image, "width-400")
        self.assertEqual(rendition.file.name, "not-found")
