from django.test import TestCase

from wagtail.images.models import Image
from wagtail.images.tests.utils import (
    get_test_image_file,
    get_test_image_file_svg,
)
from wagtail.test.utils import WagtailTestUtils


class TestJinja2SVGSupport(WagtailTestUtils, TestCase):
    """Test SVG support in Jinja2 templates with preserve-svg filter."""

    def setUp(self):
        # Create a real test engine
        from django.template.loader import engines

        self.engine = engines["jinja2"]

        # Create a raster image
        self.raster_image = Image.objects.create(
            title="Test raster image",
            file=get_test_image_file(),
        )

        # Create an SVG image
        self.svg_image = Image.objects.create(
            title="Test SVG image",
            file=get_test_image_file_svg(),
        )

    def render(self, string, context=None):
        if context is None:
            context = {}

        template = self.engine.from_string(string)
        return template.render(context)

    def test_image_with_raster_image(self):
        """Test that raster images work normally without preserve-svg."""
        html = self.render(
            '{{ image(img, "width-200|format-webp") }}', {"img": self.raster_image}
        )

        self.assertIn('width="200"', html)
        self.assertIn(".webp", html)  # Format conversion applied

    def test_image_with_svg_without_preserve(self):
        """Test that without preserve-svg, SVGs get all operations (which would fail in production)."""
        with self.assertRaises(AttributeError):
            self.render(
                '{{ image(img, "width-200|format-webp") }}', {"img": self.svg_image}
            )

    def test_image_with_svg_with_preserve(self):
        """Test that with preserve-svg filter, SVGs only get safe operations."""
        html = self.render(
            '{{ image(img, "width-200|format-webp|preserve-svg") }}',
            {"img": self.svg_image},
        )

        # Check the SVG is preserved
        self.assertIn(".svg", html)
        self.assertNotIn(".webp", html)

    def test_srcset_image_with_svg_preserve(self):
        """Test that preserve-svg works with srcset_image function."""
        html = self.render(
            '{{ srcset_image(img, "width-{200,400}|format-webp|preserve-svg", sizes="100vw") }}',
            {"img": self.svg_image},
        )

        # Should preserve SVG format
        self.assertIn(".svg", html)
        self.assertNotIn(".webp", html)

    def test_picture_with_svg_preserve(self):
        """Test that preserve-svg works with picture function."""
        html = self.render(
            '{{ picture(img, "format-{avif,webp,jpeg}|width-400|preserve-svg") }}',
            {"img": self.svg_image},
        )

        # Should preserve SVG format
        self.assertIn(".svg", html)
        self.assertNotIn(".webp", html)
        self.assertNotIn(".avif", html)
        self.assertNotIn(".jpeg", html)

    def test_preserve_svg_with_multiple_operations(self):
        """Test preserve-svg with multiple operations, some safe, some unsafe for SVGs."""
        html = self.render(
            '{{ image(img, "width-300|height-200|format-webp|fill-100x100|jpegquality-80|preserve-svg") }}',
            {"img": self.svg_image},
        )

        # Should preserve SVG format
        self.assertIn(".svg", html)
        self.assertNotIn(".webp", html)
        self.assertNotIn("jpegquality-80", html)

    def test_preserve_svg_with_custom_attributes(self):
        """Test preserve-svg works with custom HTML attributes."""
        html = self.render(
            '{{ image(img, "width-200|format-webp|preserve-svg", class="my-image", alt="Custom alt") }}',
            {"img": self.svg_image},
        )

        # Check custom attributes are present
        self.assertIn('class="my-image"', html)
        self.assertIn('alt="Custom alt"', html)

        # SVG should be preserved
        self.assertNotIn(".webp", html)
        self.assertIn(".svg", html)
