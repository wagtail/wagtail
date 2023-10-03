import os
import unittest

from django import forms, template
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile
from django.test import TestCase, override_settings
from django.test.signals import setting_changed
from django.urls import reverse
from taggit.forms import TagField, TagWidget
from willow.image import ImageFile as WillowImageFile

from wagtail.images import get_image_model, get_image_model_string
from wagtail.images.fields import WagtailImageField
from wagtail.images.formats import Format, get_image_format, register_image_format
from wagtail.images.forms import get_image_form
from wagtail.images.models import Image as WagtailImage
from wagtail.images.permissions import update_permission_policy
from wagtail.images.rect import Rect, Vector
from wagtail.images.utils import generate_signature, verify_signature
from wagtail.images.views.serve import ServeView
from wagtail.test.testapp.models import CustomImage, CustomImageFilePath
from wagtail.test.utils import WagtailTestUtils, disconnect_signal_receiver
from wagtail.utils.deprecation import RemovedInWagtail60Warning

from .utils import (
    Image,
    get_test_image_file,
    get_test_image_file_avif,
    get_test_image_file_svg,
)

try:
    import sendfile  # noqa: F401

    sendfile_mod = True
except ImportError:
    sendfile_mod = False


class TestImageTag(TestCase):
    def setUp(self):
        # Create an image for running tests on
        self.image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(),
        )

    def render_image_tag(self, image, filter_spec):
        temp = template.Template(
            "{% load wagtailimages_tags %}{% image image_obj " + filter_spec + "%}"
        )
        context = template.Context({"image_obj": image})
        return temp.render(context)

    def test_image_tag(self):
        result = self.render_image_tag(self.image, "width-400")

        # Check that all the required HTML attributes are set
        self.assertIn('width="400"', result)
        self.assertIn('height="300"', result)
        self.assertIn('alt="Test image"', result)

    def test_image_tag_none(self):
        result = self.render_image_tag(None, "width-500")
        self.assertEqual(result, "")

    def test_image_tag_wrong_type(self):
        with self.assertRaises(ValueError):
            self.render_image_tag("foobar", "width-500")

    def render_image_tag_as(self, image, filter_spec):
        temp = template.Template(
            "{% load wagtailimages_tags %}{% image image_obj "
            + filter_spec
            + " as test_img %}<img {{ test_img.attrs }} />"
        )
        context = template.Context({"image_obj": image})
        return temp.render(context)

    def test_image_tag_attrs(self):
        result = self.render_image_tag_as(self.image, "width-400")

        # Check that all the required HTML attributes are set
        self.assertIn('width="400"', result)
        self.assertIn('height="300"', result)
        self.assertIn('alt="Test image"', result)

    def render_image_tag_with_extra_attributes(self, image, title):
        temp = template.Template(
            '{% load wagtailimages_tags %}{% image image_obj width-400 \
            class="photo" title=title|lower alt="Alternate" %}'
        )
        context = template.Context({"image_obj": image, "title": title})
        return temp.render(context)

    def test_image_tag_with_extra_attributes(self):
        result = self.render_image_tag_with_extra_attributes(
            self.image, "My Wonderful Title"
        )

        # Check that all the required HTML attributes are set
        self.assertIn('width="400"', result)
        self.assertIn('height="300"', result)
        self.assertIn('class="photo"', result)
        self.assertIn('alt="Alternate"', result)
        self.assertIn('title="my wonderful title"', result)

    def render_image_tag_with_filters(self, image):
        temp = template.Template(
            "{% load wagtailimages_tags %}{% image image_primary|default:image_alternate width-400 %}"
        )
        context = template.Context({"image_primary": None, "image_alternate": image})
        return temp.render(context)

    def test_image_tag_with_filters(self):
        result = self.render_image_tag_with_filters(self.image)
        self.assertIn('width="400"', result)
        self.assertIn('height="300"', result)

    def test_image_tag_with_chained_filters(self):
        result = self.render_image_tag(self.image, "fill-200x200 height-150")
        self.assertIn('width="150"', result)
        self.assertIn('height="150"', result)

    def test_filter_specs_must_match_allowed_pattern(self):
        with self.assertRaises(template.TemplateSyntaxError):
            self.render_image_tag(self.image, "fill-200x200|height-150")

        with self.assertRaises(template.TemplateSyntaxError):
            self.render_image_tag(self.image, 'fill-800x600 alt"test"')

    def test_context_may_only_contain_one_argument(self):
        with self.assertRaises(template.TemplateSyntaxError):
            temp = template.Template(
                "{% load wagtailimages_tags %}{% image image_obj fill-200x200"
                " as test_img this_one_should_not_be_there %}<img {{ test_img.attrs }} />"
            )
            context = template.Context({"image_obj": self.image})
            temp.render(context)

    def test_no_image_filter_provided(self):
        # if image template gets the image but no filters
        with self.assertRaises(template.TemplateSyntaxError):
            temp = template.Template(
                "{% load wagtailimages_tags %}{% image image_obj %}"
            )
            context = template.Context({"image_obj": self.image})
            temp.render(context)

    def test_no_image_filter_provided_when_using_as(self):
        # if image template gets the image but no filters
        with self.assertRaises(template.TemplateSyntaxError):
            temp = template.Template(
                "{% load wagtailimages_tags %}{% image image_obj as foo %}"
            )
            context = template.Context({"image_obj": self.image})
            temp.render(context)

    def test_no_image_filter_provided_but_attributes_provided(self):
        # if image template gets the image but no filters
        with self.assertRaises(template.TemplateSyntaxError):
            temp = template.Template(
                '{% load wagtailimages_tags %}{% image image_obj class="cover-image"%}'
            )
            context = template.Context({"image_obj": self.image})
            temp.render(context)

    def render_image_url_tag(self, image, view_name):
        temp = template.Template(
            '{% load wagtailimages_tags %}{% image_url image_obj "width-400" "'
            + view_name
            + '" %}'
        )
        context = template.Context({"image_obj": image})
        return temp.render(context)

    def test_image_url(self):
        result = self.render_image_url_tag(self.image, "wagtailimages_serve")
        self.assertRegex(
            result,
            "/images/.*/width-400/{}".format(self.image.file.name.split("/")[-1]),
        )

    def test_image_url_custom_view(self):
        result = self.render_image_url_tag(
            self.image, "wagtailimages_serve_custom_view"
        )

        self.assertRegex(
            result,
            "/testimages/custom_view/.*/width-400/{}".format(
                self.image.file.name.split("/")[-1]
            ),
        )

    def test_image_url_no_imageserve_view_added(self):
        # if image_url tag is used, but the image serve view was not defined.
        with self.assertRaises(ImproperlyConfigured):
            temp = template.Template(
                '{% load wagtailimages_tags %}{% image_url image_obj "width-400" "mynonexistingimageserve_view" %}'
            )
            context = template.Context({"image_obj": self.image})
            temp.render(context)


class TestMissingImage(TestCase):
    """
    Missing image files in media/original_images should be handled gracefully, to cope with
    pulling live databases to a development instance without copying the corresponding image files.
    In this case, it's acceptable to render broken images, but not to fail rendering the page outright.
    """

    fixtures = ["test.json"]

    def test_image_tag_with_missing_image(self):
        # the page /events/christmas/ has a missing image as the feed image
        response = self.client.get("/events/christmas/")
        self.assertContains(
            response,
            '<img src="/media/not-found" width="0" height="0" alt="A missing image" \
            class="feed-image">',
            html=True,
        )

    def test_rich_text_with_missing_image(self):
        # the page /events/final-event/ has a missing image in the rich text body
        response = self.client.get("/events/final-event/")
        self.assertContains(
            response,
            '<img class="richtext-image full-width" src="/media/not-found" \
            width="0" height="0" alt="where did my image go?">',
            html=True,
        )


class TestFormat(WagtailTestUtils, TestCase):
    def setUp(self):
        # test format
        self.format = Format("test name", "test label", "test is-primary", "original")
        # test image
        self.image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(),
        )

    def test_editor_attributes(self):
        result = self.format.editor_attributes(self.image, "test alt text")
        self.assertEqual(
            result,
            {
                "data-alt": "test alt text",
                "data-embedtype": "image",
                "data-format": "test name",
                "data-id": self.image.pk,
            },
        )

    def test_image_to_editor_html(self):
        result = self.format.image_to_editor_html(self.image, "test alt text")
        self.assertTagInHTML(
            '<img data-embedtype="image" data-id="%d" data-format="test name" '
            'data-alt="test alt text" class="test is-primary" '
            'width="640" height="480" alt="test alt text" >' % self.image.pk,
            result,
            allow_extra_attrs=True,
        )

    def test_image_to_editor_html_with_quoting(self):
        result = self.format.image_to_editor_html(
            self.image, 'Arthur "two sheds" Jackson'
        )
        expected_html = (
            '<img data-embedtype="image" data-id="%d" data-format="test name" '
            'data-alt="Arthur &quot;two sheds&quot; Jackson" class="test is-primary" '
            'width="640" height="480" alt="Arthur &quot;two sheds&quot; Jackson" >'
            % self.image.pk
        )
        self.assertTagInHTML(expected_html, result, allow_extra_attrs=True)

    def test_image_to_html_no_classnames(self):
        self.format.classname = None
        result = self.format.image_to_html(self.image, "test alt text")
        self.assertTagInHTML(
            '<img width="640" height="480" alt="test alt text">',
            result,
            allow_extra_attrs=True,
        )
        self.format.classname = (
            "test is-primary"  # reset to original value for other tests
        )

    def test_image_to_html_with_quoting(self):
        result = self.format.image_to_html(self.image, 'Arthur "two sheds" Jackson')
        self.assertTagInHTML(
            '<img class="test is-primary" width="640" height="480" '
            'alt="Arthur &quot;two sheds&quot; Jackson">',
            result,
            allow_extra_attrs=True,
        )

    def test_get_image_format(self):
        register_image_format(self.format)
        result = get_image_format("test name")
        self.assertEqual(result, self.format)

    def test_deprecated_classnames_property_access(self):
        with self.assertWarns(RemovedInWagtail60Warning):
            classname = self.format.classnames
        self.assertEqual(classname, "test is-primary")


class TestSignatureGeneration(TestCase):
    def test_signature_generation(self):
        self.assertEqual(
            generate_signature(100, "fill-800x600"), "xnZOzQyUg6pkfciqcfRJRosOrGg="
        )

    def test_signature_verification(self):
        self.assertTrue(
            verify_signature("xnZOzQyUg6pkfciqcfRJRosOrGg=", 100, "fill-800x600")
        )

    def test_signature_changes_on_image_id(self):
        self.assertFalse(
            verify_signature("xnZOzQyUg6pkfciqcfRJRosOrGg=", 200, "fill-800x600")
        )

    def test_signature_changes_on_filter_spec(self):
        self.assertFalse(
            verify_signature("xnZOzQyUg6pkfciqcfRJRosOrGg=", 100, "fill-800x700")
        )


class TestFrontendServeView(TestCase):
    def setUp(self):
        # Create an image for running tests on
        self.image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(),
        )

    def test_get(self):
        """
        Test a valid GET request to the view
        """
        # Generate signature
        signature = generate_signature(self.image.id, "fill-800x600")

        # Get the image
        response = self.client.get(
            reverse(
                "wagtailimages_serve", args=(signature, self.image.id, "fill-800x600")
            )
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.streaming)
        self.assertEqual(response["Content-Type"], "image/png")

    def test_get_svg(self):
        image = Image.objects.create(title="Test SVG", file=get_test_image_file_svg())

        # Generate signature
        signature = generate_signature(image.id, "fill-800x600")

        # Get the image
        response = self.client.get(
            reverse("wagtailimages_serve", args=(signature, image.id, "fill-800x600"))
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.streaming)
        self.assertEqual(response["Content-Type"], "image/svg+xml")

    @override_settings(WAGTAILIMAGES_FORMAT_CONVERSIONS={"avif": "avif"})
    def test_get_avif(self):
        image = Image.objects.create(title="Test AVIF", file=get_test_image_file_avif())

        # Generate signature
        signature = generate_signature(image.id, "fill-800x600")

        # Get the image
        response = self.client.get(
            reverse("wagtailimages_serve", args=(signature, image.id, "fill-800x600"))
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.streaming)
        self.assertEqual(response["Content-Type"], "image/avif")

    def test_get_with_extra_component(self):
        """
        Test that a filename can be optionally added to the end of the URL.
        """
        # Generate signature
        signature = generate_signature(self.image.id, "fill-800x600")

        # Get the image
        response = self.client.get(
            reverse(
                "wagtailimages_serve", args=(signature, self.image.id, "fill-800x600")
            )
            + "test.png"
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.streaming)
        self.assertEqual(response["Content-Type"], "image/png")

    def test_get_with_too_many_extra_components(self):
        """
        A filename can be appended to the end of the URL, but it must not contain a '/'
        """
        # Generate signature
        signature = generate_signature(self.image.id, "fill-800x600")

        # Get the image
        response = self.client.get(
            reverse(
                "wagtailimages_serve", args=(signature, self.image.id, "fill-800x600")
            )
            + "test/test.png"
        )

        # URL pattern should not match
        self.assertEqual(response.status_code, 404)

    def test_get_with_serve_action(self):
        signature = generate_signature(self.image.id, "fill-800x600")
        response = self.client.get(
            reverse(
                "wagtailimages_serve_action_serve",
                args=(signature, self.image.id, "fill-800x600"),
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.streaming)
        self.assertEqual(response["Content-Type"], "image/png")

    def test_get_with_redirect_action(self):
        signature = generate_signature(self.image.id, "fill-800x600")
        response = self.client.get(
            reverse(
                "wagtailimages_serve_action_redirect",
                args=(signature, self.image.id, "fill-800x600"),
            )
        )

        expected_redirect_url = (
            "/media/images/{filename[0]}.2e16d0ba.fill-800x600{filename[1]}".format(
                filename=os.path.splitext(os.path.basename(self.image.file.path))
            )
        )

        self.assertRedirects(
            response,
            expected_redirect_url,
            status_code=302,
            fetch_redirect_response=False,
        )

    def test_init_with_unknown_action_raises_error(self):
        with self.assertRaises(ImproperlyConfigured):
            ServeView.as_view(action="unknown")

    def test_get_with_custom_key(self):
        """
        Test that that the key can be changed on the view
        """
        # Generate signature
        signature = generate_signature(self.image.id, "fill-800x600", key="custom")

        # Get the image
        response = self.client.get(
            reverse(
                "wagtailimages_serve_custom_key",
                args=(signature, self.image.id, "fill-800x600"),
            )
            + "test.png"
        )

        # Check response
        self.assertEqual(response.status_code, 200)

    def test_get_with_custom_key_using_default_key(self):
        """
        Test that that the key can be changed on the view

        This tests that the default key no longer works when the key is changed on the view
        """
        # Generate signature
        signature = generate_signature(self.image.id, "fill-800x600")

        # Get the image
        response = self.client.get(
            reverse(
                "wagtailimages_serve_custom_key",
                args=(signature, self.image.id, "fill-800x600"),
            )
            + "test.png"
        )

        # Check response
        self.assertEqual(response.status_code, 403)

    def test_get_invalid_signature(self):
        """
        Test that an invalid signature returns a 403 response
        """
        # Generate a signature for the incorrect image id
        signature = generate_signature(self.image.id + 1, "fill-800x600")

        # Get the image
        response = self.client.get(
            reverse(
                "wagtailimages_serve", args=(signature, self.image.id, "fill-800x600")
            )
        )

        # Check response
        self.assertEqual(response.status_code, 403)

    def test_get_invalid_filter_spec(self):
        """
        Test that an invalid filter spec returns a 400 response

        This is very unlikely to happen in reality. A user would have
        to create signature for the invalid filter spec which can't be
        done with Wagtails built in URL generator. We should test it
        anyway though.
        """
        # Generate a signature with the invalid filterspec
        signature = generate_signature(self.image.id, "bad-filter-spec")

        # Get the image
        response = self.client.get(
            reverse(
                "wagtailimages_serve",
                args=(signature, self.image.id, "bad-filter-spec"),
            )
        )

        # Check response
        self.assertEqual(response.status_code, 400)

    def test_get_missing_source_image_file(self):
        """
        Test that a missing image file gives a 410 response

        When the source image file is missing, it is presumed deleted so we
        return a 410 "Gone" response.
        """
        # Delete the image file
        os.remove(self.image.file.path)

        # Get the image
        signature = generate_signature(self.image.id, "fill-800x600")
        response = self.client.get(
            reverse(
                "wagtailimages_serve", args=(signature, self.image.id, "fill-800x600")
            )
        )

        # Check response
        self.assertEqual(response.status_code, 410)

    def test_get_cache_control(self):
        signature = generate_signature(self.image.id, "fill-800x600")
        response = self.client.get(
            reverse(
                "wagtailimages_serve_action_serve",
                args=(signature, self.image.id, "fill-800x600"),
            )
        )
        self.assertEqual(response["Cache-Control"], "max-age=3600, public")


class TestFrontendSendfileView(TestCase):
    def setUp(self):
        self.image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(),
        )

    @override_settings(SENDFILE_BACKEND="sendfile.backends.development")
    @unittest.skipIf(not sendfile_mod, "Missing django-sendfile app.")
    def test_sendfile_nobackend(self):
        signature = generate_signature(self.image.id, "fill-800x600")
        response = self.client.get(
            reverse(
                "wagtailimages_sendfile",
                args=(signature, self.image.id, "fill-800x600"),
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/png")

    @override_settings(SENDFILE_BACKEND="sendfile.backends.development")
    def test_sendfile_dummy_backend(self):
        signature = generate_signature(self.image.id, "fill-800x600")
        response = self.client.get(
            reverse(
                "wagtailimages_sendfile_dummy",
                args=(signature, self.image.id, "fill-800x600"),
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content, msg="Dummy backend response")


class TestRect(TestCase):
    def test_init(self):
        rect = Rect(100, 150, 200, 250)
        self.assertEqual(rect.left, 100)
        self.assertEqual(rect.top, 150)
        self.assertEqual(rect.right, 200)
        self.assertEqual(rect.bottom, 250)

    def test_equality(self):
        self.assertEqual(Rect(100, 150, 200, 250), Rect(100, 150, 200, 250))
        self.assertNotEqual(Rect(100, 150, 200, 250), Rect(10, 15, 20, 25))

    def test_getitem(self):
        rect = Rect(100, 150, 200, 250)
        self.assertEqual(rect[0], 100)
        self.assertEqual(rect[1], 150)
        self.assertEqual(rect[2], 200)
        self.assertEqual(rect[3], 250)
        self.assertRaises(IndexError, rect.__getitem__, 4)

    def test_as_tuple(self):
        rect = Rect(100, 150, 200, 250)
        self.assertEqual(rect.as_tuple(), (100, 150, 200, 250))

    def test_size(self):
        rect = Rect(100, 150, 200, 350)
        self.assertIsInstance(rect.size, Vector)
        self.assertEqual(rect.size, (100, 200))
        self.assertEqual(rect.width, 100)
        self.assertEqual(rect.height, 200)

    def test_set_size_with_tuple(self):
        rect = Rect(100, 150, 200, 350)
        rect.size = (200, 400)
        self.assertEqual(rect, (50, 50, 250, 450))

    def test_set_size_with_vector(self):
        rect = Rect(100, 150, 200, 350)
        rect.size = Vector(200, 400)
        self.assertEqual(rect, (50, 50, 250, 450))

    def test_centroid(self):
        rect = Rect(100, 150, 200, 350)
        self.assertIsInstance(rect.centroid, Vector)
        self.assertEqual(rect.centroid, (150, 250))
        self.assertEqual(rect.x, 150)
        self.assertEqual(rect.y, 250)
        self.assertEqual(rect.centroid_x, 150)
        self.assertEqual(rect.centroid_y, 250)

    def test_set_centroid_with_tuple(self):
        rect = Rect(100, 150, 200, 350)
        rect.centroid = (500, 500)
        self.assertEqual(rect, (450, 400, 550, 600))

    def test_set_centroid_with_vector(self):
        rect = Rect(100, 150, 200, 350)
        rect.centroid = Vector(500, 500)
        self.assertEqual(rect, (450, 400, 550, 600))

    def test_repr(self):
        rect = Rect(100, 150, 200, 250)
        self.assertEqual(
            repr(rect), "Rect(left: 100, top: 150, right: 200, bottom: 250)"
        )

    def test_from_point(self):
        rect = Rect.from_point(100, 200, 50, 20)
        self.assertEqual(rect, Rect(75, 190, 125, 210))


class TestGetImageForm(WagtailTestUtils, TestCase):
    def test_fields(self):
        form = get_image_form(Image)

        self.assertEqual(
            list(form.base_fields.keys()),
            [
                "title",
                "file",
                "collection",
                "tags",
                "focal_point_x",
                "focal_point_y",
                "focal_point_width",
                "focal_point_height",
            ],
        )

    def test_admin_form_fields_attribute(self):
        form = get_image_form(CustomImage)

        self.assertEqual(
            list(form.base_fields.keys()),
            [
                "title",
                "file",
                "collection",
                "tags",
                "focal_point_x",
                "focal_point_y",
                "focal_point_width",
                "focal_point_height",
                "caption",
                "fancy_caption",
            ],
        )

    def test_file_field(self):
        form = get_image_form(WagtailImage)

        self.assertIsInstance(form.base_fields["file"], WagtailImageField)
        self.assertIsInstance(form.base_fields["file"].widget, forms.FileInput)

    def test_tags_field(self):
        form = get_image_form(WagtailImage)

        self.assertIsInstance(form.base_fields["tags"], TagField)
        self.assertIsInstance(form.base_fields["tags"].widget, TagWidget)

    def test_focal_point_fields(self):
        form = get_image_form(WagtailImage)

        self.assertIsInstance(form.base_fields["focal_point_x"], forms.IntegerField)
        self.assertIsInstance(form.base_fields["focal_point_y"], forms.IntegerField)
        self.assertIsInstance(form.base_fields["focal_point_width"], forms.IntegerField)
        self.assertIsInstance(
            form.base_fields["focal_point_height"], forms.IntegerField
        )

        self.assertIsInstance(
            form.base_fields["focal_point_x"].widget, forms.HiddenInput
        )
        self.assertIsInstance(
            form.base_fields["focal_point_y"].widget, forms.HiddenInput
        )
        self.assertIsInstance(
            form.base_fields["focal_point_width"].widget, forms.HiddenInput
        )
        self.assertIsInstance(
            form.base_fields["focal_point_height"].widget, forms.HiddenInput
        )


class TestRenditionFilenames(TestCase):
    # Can't create image in setUp as we need a unique filename for each test.
    # This stops Django appending some rubbish to the filename which makes
    # the assertions difficult.

    def test_normal_filter(self):
        image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(filename="test_rf1.png"),
        )
        rendition = image.get_rendition("width-100")

        self.assertEqual(rendition.file.name, "images/test_rf1.width-100.png")

    def test_fill_filter(self):
        image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(filename="test_rf2.png"),
        )
        rendition = image.get_rendition("fill-100x100")

        self.assertEqual(
            rendition.file.name, "images/test_rf2.2e16d0ba.fill-100x100.png"
        )

    def test_fill_filter_with_focal_point(self):
        image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(filename="test_rf3.png"),
        )
        image.set_focal_point(Rect(100, 100, 200, 200))
        image.save()

        rendition = image.get_rendition("fill-100x100")

        self.assertEqual(
            rendition.file.name, "images/test_rf3.15ee4958.fill-100x100.png"
        )

    def test_filter_with_pipe_gets_dotted(self):
        image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(filename="test_rf4.png"),
        )
        image.set_focal_point(Rect(100, 100, 200, 200))
        image.save()

        rendition = image.get_rendition("fill-200x200|height-150")

        self.assertEqual(
            rendition.file.name, "images/test_rf4.15ee4958.fill-200x200.height-150.png"
        )


class TestDifferentUpload(TestCase):
    def test_upload_path(self):
        image = CustomImageFilePath.objects.create(
            title="Test image",
            file=get_test_image_file(),
        )

        second_image = CustomImageFilePath.objects.create(
            title="Test Image",
            file=get_test_image_file(colour="black"),
        )

        # The files should be uploaded based on it's content, not just
        # it's filename
        self.assertNotEqual(image.file.url, second_image.file.url)


class TestGetImageModel(WagtailTestUtils, TestCase):
    @override_settings(WAGTAILIMAGES_IMAGE_MODEL="tests.CustomImage")
    def test_custom_get_image_model(self):
        """Test get_image_model with a custom image model"""
        self.assertIs(get_image_model(), CustomImage)

    @override_settings(WAGTAILIMAGES_IMAGE_MODEL="tests.CustomImage")
    def test_custom_get_image_model_string(self):
        """Test get_image_model_string with a custom image model"""
        self.assertEqual(get_image_model_string(), "tests.CustomImage")

    @override_settings()
    def test_standard_get_image_model(self):
        """Test get_image_model with no WAGTAILIMAGES_IMAGE_MODEL"""
        del settings.WAGTAILIMAGES_IMAGE_MODEL
        from wagtail.images.models import Image

        self.assertIs(get_image_model(), Image)

    @override_settings()
    def test_standard_get_image_model_string(self):
        """Test get_image_model_STRING with no WAGTAILIMAGES_IMAGE_MODEL"""
        del settings.WAGTAILIMAGES_IMAGE_MODEL
        self.assertEqual(get_image_model_string(), "wagtailimages.Image")

    @disconnect_signal_receiver(
        signal=setting_changed, receiver=update_permission_policy
    )
    @override_settings(WAGTAILIMAGES_IMAGE_MODEL="tests.UnknownModel")
    def test_unknown_get_image_model(self):
        """Test get_image_model with an unknown model"""
        with self.assertRaises(ImproperlyConfigured):
            get_image_model()

    @disconnect_signal_receiver(
        signal=setting_changed, receiver=update_permission_policy
    )
    @override_settings(WAGTAILIMAGES_IMAGE_MODEL="invalid-string")
    def test_invalid_get_image_model(self):
        """Test get_image_model with an invalid model string"""
        with self.assertRaises(ImproperlyConfigured):
            get_image_model()


class TestWagtailImageField(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.filename = "wagtailimagefield.png"
        cls.image = get_test_image_file(filename=cls.filename).file
        cls.image_size = cls.image.getbuffer().nbytes

    def test_to_python_with_inmemoryfile(self):
        f = WagtailImageField()
        self.image.seek(0)
        file = InMemoryUploadedFile(
            self.image, "", self.filename, "image/png", self.image_size, None
        )
        to_python = f.to_python(file)
        self.assertIsInstance(to_python.image, WillowImageFile)
        self.assertEqual(to_python.content_type, "image/png")

    def test_to_python_gets_content_type_from_willow(self):
        f = WagtailImageField()
        self.image.seek(0)
        file = InMemoryUploadedFile(
            self.image, "", self.filename, "image/jpeg", self.image_size, None
        )
        to_python = f.to_python(file)
        self.assertIsInstance(to_python.image, WillowImageFile)
        self.assertEqual(to_python.content_type, "image/png")

    def test_to_python_with_temporary_file(self):
        f = WagtailImageField()
        with TemporaryUploadedFile(
            "test_temp.png", "image/png", self.image_size, None
        ) as tmp_file:
            self.image.seek(0)
            tmp_file.write(self.image.read())
            tmp_file.seek(0)

            to_python = f.to_python(tmp_file)
            self.assertIsInstance(to_python.image, WillowImageFile)
            self.assertEqual(to_python.content_type, "image/png")

    def test_to_python_raises_error_with_invalid_image_file(self):
        msg = (
            "Upload a valid image. The file you uploaded was either not an "
            "image or a corrupted image."
        )
        f = WagtailImageField()
        with TemporaryUploadedFile("test_temp.png", "image/png", 32, None) as tmp_file:
            with self.assertRaisesMessage(ValidationError, msg):
                f.to_python(tmp_file)

        with self.assertRaisesMessage(
            ValidationError,
            "No file was submitted. Check the encoding type on the form.",
        ):
            f.to_python(self.image)
