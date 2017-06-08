from __future__ import absolute_import, unicode_literals

from bs4 import BeautifulSoup

from django.test import TestCase

from wagtail.wagtaildocs.rich_text import DocumentLinkHandler


class TestDocumentRichTextLinkHandler(TestCase):
    fixtures = ['test.json']

    def test_get_db_attributes(self):
        soup = BeautifulSoup('<a data-id="test-id">foo</a>', 'html5lib')
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
                         '<a data-linktype="document" data-id="1" href="/documents/1/test.pdf">')

    def test_expand_db_attributes_not_for_editor(self):
        result = DocumentLinkHandler.expand_db_attributes(
            {'id': 1},
            False
        )
        self.assertEqual(result,
                         '<a href="/documents/1/test.pdf">')
