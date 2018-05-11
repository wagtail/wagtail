from bs4 import BeautifulSoup
from django.test import TestCase

from wagtail.images.rich_text import ImageEmbedHandler, image_embedtype_handler
from wagtail.tests.utils import WagtailTestUtils

from .utils import Image, get_test_image_file


class TestImageEmbedHandler(TestCase, WagtailTestUtils):
    def test_get_db_attributes(self):
        soup = BeautifulSoup(
            '<b data-id="test-id" data-format="test-format" data-alt="test-alt">foo</b>',
            'html5lib'
        )
        tag = soup.b
        result = ImageEmbedHandler.get_db_attributes(tag)
        self.assertEqual(result,
                         {'alt': 'test-alt',
                          'id': 'test-id',
                          'format': 'test-format'})

    def test_expand_db_attributes_image_does_not_exist(self):
        result = image_embedtype_handler({'id': 0})
        self.assertEqual(result, '<img>')

    def test_expand_db_attributes_not_for_editor(self):
        Image.objects.create(id=1, title='Test', file=get_test_image_file())
        result = image_embedtype_handler(
            {'id': 1,
             'alt': 'test-alt',
             'format': 'left'}
        )
        self.assertTagInHTML('<img class="richtext-image left" />', result, allow_extra_attrs=True)

    def test_expand_db_attributes_escapes_alt_text(self):
        Image.objects.create(id=1, title='Test', file=get_test_image_file())
        result = image_embedtype_handler(
            {'id': 1,
             'alt': 'Arthur "two sheds" Jackson',
             'format': 'left'},
        )
        self.assertIn('alt="Arthur &quot;two sheds&quot; Jackson"', result)

    def test_expand_db_attributes_with_missing_alt(self):
        Image.objects.create(id=1, title='Test', file=get_test_image_file())
        result = image_embedtype_handler(
            {'id': 1,
             'format': 'left'},
        )
        self.assertTagInHTML('<img class="richtext-image left" alt="" />', result, allow_extra_attrs=True)

    def test_expand_db_attributes_for_editor(self):
        Image.objects.create(id=1, title='Test', file=get_test_image_file())
        result = ImageEmbedHandler.expand_db_attributes(
            {'id': 1,
             'alt': 'test-alt',
             'format': 'left'},
        )
        self.assertTagInHTML(
            '<img data-embedtype="image" data-id="1" data-format="left" '
            'data-alt="test-alt" class="richtext-image left" />', result, allow_extra_attrs=True)

    def test_expand_db_attributes_for_editor_escapes_alt_text(self):
        Image.objects.create(id=1, title='Test', file=get_test_image_file())
        result = ImageEmbedHandler.expand_db_attributes(
            {'id': 1,
             'alt': 'Arthur "two sheds" Jackson',
             'format': 'left'},
        )
        self.assertTagInHTML(
            '<img data-embedtype="image" data-id="1" data-format="left" '
            'data-alt="Arthur &quot;two sheds&quot; Jackson" class="richtext-image left" />',
            result, allow_extra_attrs=True)

        self.assertIn('alt="Arthur &quot;two sheds&quot; Jackson"', result)

    def test_expand_db_attributes_for_editor_with_missing_alt(self):
        Image.objects.create(id=1, title='Test', file=get_test_image_file())
        result = ImageEmbedHandler.expand_db_attributes(
            {'id': 1,
             'format': 'left'},
        )
        self.assertTagInHTML(
            '<img data-embedtype="image" data-id="1" data-format="left" data-alt="" '
            'class="richtext-image left" />', result, allow_extra_attrs=True)
