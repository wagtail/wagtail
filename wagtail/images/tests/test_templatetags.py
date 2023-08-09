from django.template import Variable
from django.test import TestCase

from wagtail.images.models import Image, Rendition
from wagtail.images.templatetags.wagtailimages_tags import ImageNode
from wagtail.images.tests.utils import get_test_image_file, get_test_image_file_svg


class ImageNodeTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create an image for running tests on
        cls.image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(),
        )
        cls.svg_image = Image.objects.create(
            title="Test SVG image",
            file=get_test_image_file_svg(),
        )

    def test_render_valid_image_to_string(self):
        """
        Tests that an ImageNode with a valid image renders an img tag
        """
        context = {"image": self.image}
        node = ImageNode(Variable("image"), ["original"])

        rendered = node.render(context)

        self.assertIn('<img alt="Test image"', rendered)

    def test_render_none_to_string(self):
        """
        Tests that an ImageNode without image renders an empty string
        """
        context = {"image": None}
        node = ImageNode(Variable("image"), ["original"])

        rendered = node.render(context)

        self.assertEqual(rendered, "")

    def test_render_valid_image_as_context_variable(self):
        """
        Tests that an ImageNode with a valid image and a context variable name
        renders an empty string and puts a rendition in the context variable
        """
        context = {"image": self.image, "image_node": "fake value"}
        node = ImageNode(Variable("image"), ["original"], "image_node")

        rendered = node.render(context)

        self.assertEqual(rendered, "")
        self.assertIsInstance(context["image_node"], Rendition)

    def test_render_none_as_context_variable(self):
        """
        Tests that an ImageNode without an image and a context variable name
        renders an empty string and puts None in the context variable
        """
        context = {"image": None, "image_node": "fake value"}
        node = ImageNode(Variable("image"), ["original"], "image_node")

        rendered = node.render(context)

        self.assertEqual(rendered, "")
        self.assertIsNone(context["image_node"])

    def test_filters_preserve_svg(self):
        """
        If the image is an SVG, and we set the preserve_svg parameter of ImageNode
        to True, we should only use filters that don't require rasterisation (at this
        time, resize and crop operations only).
        """
        params = [
            (self.svg_image, ["original"], "original"),
            (self.svg_image, ["fill-400x400", "bgcolor-000"], "fill-400x400"),
            (
                self.svg_image,
                ["fill-400x400", "format-webp", "webpquality-50"],
                "fill-400x400",
            ),
            (self.image, ["fill-400x400", "bgcolor-000"], "fill-400x400|bgcolor-000"),
            (self.image, ["fill-400x400", "format-webp"], "fill-400x400|format-webp"),
            (
                self.image,
                ["fill-400x400", "format-webp", "webpquality-50"],
                "fill-400x400|format-webp|webpquality-50",
            ),
            (self.svg_image, ["max-400x400"], "max-400x400"),
            (self.svg_image, ["min-400x400"], "min-400x400"),
            (self.svg_image, ["width-300"], "width-300"),
            (self.svg_image, ["height-300"], "height-300"),
            (self.svg_image, ["scale-50"], "scale-50"),
            (self.svg_image, ["fill-400x400"], "fill-400x400"),
        ]
        for image, filter_specs, expected in params:
            with self.subTest(img=image, filter_specs=filter_specs, expected=expected):
                context = {"image": image, "image_node": "fake_value"}
                node = ImageNode(Variable("image"), filter_specs, preserve_svg=True)
                node.render(context)
                self.assertEqual(
                    node.get_filter(preserve_svg=image.is_svg()).spec, expected
                )
