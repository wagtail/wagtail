from mock import patch

from django.test import TestCase

from wagtail.wagtailcore.rich_text import (
    ImageEmbedHandler,
    MediaEmbedHandler,
    PageLinkHandler,
    DocumentLinkHandler,
    DbWhitelister,
    extract_attrs,
    expand_db_html
)
from bs4 import BeautifulSoup


class TestImageEmbedHandler(TestCase):
    fixtures = ['wagtail/tests/fixtures/test.json']

    def test_get_db_attributes(self):
        soup = BeautifulSoup(
            '<b data-id="test-id" data-format="test-format" data-alt="test-alt">foo</b>'
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

    @patch('wagtail.wagtailimages.models.Image')
    @patch('django.core.files.File')
    def test_expand_db_attributes_not_for_editor(self, mock_file, mock_image):
        result = ImageEmbedHandler.expand_db_attributes(
            {'id': 1,
             'alt': 'test-alt',
             'format': 'left'},
            False
        )
        self.assertIn('<img class="richtext-image left"', result)

    @patch('wagtail.wagtailimages.models.Image')
    @patch('django.core.files.File')
    def test_expand_db_attributes_for_editor(self, mock_file, mock_image):
        result = ImageEmbedHandler.expand_db_attributes(
            {'id': 1,
             'alt': 'test-alt',
             'format': 'left'},
            True
        )
        self.assertIn('<img data-embedtype="image" data-id="1" data-format="left" data-alt="test-alt" class="richtext-image left"', result)

    @patch('wagtail.wagtailimages.models.Image')
    @patch('django.core.files.File')
    def test_expand_db_attributes_for_editor_throws_exception(self, mock_file, mock_image):
        result = ImageEmbedHandler.expand_db_attributes(
            {'id': 1,
             'format': 'left'},
            True
        )
        self.assertEqual(result, '')


class TestMediaEmbedHandler(TestCase):
    def test_get_db_attributes(self):
        soup = BeautifulSoup(
            '<b data-url="test-url">foo</b>'
        )
        tag = soup.b
        result = MediaEmbedHandler.get_db_attributes(tag)
        self.assertEqual(result,
                         {'url': 'test-url'})

    @patch('wagtail.wagtailembeds.embeds.oembed')
    def test_expand_db_attributes_for_editor(self, oembed):
        oembed.return_value = {
            'title': 'test title',
            'author_name': 'test author name',
            'provider_name': 'test provider name',
            'type': 'test type',
            'thumbnail_url': 'test thumbnail url',
            'width': 'test width',
            'height': 'test height',
            'html': 'test html'
        }
        result = MediaEmbedHandler.expand_db_attributes(
            {'url': 'http://www.youtube.com/watch/'},
            True
        )
        self.assertIn('<div class="embed-placeholder" contenteditable="false" data-embedtype="media" data-url="http://www.youtube.com/watch/">', result)
        self.assertIn('<h3>test title</h3>', result)
        self.assertIn('<p>URL: http://www.youtube.com/watch/</p>', result)
        self.assertIn('<p>Provider: test provider name</p>', result)
        self.assertIn('<p>Author: test author name</p>', result)
        self.assertIn('<img src="test thumbnail url" alt="test title">', result)

    @patch('wagtail.wagtailembeds.embeds.oembed')
    def test_expand_db_attributes_not_for_editor(self, oembed):
        oembed.return_value = {
            'title': 'test title',
            'author_name': 'test author name',
            'provider_name': 'test provider name',
            'type': 'test type',
            'thumbnail_url': 'test thumbnail url',
            'width': 'test width',
            'height': 'test height',
            'html': 'test html'
        }
        result = MediaEmbedHandler.expand_db_attributes(
            {'url': 'http://www.youtube.com/watch/'},
            False
        )
        self.assertIn('test html', result)


class TestPageLinkHandler(TestCase):
    fixtures = ['wagtail/tests/fixtures/test.json']

    def test_get_db_attributes(self):
        soup = BeautifulSoup(
            '<a data-id="test-id">foo</a>'
        )
        tag = soup.a
        result = PageLinkHandler.get_db_attributes(tag)
        self.assertEqual(result,
                         {'id': 'test-id'})

    def test_expand_db_attributes_page_does_not_exist(self):
        result = PageLinkHandler.expand_db_attributes(
            {'id': 0},
            False
        )
        self.assertEqual(result, '<a>')

    def test_expand_db_attributes_for_editor(self):
        result = PageLinkHandler.expand_db_attributes(
            {'id': 1},
            True
        )
        self.assertEqual(result,
                         '<a data-linktype="page" data-id="1" href="None">')

    def test_expand_db_attributes_not_for_editor(self):
        result = PageLinkHandler.expand_db_attributes(
            {'id': 1},
            False
        )
        self.assertEqual(result, '<a href="None">')


class TestDocumentLinkHandler(TestCase):
    fixtures = ['wagtail/tests/fixtures/test.json']

    def test_get_db_attributes(self):
        soup = BeautifulSoup(
            '<a data-id="test-id">foo</a>'
        )
        tag = soup.a
        result = DocumentLinkHandler.get_db_attributes(tag)
        self.assertEqual(result,
                         {'id': 'test-id'})

    def test_expand_db_attributes_document_does_not_exist(self):
        result = DocumentLinkHandler.expand_db_attributes(
            {'id': 0},
            False
        )
        self.assertEqual(result, '<a>')

    def test_expand_db_attributes_for_editor(self):
        result = DocumentLinkHandler.expand_db_attributes(
            {'id': 1},
            True
        )
        self.assertEqual(result,
                         '<a data-linktype="document" data-id="1" href="/documents/1/">')

    def test_expand_db_attributes_not_for_editor(self):
        result = DocumentLinkHandler.expand_db_attributes(
            {'id': 1},
            False
        )
        self.assertEqual(result,
                         '<a href="/documents/1/">')


class TestDbWhiteLister(TestCase):
    def test_clean_tag_node_div(self):
        soup = BeautifulSoup(
            '<div>foo</div>'
        )
        tag = soup.div
        self.assertEqual(tag.name, 'div')
        DbWhitelister.clean_tag_node(soup, tag)
        self.assertEqual(tag.name, 'p')

    def test_clean_tag_node_with_data_embedtype(self):
        soup = BeautifulSoup(
            '<p><a data-embedtype="image" data-id=1 data-format="left" data-alt="bar" irrelevant="baz">foo</a></p>'
        )
        tag = soup.p
        DbWhitelister.clean_tag_node(soup, tag)
        self.assertEqual(str(tag),
                         '<p><embed alt="bar" embedtype="image" format="left" id="1"/></p>')

    def test_clean_tag_node_with_data_linktype(self):
        soup = BeautifulSoup(
            '<a data-linktype="document" data-id="1" irrelevant="baz">foo</a>'
        )
        tag = soup.a
        DbWhitelister.clean_tag_node(soup, tag)
        self.assertEqual(str(tag), '<a id="1" linktype="document">foo</a>')

    def test_clean_tag_node(self):
        soup = BeautifulSoup(
            '<a irrelevant="baz">foo</a>'
        )
        tag = soup.a
        DbWhitelister.clean_tag_node(soup, tag)
        self.assertEqual(str(tag), '<a>foo</a>')


class TestExtractAttrs(TestCase):
    def test_extract_attr(self):
        html = '<a foo="bar" baz="quux">snowman</a>'
        result = extract_attrs(html)
        self.assertEqual(result, {'foo': 'bar', 'baz': 'quux'})


class TestExpandDbHtml(TestCase):
    def test_expand_db_html_with_linktype(self):
        html = '<a id="1" linktype="document">foo</a>'
        result = expand_db_html(html)
        self.assertEqual(result, '<a>foo</a>')

    def test_expand_db_html_no_linktype(self):
        html = '<a id="1">foo</a>'
        result = expand_db_html(html)
        self.assertEqual(result, '<a id="1">foo</a>')

    @patch('wagtail.wagtailembeds.embeds.oembed')
    def test_expand_db_html_with_embed(self, oembed):
        oembed.return_value = {
            'title': 'test title',
            'author_name': 'test author name',
            'provider_name': 'test provider name',
            'type': 'test type',
            'thumbnail_url': 'test thumbnail url',
            'width': 'test width',
            'height': 'test height',
            'html': 'test html'
        }
        html = '<embed embedtype="media" url="http://www.youtube.com/watch" />'
        result = expand_db_html(html)
        self.assertIn('test html', result)
