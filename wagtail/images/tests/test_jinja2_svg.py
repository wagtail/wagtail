from django.test import TestCase

from wagtail.images.models import Image
from wagtail.images.tests.utils import (
    get_test_image_file,
    get_test_image_file_svg,
    get_test_image_filename,
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
        filename = get_test_image_filename(self.raster_image, "width-200.format-webp")

        self.assertHTMLEqual(
            html,
            f'<img src="{filename}" width="200" height="150" alt="Test raster image">',
        )

    def test_image_with_svg_without_preserve(self):
        """Test that without preserve-svg, SVGs get all operations (which would fail in production)."""
        with self.assertRaises(AttributeError):
            self.render(
                '{{ image(img, "width-200|format-webp") }}', {"img": self.svg_image}
            )

    def test_image_with_svg_with_preserve(self):
        """Test that with preserve-svg filter, SVGs only get safe operations."""
        html = self.render(
            '{{ image(img, "width-45|format-webp|preserve-svg") }}',
            {"img": self.svg_image},
        )
        filename = get_test_image_filename(self.svg_image, "width-45")

        self.assertHTMLEqual(
            html,
            f'<img src="{filename}" width="45.0" height="45.0" alt="Test SVG image">',
        )

    def test_raster_image_with_preserve_svg(self):
        """Test that preserve-svg on image tag has no effect on raster images."""
        html = self.render(
            '{{ image(img, "width-100|format-webp|preserve-svg") }}',
            {"img": self.raster_image},
        )
        filename = get_test_image_filename(self.raster_image, "width-100.format-webp")

        self.assertHTMLEqual(
            html,
            f'<img src="{filename}" width="100" height="75" alt="Test raster image">',
        )

    def test_srcset_image_with_svg_preserve(self):
        """Test that preserve-svg works with srcset_image function."""
        html = self.render(
            '{{ srcset_image(img, "width-{35,55}|format-webp|preserve-svg", sizes="100vw") }}',
            {"img": self.svg_image},
        )
        filename35 = get_test_image_filename(self.svg_image, "width-35")
        filename55 = get_test_image_filename(self.svg_image, "width-55")

        self.assertHTMLEqual(
            html,
            f"""
                <img sizes="100vw" src="{filename35}"
                    srcset="{filename35} 35.0w, {filename55} 55.0w" width="35.0" height="35.0"
                    alt="Test SVG image">
            """,
        )

    def test_raster_srcset_image_with_preserve_svg(self):
        """Test that preserve-svg on srcset_image tag has no effect on raster images."""
        html = self.render(
            '{{ srcset_image(img, "width-{100,120}|format-webp|preserve-svg", sizes="100vw") }}',
            {"img": self.raster_image},
        )
        filename100 = get_test_image_filename(
            self.raster_image, "width-100.format-webp"
        )
        filename120 = get_test_image_filename(
            self.raster_image, "width-120.format-webp"
        )

        self.assertHTMLEqual(
            html,
            f"""
                <img sizes="100vw" src="{filename100}"
                    srcset="{filename100} 100w, {filename120} 120w" width="100" height="75"
                    alt="Test raster image">
            """,
        )

    def test_picture_with_svg_preserve(self):
        """Test that preserve-svg works with picture function."""
        html = self.render(
            '{{ picture(img, "format-{avif,webp,jpeg}|width-85|preserve-svg") }}',
            {"img": self.svg_image},
        )
        filename = get_test_image_filename(self.svg_image, "width-85")
        self.assertHTMLEqual(
            html,
            f"""
                <picture>
                    <img src="{filename}" alt="Test SVG image" width="85.0" height="85.0">
                </picture>
            """,
        )

    def test_raster_picture_with_preserve_svg(self):
        """Test that preserve-svg on picture tag has no effect on raster images."""
        html = self.render(
            '{{ picture(img, "width-160|format-{webp,jpeg}|preserve-svg") }}',
            {"img": self.raster_image},
        )
        filename_webp = get_test_image_filename(
            self.raster_image, "width-160.format-webp"
        )
        filename_jpeg = get_test_image_filename(
            self.raster_image, "width-160.format-jpeg"
        )

        self.assertHTMLEqual(
            html,
            f"""
                <picture>
                    <source srcset="{filename_webp}" type="image/webp">
                    <img src="{filename_jpeg}" alt="Test raster image" width="160" height="120">
                </picture>
            """,
        )

    def test_preserve_svg_with_multiple_operations(self):
        """Test preserve-svg with multiple operations, some safe, some unsafe for SVGs."""
        html = self.render(
            '{{ image(img, "width-300|height-200|format-webp|max-100x100|jpegquality-80|preserve-svg") }}',
            {"img": self.svg_image},
        )
        filename = get_test_image_filename(
            self.svg_image, "width-300.height-200.max-100x100"
        )
        self.assertHTMLEqual(
            html,
            f'<img src="{filename}" alt="Test SVG image" width="100.0" height="100.0">',
        )

    def test_preserve_svg_with_custom_attributes(self):
        """Test preserve-svg works with custom HTML attributes."""
        html = self.render(
            '{{ image(img, "width-66|format-webp|preserve-svg", class="my-image", alt="Custom alt") }}',
            {"img": self.svg_image},
        )
        filename = get_test_image_filename(self.svg_image, "width-66")

        self.assertHTMLEqual(
            html,
            f'<img src="{filename}" class="my-image" alt="Custom alt" width="66.0" height="66.0">',
        )

    def test_picture_with_multiple_formats_and_sizes_with_raster_image(self):
        filenames = [
            get_test_image_filename(self.raster_image, "width-160.format-avif"),
            get_test_image_filename(self.raster_image, "width-320.format-avif"),
            get_test_image_filename(self.raster_image, "width-160.format-jpeg"),
            get_test_image_filename(self.raster_image, "width-320.format-jpeg"),
        ]

        rendered = self.render(
            '{{ picture(myimage, "width-{160,320}|format-{avif,jpeg}|preserve-svg", sizes="100vw") }}',
            {"myimage": self.raster_image},
        )
        expected = f"""
            <picture>
            <source srcset="{filenames[0]} 160w, {filenames[1]} 320w" sizes="100vw" type="image/avif">
            <img
                sizes="100vw"
                src="{filenames[2]}"
                srcset="{filenames[2]} 160w, {filenames[3]} 320w"
                alt="Test raster image"
                width="160"
                height="120"
            >
            </picture>
        """
        self.assertHTMLEqual(rendered, expected)

    def test_picture_with_multiple_formats_and_sizes_with_svg_image(self):
        filenames = [
            get_test_image_filename(self.svg_image, "width-45"),
            get_test_image_filename(self.svg_image, "width-90"),
        ]

        rendered = self.render(
            '{{ picture(myimage, "width-{45,90}|format-{avif,jpeg}|preserve-svg", sizes="100vw") }}',
            {"myimage": self.svg_image},
        )
        expected = f"""
            <picture>
            <img
                sizes="100vw"
                src="{filenames[0]}"
                srcset="{filenames[0]} 45.0w, {filenames[1]} 90.0w"
                alt="Test SVG image"
                width="45.0"
                height="45.0"
            >
            </picture>
        """
        self.assertHTMLEqual(rendered, expected)
