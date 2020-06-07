from django.test import TestCase
from django.test.utils import override_settings
from rest_framework.renderers import BrowsableAPIRenderer, JSONRenderer

from wagtail.api.v2.utils import get_default_renderer_classes


class TestPageListing(TestCase):
    @override_settings(WAGTAILAPI_DEFAULT_RENDERER_CLASSES=[
        'rest_framework.renderers.JSONRenderer',
    ])
    def test_renderer_classes_override(self):
        renderer_classes = get_default_renderer_classes()
        self.assertEqual(len(renderer_classes), 1)
        self.assertEqual(renderer_classes[0], JSONRenderer)

    def test_default_renderer_classes_return_expected_value(self):
        renderer_classes = get_default_renderer_classes()
        self.assertEqual(renderer_classes, [
            JSONRenderer,
            BrowsableAPIRenderer,
        ])
