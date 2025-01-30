import os
import unittest
from io import BytesIO

import willow
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase, override_settings
from django.urls import reverse
from willow.image import (
    AvifImageFile,
    PNGImageFile,
    SvgImageFile,
)

from wagtail.images.utils import generate_signature, verify_signature
from wagtail.images.views.serve import ServeView

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


class TestServeView(TestCase):
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
        self.assertEqual(response["Content-Security-Policy"], "default-src 'none'")
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")
        # Ensure the file can actually be read
        image = willow.Image.open(b"".join(response.streaming_content))
        self.assertIsInstance(image, PNGImageFile)

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
        self.assertEqual(response["Content-Security-Policy"], "default-src 'none'")
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")
        # Ensure the file can actually be read
        image = willow.Image.open(BytesIO(b"".join(response.streaming_content)))
        self.assertIsInstance(image, SvgImageFile)

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
        # Ensure the file can actually be read
        image = willow.Image.open(b"".join(response.streaming_content))
        self.assertIsInstance(image, AvifImageFile)

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
        # Ensure the file can actually be read
        image = willow.Image.open(b"".join(response.streaming_content))
        self.assertIsInstance(image, PNGImageFile)

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
        self.assertEqual(response["Content-Security-Policy"], "default-src 'none'")
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")
        # Ensure the file can actually be read
        image = willow.Image.open(b"".join(response.streaming_content))
        self.assertIsInstance(image, PNGImageFile)

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
        Test that the key can be changed on the view
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

        # Ensure the file can actually be read
        image = willow.Image.open(b"".join(response.streaming_content))
        self.assertIsInstance(image, PNGImageFile)

        # Check cache control headers
        self.assertEqual(
            response["Cache-Control"], "max-age=3600, s_maxage=3600, public"
        )

    def test_get_with_custom_key_using_default_key(self):
        """
        Test that the key can be changed on the view

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
        self.assertContains(response, "Invalid signature", status_code=400)

    def test_get_invalid_signature(self):
        """
        Test that an invalid signature returns a 400 response
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
        self.assertContains(response, "Invalid signature", status_code=400)

        # Check cache control headers
        self.assertEqual(
            response["Cache-Control"], "max-age=3600, s_maxage=3600, public"
        )

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
        self.assertContains(response, "Invalid filter spec: bad-filter-spec", status_code=400)

        # Check cache control headers
        self.assertEqual(
            response["Cache-Control"], "max-age=3600, s_maxage=3600, public"
        )

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
        self.assertContains(response, "Source image file not found", status_code=410)

        # Check cache control headers
        self.assertEqual(
            response["Cache-Control"], "max-age=3600, s_maxage=3600, public"
        )


class TestSendFileView(TestCase):
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
        self.assertEqual(response["Content-Security-Policy"], "default-src 'none'")
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")

        # Check cache control headers
        self.assertEqual(
            response["Cache-Control"], "max-age=3600, s_maxage=3600, public"
        )

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
        self.assertEqual(response["Content-Security-Policy"], "default-src 'none'")
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")

        # Check cache control headers
        self.assertEqual(
            response["Cache-Control"], "max-age=3600, s_maxage=3600, public"
        )
