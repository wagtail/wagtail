from django.template import Variable
from django.test import TestCase

from wagtail.images.models import Image, Rendition
from wagtail.images.templatetags.wagtailimages_tags import ImageNode
from wagtail.images.tests.utils import get_test_image_file


class ImageNodeTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create an image for running tests on
        cls.image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(),
        )

    def test_render_valid_image_to_string(self):
        """
        Tests that an ImageNode with a valid image renders an img tag
        """
        context = {"image": self.image}
        node = ImageNode(Variable("image"), "original")

        rendered = node.render(context)

        self.assertIn('<img alt="Test image"', rendered)

    def test_render_none_to_string(self):
        """
        Tests that an ImageNode without image renders an empty string
        """
        context = {"image": None}
        node = ImageNode(Variable("image"), "original")

        rendered = node.render(context)

        self.assertEqual(rendered, "")

    def test_render_valid_image_as_context_variable(self):
        """
        Tests that an ImageNode with a valid image and a context variable name
        renders an empty string and puts a rendition in the context variable
        """
        context = {"image": self.image, "image_node": "fake value"}
        node = ImageNode(Variable("image"), "original", "image_node")

        rendered = node.render(context)

        self.assertEqual(rendered, "")
        self.assertIsInstance(context["image_node"], Rendition)

    def test_render_none_as_context_variable(self):
        """
        Tests that an ImageNode without an image and a context variable name
        renders an empty string and puts None in the context variable
        """
        context = {"image": None, "image_node": "fake value"}
        node = ImageNode(Variable("image"), "original", "image_node")

        rendered = node.render(context)

        self.assertEqual(rendered, "")
        self.assertIsNone(context["image_node"])
