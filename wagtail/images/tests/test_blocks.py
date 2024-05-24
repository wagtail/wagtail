import unittest.mock

from bs4 import BeautifulSoup
from django.apps import apps
from django.test import TestCase

from wagtail.blocks.struct_block import StructBlockValidationError
from wagtail.images.blocks import ImageBlock, ImageChooserBlock

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
        expected_html = '<img src="{}" width="640" height="480">'.format(
            get_test_image_filename(self.image, "original")
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
            '<img src="/media/not-found" width="0" height="0" decoding="async" loading="lazy">',
        )

    def test_render_missing(self):
        block = ImageChooserBlock()
        html = block.render(self.bad_image)
        expected_html = '<img src="/media/not-found" width="0" height="0">'

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


class TestImageBlock(TestImageChooserBlock):
    def test_render(self):
        block = ImageBlock()
        value = {
            "image": self.image.id,  # An id is expected
            "alt_text": "Sample alt text",
            "decorative": False,
        }
        html = block.render(block.to_python(value))
        soup = BeautifulSoup(html, "html.parser")
        img_tag = soup.find("img")

        # check specific attributes
        self.assertEqual(img_tag["alt"], value.get("alt_text"))
        self.assertIn("/media/images/test", img_tag["src"])

    def test_render_as_decorative(self):
        block = ImageBlock()
        value = {
            "image": self.image.id,  # An id is expected
            "alt_text": "Sample alt text",
            "decorative": True,
        }
        html = block.render(block.to_python(value))
        soup = BeautifulSoup(html, "html.parser")
        img_tag = soup.find("img")

        # check specific attributes
        self.assertEqual(img_tag["alt"], "")
        self.assertIn("/media/images/test", img_tag["src"])

    def test_no_alt_text(self):
        block = ImageBlock()
        value = {
            "image": self.image.id,  # An id is expected
            "alt_text": None,  # No alt text passed
            "decorative": False,
        }

        # Invalid state when no alt text is given, and image not marked as decorative
        # Should raise a StructBlock validation error
        with self.assertRaises(StructBlockValidationError) as context:
            block.clean(block.to_python(value))

        # Check the error message
        self.assertIn(
            "Alt text is required for non-decorative images",
            str(context.exception.block_errors["alt_text"]),
        )

    def test_wrong_instance_type(self):
        block = ImageBlock()
        value = {"image": self.image.id, "alt_text": "Blank", "decorative": False}

        # Invalid state when value is not an image instance
        # Should raise a StructBlock validation error
        with self.assertRaises(StructBlockValidationError) as context:
            # pass in dict instead of normalized image instance
            block.clean(value)

        # Check the error message
        self.assertIn(
            "Expected an image instance, got %r" % value,
            str(context.exception.block_errors["image"]),
        )
