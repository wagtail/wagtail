from __future__ import absolute_import, unicode_literals

import os

from django.db import transaction
from django.test import TestCase, override_settings

from wagtail.wagtailimages import get_image_model, signal_handlers
from wagtail.wagtailimages.tests.utils import get_test_image_file


class ExpectedException(Exception):
    pass


class TestDefaultModelSignalHandlers(TestCase):

    def test_image_file_deleted(self):
        image = get_image_model().objects.create(title="Test Image", file=get_test_image_file())
        image_path = image.file.path
        
        self.assertTrue(os.path.exists(image_path))
        
        image.delete()

        self.assertFalse(os.path.exists(image_path))
    
    def test_image_file_not_deleted(self):
        image = get_image_model().objects.create(title="Test Image", file=get_test_image_file())
        file_name = image.file.name
        self.assertTrue(image.file.storage.exists(file_name))
        
        try:
            with transaction.atomic():
                image.delete()
                raise ExpectedException()
        except ExpectedException:
            pass
        
        self.assertTrue(image.file.storage.exists(file_name))
    
    def test_rendition_file_deleted(self):
        image = get_image_model().objects.create(title="Test Image", file=get_test_image_file())
        rendition = image.get_rendition('original')
        rendition_path = rendition.file.path
        
        self.assertTrue(os.path.exists(rendition_path))
        
        rendition.delete()

        self.assertFalse(os.path.exists(rendition_path))


@override_settings(WAGTAILIMAGES_IMAGE_MODEL='tests.CustomImage')
class TestCustomModelSignalHandlers(TestDefaultModelSignalHandlers):
    def setUp(self):
        #: Sadly signal receivers only get connected when starting django.
        #: We will re-attach them here to mimic the django startup behavior
        #: and get the signals connected to our custom model..
        signal_handlers.register_signal_handlers()
