# -*- coding: utf-8 -*
from __future__ import unicode_literals

import os

from django.test import TestCase
from django.core import serializers
from django.conf import settings

from wagtail.wagtailimages.blocks import ImageChooserBlock

from .utils import get_test_image_file, Image


class TestImageChooserBlock(TestCase):
    def setUp(self):
        self.image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(),
        )

        # Create an image with a missing file, by deserializing fom a python object
        # (which bypasses FileField's attempt to read the file)
        self.bad_image = list(serializers.deserialize('python', [{
            'fields': {
                'title': 'missing image',
                'height': 100,
                'file': 'original_images/missing-image.jpg',
                'width': 100,
            },
            'model': 'wagtailimages.image'
        }]))[0].object
        self.bad_image.save()

    def get_image_filename(self, image, filterspec):
        """
        Get the generated filename for a resized image
        """
        name, ext = os.path.splitext(os.path.basename(image.file.name))
        return '{}images/{}.{}{}'.format(
            settings.MEDIA_URL, name, filterspec, ext)

    def test_render(self):
        block = ImageChooserBlock()
        html = block.render(self.image)
        expected_html = '<img alt="Test image" src="{}" width="640" height="480">'.format(
            self.get_image_filename(self.image, "original")
        )

        self.assertHTMLEqual(html, expected_html)

    def test_render_missing(self):
        block = ImageChooserBlock()
        html = block.render(self.bad_image)
        expected_html = '<img alt="missing image" src="/media/not-found" width="0" height="0">'

        self.assertHTMLEqual(html, expected_html)
