from __future__ import absolute_import, unicode_literals

import os

from django.test import TestCase, override_settings

from wagtail.wagtailimages import get_image_model, signal_handlers
from wagtail.wagtailimages.tests.utils import get_test_image_file


class TestSignalHandlers(TestCase):

    def test_image_signal_handlers(self):
        image = get_image_model().objects.create(title="Test Image", file=get_test_image_file())
        image_path = image.file.path
        image.delete()

        self.assertFalse(os.path.exists(image_path))

    @override_settings(WAGTAILIMAGES_IMAGE_MODEL='tests.CustomImage')
    def test_custom_image_signal_handlers(self):
        #: Sadly signal receivers only get connected when starting django.
        #: We will re-attach them here to mimic the django startup behavior
        #: and get the signals connected to our custom model..
        signal_handlers.register_signal_handlers()

        image = get_image_model().objects.create(title="Test CustomImage", file=get_test_image_file())
        image_path = image.file.path
        image.delete()

        self.assertFalse(os.path.exists(image_path))
