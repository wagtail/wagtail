from django.test import SimpleTestCase

from wagtail.search.query import And, Phrase, PlainText
from wagtail.search.utils import parse_query_string


class TestParseQueryString(SimpleTestCase):
    def test_apostrophe_in_word(self):
        """
        Searching for a word containing an apostrophe (e.g. "it's") should
        be treated as a single PlainText query, not split into PlainText AND Phrase.
        See: https://github.com/wagtail/wagtail/issues/XXXXX
        """
        filters, query = parse_query_string("it's")

        self.assertDictEqual(filters.dict(), {})
        self.assertEqual(repr(query), repr(PlainText("it's")))

    def test_apostrophe_as_phrase_delimiter(self):
        """
        Apostrophes used as phrase delimiters should still work.
        e.g. 'hot cross bun' should be treated as a phrase.
        """
        filters, query = parse_query_string("'hot cross bun'")

        self.assertDictEqual(filters.dict(), {})
        self.assertEqual(repr(query), repr(Phrase("hot cross bun")))

    def test_apostrophe_phrase_with_plain_text(self):
        """
        Mix of plain text and apostrophe phrase should still work.
        e.g. recipe 'hot cross bun'
        """
        filters, query = parse_query_string("recipe 'hot cross bun'")

        self.assertDictEqual(filters.dict(), {})
        self.assertEqual(
            repr(query), repr(And([PlainText("recipe"), Phrase("hot cross bun")]))
        )

    def test_multiple_apostrophes_in_words(self):
        """
        Multiple mid-word apostrophes should all be handled correctly.
        """
        filters, query = parse_query_string("it's don't")

        self.assertDictEqual(filters.dict(), {})
        self.assertEqual(repr(query), repr(PlainText("it's don't")))
