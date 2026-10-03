from django.test import TestCase

from wagtail.api.v3.tests.base import TestV3Base
from wagtail.images import get_image_model
from wagtail.images.tests.utils import get_test_image_file
from wagtail.test.utils import WagtailTestUtils
from wagtail.test.utils.wagtail_factories import CollectionFactory

Image = get_image_model()


class TestV3ImagesBase(TestV3Base, WagtailTestUtils, TestCase):
    def create_image(self, **kwargs):
        defaults = {
            "title": "Test image",
            "file": get_test_image_file(),
        }
        defaults.update(kwargs)
        return Image.objects.create(**defaults)

    def create_collection(self, name="Test collection", parent=None):
        return CollectionFactory.create(name=name, parent=parent)
