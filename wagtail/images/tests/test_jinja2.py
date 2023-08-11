import unittest.mock

from django.apps import apps
from django.template import TemplateSyntaxError, engines
from django.test import TestCase

from wagtail.models import Site

from .utils import (
    Image,
    get_test_bad_image,
    get_test_image_file,
    get_test_image_filename,
)


class JinjaImagesTestCase(TestCase):
    def setUp(self):
        self.engine = engines["jinja2"]

        self.image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(),
        )

        self.bad_image = get_test_bad_image()
        self.bad_image.save()

    def render(self, string, context=None, request_context=True):
        if context is None:
            context = {}

        # Add a request to the template, to simulate a RequestContext
        if request_context:
            site = Site.objects.get(is_default_site=True)
            request = self.client.get("/test/", HTTP_HOST=site.hostname)
            context["request"] = request

        template = self.engine.from_string(string)
        return template.render(context)


class TestImageJinja(JinjaImagesTestCase):
    def test_image(self):
        self.assertHTMLEqual(
            self.render('{{ image(myimage, "width-200") }}', {"myimage": self.image}),
            '<img alt="Test image" src="{}" width="200" height="150">'.format(
                get_test_image_filename(self.image, "width-200")
            ),
        )

    def test_image_attributes(self):
        self.assertHTMLEqual(
            self.render(
                '{{ image(myimage, "width-200", alt="alternate", class="test") }}',
                {"myimage": self.image},
            ),
            '<img alt="alternate" src="{}" width="200" height="150" class="test">'.format(
                get_test_image_filename(self.image, "width-200")
            ),
        )

    def test_image_assignment(self):
        template = (
            '{% set bg=image(myimage, "width-200") %}'
            "width: {{ bg.width }}, url: {{ bg.url }}"
        )
        output = "width: 200, url: " + get_test_image_filename(self.image, "width-200")
        self.assertHTMLEqual(self.render(template, {"myimage": self.image}), output)

    def test_image_assignment_render_as_is(self):
        self.assertHTMLEqual(
            self.render(
                '{% set bg=image(myimage, "width-200") %}{{ bg }}',
                {"myimage": self.image},
            ),
            '<img alt="Test image" src="{}" width="200" height="150">'.format(
                get_test_image_filename(self.image, "width-200")
            ),
        )

    def test_missing_image(self):
        self.assertHTMLEqual(
            self.render(
                '{{ image(myimage, "width-200") }}', {"myimage": self.bad_image}
            ),
            '<img alt="missing image" src="/media/not-found" width="0" height="0">',
        )

    def test_invalid_character(self):
        with self.assertRaisesRegex(
            TemplateSyntaxError, "filter specs in 'image' tag may only"
        ):
            self.render('{{ image(myimage, "fill-200×200") }}', {"myimage": self.image})

    def test_custom_default_attrs(self):
        with unittest.mock.patch.object(
            apps.get_app_config("wagtailimages"),
            "default_attrs",
            new={"decoding": "async", "loading": "lazy"},
        ):
            self.assertHTMLEqual(
                self.render(
                    '{{ image(myimage, "width-200") }}', {"myimage": self.bad_image}
                ),
                '<img alt="missing image" src="/media/not-found" width="0" height="0" decoding="async" loading="lazy">',
            )

    def test_chaining_filterspecs(self):
        self.assertHTMLEqual(
            self.render(
                '{{ image(myimage, "width-200|jpegquality-40") }}',
                {"myimage": self.image},
            ),
            '<img alt="Test image" src="{}" width="200" height="150">'.format(
                get_test_image_filename(self.image, "width-200.jpegquality-40")
            ),
        )


class TestImageURLJinja(JinjaImagesTestCase):
    def test_image_url(self):
        self.assertRegex(
            self.render(
                '{{ image_url(myimage, "width-200") }}', {"myimage": self.image}
            ),
            "/images/.*/width-200/{}".format(self.image.file.name.split("/")[-1]),
        )

    def test_image_url_custom_view(self):
        self.assertRegex(
            self.render(
                '{{ image_url(myimage, "width-200", "wagtailimages_serve_custom_view") }}',
                {"myimage": self.image},
            ),
            "/testimages/custom_view/.*/width-200/{}".format(
                self.image.file.name.split("/")[-1]
            ),
        )


class TestSrcsetImageJinja(JinjaImagesTestCase):
    def test_srcset_image(self):
        filename_200 = get_test_image_filename(self.image, "width-200")
        filename_400 = get_test_image_filename(self.image, "width-400")
        rendered = self.render(
            '{{ srcset_image(myimage, "width-{200,400}", sizes="100vw") }}',
            {"myimage": self.image},
        )
        expected = f"""
            <img
                sizes="100vw"
                src="{filename_200}"
                srcset="{filename_200} 200w, {filename_400} 400w"
                alt="Test image"
                width="200"
                height="150"
            >
        """
        self.assertHTMLEqual(rendered, expected)

    def test_srcset_output_single_image(self):
        self.assertHTMLEqual(
            self.render(
                '{{ srcset_image(myimage, "width-200") }}',
                {"myimage": self.image},
            ),
            self.render(
                '{{ image(myimage, "width-200") }}',
                {"myimage": self.image},
            ),
        )

    def test_srcset_image_assignment(self):
        template = (
            '{% set bg=srcset_image(myimage, "width-{200,400}") %}'
            "width: {{ bg.renditions[0].width }}, url: {{ bg.renditions[0].url }} "
            "width: {{ bg.renditions[1].width }}, url: {{ bg.renditions[1].url }} "
        )
        rendered = self.render(template, {"myimage": self.image})
        expected = f"""
            width: 200, url: {get_test_image_filename(self.image, "width-200")}
            width: 400, url: {get_test_image_filename(self.image, "width-400")}
        """
        self.assertHTMLEqual(rendered, expected)

    def test_srcset_image_assignment_render_as_is(self):
        filename_200 = get_test_image_filename(self.image, "width-200")
        filename_400 = get_test_image_filename(self.image, "width-400")
        rendered = self.render(
            '{% set bg=srcset_image(myimage, "width-{200,400}") %}{{ bg }}',
            {"myimage": self.image},
        )
        expected = f"""
            <img
                src="{filename_200}"
                srcset="{filename_200} 200w, {filename_400} 400w"
                alt="Test image"
                width="200"
                height="150"
            >
        """
        self.assertHTMLEqual(rendered, expected)

    def test_missing_srcset_image(self):
        rendered = self.render(
            '{{ srcset_image(myimage, "width-{200,400}", sizes="100vw") }}',
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

    def test_invalid_character(self):
        with self.assertRaisesRegex(
            TemplateSyntaxError, "filter specs in 'srcset_image' tag may only"
        ):
            self.render(
                '{{ srcset_image(myimage, "fill-{20×20,40×40}", sizes="100vw") }}',
                {"myimage": self.image},
            )

    def test_custom_default_attrs(self):
        with unittest.mock.patch.object(
            apps.get_app_config("wagtailimages"),
            "default_attrs",
            new={"decoding": "async", "loading": "lazy"},
        ):
            rendered = self.render(
                '{{ srcset_image(myimage, "width-{20,40}", sizes="100vw") }}',
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
                    decoding="async"
                    loading="lazy"
                >
            """
            self.assertHTMLEqual(rendered, expected)

    def test_chaining_filterspecs(self):
        filenames = [
            get_test_image_filename(self.image, "width-200.jpegquality-40"),
            get_test_image_filename(self.image, "width-400.jpegquality-40"),
        ]
        rendered = self.render(
            '{{ srcset_image(myimage, "width-{200,400}|jpegquality-40", sizes="100vw") }}',
            {"myimage": self.image},
        )
        expected = f"""
            <img
                sizes="100vw"
                src="{filenames[0]}"
                srcset="{filenames[0]} 200w, {filenames[1]} 400w"
                alt="Test image"
                width="200"
                height="150"
            >
        """
        self.assertHTMLEqual(rendered, expected)
