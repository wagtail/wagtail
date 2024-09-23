from django.template import Context, Engine, TemplateSyntaxError, Variable
from django.test import TestCase

from wagtail.images.models import Image, Rendition
from wagtail.images.templatetags.wagtailimages_tags import ImageNode
from wagtail.images.tests.utils import (
    get_test_bad_image,
    get_test_image_file,
    get_test_image_file_svg,
    get_test_image_filename,
)

LIBRARIES = {
    "wagtailimages_tags": "wagtail.images.templatetags.wagtailimages_tags",
    "l10n": "django.templatetags.l10n",
}


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


class ImagesTestCase(TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.engine = Engine(
            app_dirs=True,
            libraries=LIBRARIES,
            builtins=[
                LIBRARIES["wagtailimages_tags"],
                LIBRARIES["l10n"],
            ],
        )

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
        cls.bad_image = get_test_bad_image()
        cls.bad_image.save()

    def render(self, string, context=None):
        if context is None:
            context = {}

        template = self.engine.from_string(string)
        return template.render(Context(context, autoescape=False))


class ImageTagTestCase(ImagesTestCase):
    def test_image(self):
        filename_200 = get_test_image_filename(self.image, "width-200")

        rendered = self.render("{% image myimage width-200 %}", {"myimage": self.image})
        self.assertHTMLEqual(
            rendered,
            f'<img alt="Test image" height="150" src="{filename_200}" width="200" />',
        )

    def test_none(self):
        rendered = self.render("{% image myimage width-2 %}", {"myimage": None})
        self.assertEqual(rendered, "")

    def test_missing_image(self):
        rendered = self.render(
            "{% image myimage width-200 %}", {"myimage": self.bad_image}
        )
        self.assertHTMLEqual(
            rendered,
            '<img alt="missing image" src="/media/not-found" width="0" height="0">',
        )

    def test_not_an_image(self):
        with self.assertRaisesMessage(
            ValueError, "Image template tags expect an Image object, got 'not a pipe'"
        ):
            self.render(
                "{% image myimage width-200 %}",
                {"myimage": "not a pipe"},
            )

    def test_invalid_character(self):
        with self.assertRaisesRegex(
            TemplateSyntaxError, "filter specs in image tags may only"
        ):
            self.render(
                "{% image myimage fill-200×200 %}",
                {"myimage": self.image},
            )

    def test_multiple_as_variable(self):
        with self.assertRaisesRegex(
            TemplateSyntaxError, "More than one variable name after 'as'"
        ):
            self.render(
                "{% image myimage width-200 as a b %}",
                {"myimage": self.image},
            )

    def test_missing_as_variable(self):
        with self.assertRaisesRegex(
            TemplateSyntaxError, "Missing a variable name after 'as'"
        ):
            self.render(
                "{% image myimage width-200 as %}",
                {"myimage": self.image},
            )

    def test_mixing_as_variable_and_attrs(self):
        with self.assertRaisesRegex(
            TemplateSyntaxError, "Do not use attributes with 'as' context assignments"
        ):
            self.render(
                "{% image myimage width-200 alt='Test' as test %}",
                {"myimage": self.image},
            )

    def test_missing_filter_spec(self):
        with self.assertRaisesRegex(
            TemplateSyntaxError, "Image tags must be used with at least one filter spec"
        ):
            self.render(
                "{% image myimage %}",
                {"myimage": self.image},
            )


class SrcsetImageTagTestCase(ImagesTestCase):
    def test_srcset_image(self):
        filename_20 = get_test_image_filename(self.image, "width-20")
        filename_40 = get_test_image_filename(self.image, "width-40")

        rendered = self.render(
            "{% srcset_image myimage width-{20,40} sizes='100vw' %}",
            {"myimage": self.image},
        )
        expected = f"""
            <img
                sizes="100vw"
                src="{filename_20}"
                srcset="{filename_20} 20w, {filename_40} 40w"
                alt="Test image"
                width="20"
                height="15"
            >
        """
        self.assertHTMLEqual(rendered, expected)

    def test_srcset_output_single_image(self):
        self.assertHTMLEqual(
            self.render(
                "{% srcset_image myimage width-20 %}",
                {"myimage": self.image},
            ),
            self.render(
                "{% image myimage width-20 %}",
                {"myimage": self.image},
            ),
        )

    def test_none(self):
        rendered = self.render("{% srcset_image myimage width-2 %}", {"myimage": None})
        self.assertEqual(rendered, "")

    def test_invalid_character(self):
        with self.assertRaisesRegex(
            TemplateSyntaxError, "filter specs in image tags may only contain"
        ):
            self.render(
                "{% srcset_image myimage fill-{200×200,400×400} sizes='100vw' %}",
                {"myimage": self.image},
            )

    def test_srcset_image_assignment(self):
        template = (
            "{% srcset_image myimage width-{30,60} as bg %}"
            "width: {{ bg.renditions.0.width|unlocalize }}, url: {{ bg.renditions.0.url }} "
            "width: {{ bg.renditions.1.width|unlocalize }}, url: {{ bg.renditions.1.url }} "
        )
        rendered = self.render(template, {"myimage": self.image})
        expected = f"""
            width: 30, url: {get_test_image_filename(self.image, "width-30")}
            width: 60, url: {get_test_image_filename(self.image, "width-60")}
        """
        self.assertHTMLEqual(rendered, expected)

    def test_srcset_image_assignment_render_as_is(self):
        filename_35 = get_test_image_filename(self.image, "width-35")
        filename_70 = get_test_image_filename(self.image, "width-70")

        rendered = self.render(
            "{% srcset_image myimage width-{35,70} as bg %}{{ bg }}",
            {"myimage": self.image},
        )
        expected = f"""
            <img
                src="{filename_35}"
                srcset="{filename_35} 35w, {filename_70} 70w"
                alt="Test image"
                width="35"
                height="26"
            >
        """
        self.assertHTMLEqual(rendered, expected)

    def test_missing_srcset_image(self):
        rendered = self.render(
            "{% srcset_image myimage width-{200,400} sizes='100vw' %}",
            {"myimage": self.bad_image},
        )
        expected = """
            <img
                sizes="100vw"
                src="/media/not-found"
                srcset="/media/not-found 0w, /media/not-found 0w"
                alt="missing image"
                width="0"
                height="0"
            >
        """
        self.assertHTMLEqual(rendered, expected)


class PictureTagTestCase(ImagesTestCase):
    def test_picture_formats_multi_sizes(self):
        filenames = [
            get_test_image_filename(self.image, "width-200.format-jpeg"),
            get_test_image_filename(self.image, "width-400.format-jpeg"),
            get_test_image_filename(self.image, "width-200.format-webp"),
            get_test_image_filename(self.image, "width-400.format-webp"),
            get_test_image_filename(self.image, "width-200.format-gif"),
            get_test_image_filename(self.image, "width-400.format-gif"),
        ]

        rendered = self.render(
            '{% picture myimage width-{200,400} format-{jpeg,webp,gif} sizes="100vw" %}',
            {"myimage": self.image},
        )
        expected = f"""
            <picture>
            <source srcset="{filenames[2]} 200w, {filenames[3]} 400w" sizes="100vw" type="image/webp">
            <source srcset="{filenames[0]} 200w, {filenames[1]} 400w" sizes="100vw" type="image/jpeg">
            <img
                sizes="100vw"
                src="{filenames[4]}"
                srcset="{filenames[4]} 200w, {filenames[5]} 400w"
                alt="Test image"
                width="200"
                height="150"
            >
            </picture>
        """
        self.assertHTMLEqual(rendered, expected)

    def test_picture_formats_only(self):
        filename_jpeg = get_test_image_filename(self.image, "format-jpeg")
        filename_webp = get_test_image_filename(self.image, "format-webp")

        rendered = self.render(
            "{% picture myimage format-{jpeg,webp} %}",
            {"myimage": self.image},
        )
        expected = f"""
            <picture>
            <source srcset="{filename_webp}" type="image/webp">
            <img
                src="{filename_jpeg}"
                alt="Test image"
                width="640"
                height="480"
            >
            </picture>
        """
        self.assertHTMLEqual(rendered, expected)

    def test_picture_sizes_only(self):
        rendered = self.render(
            '{% picture myimage width-{350,450} sizes="100vw" %}',
            {"myimage": self.image},
        )
        expected = self.render(
            '<picture>{% srcset_image myimage width-{350,450} sizes="100vw" %}</picture>',
            {"myimage": self.image},
        )
        self.assertHTMLEqual(rendered, expected)

    def test_picture_single_format(self):
        rendered = self.render(
            "{% picture myimage format-jpeg %}",
            {"myimage": self.image},
        )
        expected = self.render(
            "<picture>{% image myimage format-jpeg %}</picture>",
            {"myimage": self.image},
        )
        self.assertHTMLEqual(rendered, expected)

    def test_none(self):
        rendered = self.render("{% picture myimage width-2 %}", {"myimage": None})
        self.assertEqual(rendered, "")

    def test_picture_assignment(self):
        template = (
            "{% picture myimage width-{550,600} format-{jpeg,webp} as bg %}"
            "width: {{ bg.formats.jpeg.0.width|unlocalize }}, url: {{ bg.formats.jpeg.0.url }} "
            "width: {{ bg.formats.jpeg.1.width|unlocalize }}, url: {{ bg.formats.jpeg.1.url }} "
            "width: {{ bg.formats.webp.0.width|unlocalize }}, url: {{ bg.formats.webp.0.url }} "
            "width: {{ bg.formats.webp.1.width|unlocalize }}, url: {{ bg.formats.webp.1.url }} "
        )
        rendered = self.render(template, {"myimage": self.image})
        expected = f"""
            width: 550, url: {get_test_image_filename(self.image, "width-550.format-jpeg")}
            width: 600, url: {get_test_image_filename(self.image, "width-600.format-jpeg")}
            width: 550, url: {get_test_image_filename(self.image, "width-550.format-webp")}
            width: 600, url: {get_test_image_filename(self.image, "width-600.format-webp")}
        """
        self.assertHTMLEqual(rendered, expected)

    def test_picture_assignment_render_as_is(self):
        rendered = self.render(
            "{% picture myimage width-{2000,4000} format-{jpeg,webp} as bg %}{{ bg }}",
            {"myimage": self.image},
        )
        expected = self.render(
            "{% picture myimage width-{2000,4000} format-{jpeg,webp} %}",
            {"myimage": self.image},
        )
        self.assertHTMLEqual(rendered, expected)

    def test_missing_picture(self):
        rendered = self.render(
            "{% picture myimage width-{200,400} %}",
            {"myimage": self.bad_image},
        )
        expected = """
            <picture>
                <img
                    src="/media/not-found"
                    srcset="/media/not-found 0w, /media/not-found 0w"
                    alt="missing image"
                    width="0"
                    height="0"
                >
            </picture>
        """
        self.assertHTMLEqual(rendered, expected)

    def test_invalid_character(self):
        with self.assertRaisesRegex(
            TemplateSyntaxError, "filter specs in image tags may only"
        ):
            self.render(
                '{% picture myimage fill-{20×20,40×40} sizes="100vw" %}',
                {"myimage": self.image},
            )

    def test_chaining_filterspecs(self):
        filename_jpeg = get_test_image_filename(
            self.image, "format-jpeg.jpegquality-40.webpquality-40"
        )
        filename_webp = get_test_image_filename(
            self.image, "format-webp.jpegquality-40.webpquality-40"
        )
        rendered = self.render(
            "{% picture myimage format-{jpeg,webp} jpegquality-40 webpquality-40 %}",
            {"myimage": self.image},
        )
        expected = f"""
            <picture>
            <source srcset="{filename_webp}" type="image/webp">
            <img
                src="{filename_jpeg}"
                alt="Test image"
                width="640"
                height="480"
            >
            </picture>
        """
        self.assertHTMLEqual(rendered, expected)
