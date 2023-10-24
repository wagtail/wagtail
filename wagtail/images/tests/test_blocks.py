import unittest.mock

from django.apps import apps
from django.test import TestCase

from wagtail.images.blocks import ImageChooserBlock

from .utils import (
    Image,
    get_test_bad_image,
    get_test_image_file,
    get_test_image_filename,
)


class TestImageChooserBlock(TestCase):
    def setUp(self):
        self.image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(),
        )

        self.bad_image = get_test_bad_image()
        self.bad_image.save()

    def test_render(self):
        block = ImageChooserBlock()
        html = block.render(self.image)
        expected_html = (
            '<img alt="Test image" src="{}" width="640" height="480">'.format(
                get_test_image_filename(self.image, "original")
            )
        )

        self.assertHTMLEqual(html, expected_html)

    def test_render_with_custom_default_attrs(self):
        block = ImageChooserBlock()
        with unittest.mock.patch.object(
            apps.get_app_config("wagtailimages"),
            "default_attrs",
            new={"decoding": "async", "loading": "lazy"},
        ):
            html = block.render(self.bad_image)
        self.assertHTMLEqual(
            html,
            '<img alt="missing image" src="/media/not-found" width="0" height="0" decoding="async" loading="lazy">',
        )

    def test_render_missing(self):
        block = ImageChooserBlock()
        html = block.render(self.bad_image)
        expected_html = (
            '<img alt="missing image" src="/media/not-found" width="0" height="0">'
        )

        self.assertHTMLEqual(html, expected_html)

    def test_deconstruct(self):
        block = ImageChooserBlock(required=False)
        path, args, kwargs = block.deconstruct()
        self.assertEqual(path, "wagtail.images.blocks.ImageChooserBlock")
        self.assertEqual(args, ())
        self.assertEqual(kwargs, {"required": False})

    def test_extract_references(self):
        block = ImageChooserBlock()

        self.assertListEqual(
            list(block.extract_references(self.image)),
            [(Image, str(self.image.id), "", "")],
        )

        # None should not yield any references
        self.assertListEqual(list(block.extract_references(None)), [])
