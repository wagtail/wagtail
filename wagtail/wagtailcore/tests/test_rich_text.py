from __future__ import absolute_import, unicode_literals

from bs4 import BeautifulSoup
from django.test import TestCase
from mock import patch

from wagtail.wagtailcore.rich_text import (
    DbWhitelister, PageLinkHandler, RichText, expand_db_html, extract_attrs)


class TestPageLinkHandler(TestCase):
    fixtures = ['test.json']

    def test_get_db_attributes(self):
        soup = BeautifulSoup('<a data-id="test-id">foo</a>', 'html5lib')
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


class TestDbWhiteLister(TestCase):
    def test_clean_tag_node_div(self):
        soup = BeautifulSoup('<div>foo</div>', 'html5lib')
        tag = soup.div
        self.assertEqual(tag.name, 'div')
        DbWhitelister.clean_tag_node(soup, tag)
        self.assertEqual(tag.name, 'p')

    def test_clean_tag_node_with_data_embedtype(self):
        soup = BeautifulSoup(
            '<p><a data-embedtype="image" data-id=1 data-format="left" data-alt="bar" irrelevant="baz">foo</a></p>',
            'html5lib'
        )
        tag = soup.p
        DbWhitelister.clean_tag_node(soup, tag)
        self.assertEqual(str(tag),
                         '<p><embed alt="bar" embedtype="image" format="left" id="1"/></p>')

    def test_clean_tag_node_with_data_linktype(self):
        soup = BeautifulSoup(
            '<a data-linktype="document" data-id="1" irrelevant="baz">foo</a>',
            'html5lib'
        )
        tag = soup.a
        DbWhitelister.clean_tag_node(soup, tag)
        self.assertEqual(str(tag), '<a id="1" linktype="document">foo</a>')

    def test_clean_tag_node(self):
        soup = BeautifulSoup('<a irrelevant="baz">foo</a>', 'html5lib')
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

    @patch('wagtail.wagtailembeds.finders.oembed.find_embed')
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


class TestRichTextValue(TestCase):
    fixtures = ['test.json']

    def test_construct_with_none(self):
        value = RichText(None)
        self.assertEqual(value.source, '')

    def test_construct_with_empty_string(self):
        value = RichText('')
        self.assertEqual(value.source, '')

    def test_construct_with_nonempty_string(self):
        value = RichText('<p>hello world</p>')
        self.assertEqual(value.source, '<p>hello world</p>')

    def test_render(self):
        value = RichText('<p>Merry <a linktype="page" id="4">Christmas</a>!</p>')
        result = str(value)
        self.assertEqual(
            result,
            '<div class="rich-text"><p>Merry <a href="/events/christmas/">Christmas</a>!</p></div>'
        )
