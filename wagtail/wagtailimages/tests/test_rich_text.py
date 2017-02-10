from __future__ import absolute_import, unicode_literals

from bs4 import BeautifulSoup
from django.test import TestCase

from wagtail.wagtailimages.rich_text import ImageEmbedHandler

from .utils import Image, get_test_image_file


class TestImageEmbedHandler(TestCase):
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

    def test_expand_db_attributes_page_does_not_exist(self):
        result = ImageEmbedHandler.expand_db_attributes(
            {'id': 0},
            False
        )
        self.assertEqual(result, '<img>')

    def test_expand_db_attributes_not_for_editor(self):
        Image.objects.create(id=1, title='Test', file=get_test_image_file())
        result = ImageEmbedHandler.expand_db_attributes(
            {'id': 1,
             'alt': 'test-alt',
             'format': 'left'},
            False
        )
        self.assertIn('<img class="richtext-image left"', result)

    def test_expand_db_attributes_for_editor(self):
        Image.objects.create(id=1, title='Test', file=get_test_image_file())
        result = ImageEmbedHandler.expand_db_attributes(
            {'id': 1,
             'alt': 'test-alt',
             'format': 'left'},
            True
        )
        self.assertIn(
            '<img data-embedtype="image" data-id="1" data-format="left" '
            'data-alt="test-alt" class="richtext-image left"', result
        )
