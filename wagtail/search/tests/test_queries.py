from django.test import SimpleTestCase, TestCase

from wagtail.search.query import And, Or, Phrase, PlainText
from wagtail.search.utils import (
    balanced_reduce,
    normalise_query_string,
    parse_query_string,
    separate_filters_from_query,
)


class TestQueryStringNormalisation(TestCase):
    def test_truncation(self):
        test_querystring = "a" * 1000
        result = normalise_query_string(test_querystring)
        self.assertEqual(len(result), 255)

    def test_no_truncation(self):
        test_querystring = "a" * 10
        result = normalise_query_string(test_querystring)
        self.assertEqual(len(result), 10)


class TestSeparateFiltersFromQuery(SimpleTestCase):
    def test_only_query(self):
        filters, query = separate_filters_from_query("hello world")

        self.assertDictEqual(filters.dict(), {})
        self.assertEqual(query, "hello world")

    def test_filter(self):
        filters, query = separate_filters_from_query("author:foo")

        self.assertDictEqual(filters.dict(), {"author": "foo"})
        self.assertEqual(query, "")

    def test_filter_with_quotation_mark(self):
        filters, query = separate_filters_from_query('author:"foo bar"')

        self.assertDictEqual(filters.dict(), {"author": "foo bar"})
        self.assertEqual(query, "")

    def test_filter_and_query(self):
        filters, query = separate_filters_from_query("author:foo hello world")

        self.assertDictEqual(filters.dict(), {"author": "foo"})
        self.assertEqual(query, "hello world")

    def test_filter_with_quotation_mark_and_query(self):
        filters, query = separate_filters_from_query('author:"foo bar" hello world')

        self.assertDictEqual(filters.dict(), {"author": "foo bar"})
        self.assertEqual(query, "hello world")

    def test_filter_with_unclosed_quotation_mark_and_query(self):
        filters, query = separate_filters_from_query('author:"foo bar hello world')

        self.assertDictEqual(filters.dict(), {})
        self.assertEqual(query, 'author:"foo bar hello world')

    def test_two_filters_and_query(self):
        filters, query = separate_filters_from_query(
            'author:"foo bar" hello world bar:beer'
        )

        self.assertDictEqual(filters.dict(), {"author": "foo bar", "bar": "beer"})
        self.assertEqual(query, "hello world")

    def test_two_filters_with_quotation_marks_and_query(self):
        filters, query = separate_filters_from_query(
            'author:"foo bar" hello world bar:"two beers"'
        )

        self.assertDictEqual(filters.dict(), {"author": "foo bar", "bar": "two beers"})
        self.assertEqual(query, "hello world")

        filters, query = separate_filters_from_query(
            "author:'foo bar' hello world bar:'two beers'"
        )

        self.assertDictEqual(filters.dict(), {"author": "foo bar", "bar": "two beers"})
        self.assertEqual(query, "hello world")

    def test_return_list_of_multiple_instances_for_same_filter_key(self):
        filters, query = separate_filters_from_query(
            'foo:test1 hello world foo:test2 foo:"test3" foo2:test4'
        )

        self.assertDictEqual(filters.dict(), {"foo": "test3", "foo2": "test4"})
        self.assertListEqual(filters.getlist("foo"), ["test1", "test2", "test3"])
        self.assertEqual(query, "hello world")


class TestParseQueryString(SimpleTestCase):
    def test_simple_query(self):
        filters, query = parse_query_string("hello world")

        self.assertDictEqual(filters.dict(), {})
        self.assertEqual(repr(query), repr(PlainText("hello world")))

    def test_with_phrase(self):
        filters, query = parse_query_string('"hello world"')

        self.assertDictEqual(filters.dict(), {})
        self.assertEqual(repr(query), repr(Phrase("hello world")))

        filters, query = parse_query_string("'hello world'")

        self.assertDictEqual(filters.dict(), {})
        self.assertEqual(repr(query), repr(Phrase("hello world")))

    def test_with_simple_and_phrase(self):
        filters, query = parse_query_string('this is simple "hello world"')

        self.assertDictEqual(filters.dict(), {})
        self.assertEqual(
            repr(query), repr(And([PlainText("this is simple"), Phrase("hello world")]))
        )

        filters, query = parse_query_string("this is simple 'hello world'")

        self.assertDictEqual(filters.dict(), {})
        self.assertEqual(
            repr(query), repr(And([PlainText("this is simple"), Phrase("hello world")]))
        )

    def test_operator(self):
        filters, query = parse_query_string(
            'this is simple "hello world"', operator="or"
        )

        self.assertDictEqual(filters.dict(), {})
        self.assertEqual(
            repr(query),
            repr(
                Or([PlainText("this is simple", operator="or"), Phrase("hello world")])
            ),
        )

        filters, query = parse_query_string(
            "this is simple 'hello world'", operator="or"
        )

        self.assertDictEqual(filters.dict(), {})
        self.assertEqual(
            repr(query),
            repr(
                Or([PlainText("this is simple", operator="or"), Phrase("hello world")])
            ),
        )

    def test_with_phrase_unclosed(self):
        filters, query = parse_query_string('"hello world')

        self.assertDictEqual(filters.dict(), {})
        self.assertEqual(repr(query), repr(Phrase("hello world")))

        filters, query = parse_query_string("'hello world")

        self.assertDictEqual(filters.dict(), {})
        self.assertEqual(repr(query), repr(Phrase("hello world")))

    def test_phrase_with_filter(self):
        filters, query = parse_query_string('"hello world" author:"foo bar" bar:beer')

        self.assertDictEqual(filters.dict(), {"author": "foo bar", "bar": "beer"})
        self.assertEqual(repr(query), repr(Phrase("hello world")))

        filters, query = parse_query_string("'hello world' author:'foo bar' bar:beer")

        self.assertDictEqual(filters.dict(), {"author": "foo bar", "bar": "beer"})
        self.assertEqual(repr(query), repr(Phrase("hello world")))

    def test_long_queries(self):
        filters, query = parse_query_string("0" * 60_000)
        self.assertEqual(filters.dict(), {})
        self.assertEqual(repr(query), repr(PlainText("0" * 60_000)))

        filters, _ = parse_query_string(f'{"a" * 60_000}:"foo bar"')
        self.assertEqual(filters.dict(), {"a" * 60_000: "foo bar"})

    def test_long_filter_value(self):
        filters, _ = parse_query_string(f"foo:ba{'r' * 60_000}")
        self.assertEqual(filters.dict(), {"foo": f"ba{'r' * 60_000}"})

    def test_joined_filters(self):
        filters, query = parse_query_string("foo:bar:baz")
        self.assertEqual(filters.dict(), {"foo": "bar"})
        self.assertEqual(repr(query), repr(PlainText(":baz")))

        filters, query = parse_query_string("foo:'bar':baz")
        self.assertEqual(filters.dict(), {"foo": "bar"})
        self.assertEqual(repr(query), repr(PlainText(":baz")))

        filters, query = parse_query_string("foo:'bar:baz'")
        self.assertEqual(filters.dict(), {"foo": "bar:baz"})

    def test_multiple_phrases(self):
        filters, query = parse_query_string('"hello world" "hi earth"')

        self.assertEqual(
            repr(query), repr(And([Phrase("hello world"), Phrase("hi earth")]))
        )

        filters, query = parse_query_string("'hello world' 'hi earth'")

        self.assertEqual(
            repr(query), repr(And([Phrase("hello world"), Phrase("hi earth")]))
        )

    def test_mixed_phrases_with_filters(self):
        filters, query = parse_query_string(
            """"lord of the rings" army_1:"elves" army_2:'humans'"""
        )

        self.assertDictEqual(filters.dict(), {"army_1": "elves", "army_2": "humans"})
        self.assertEqual(
            repr(query),
            repr(Phrase("lord of the rings")),
        )


class TestBalancedReduce(SimpleTestCase):
    # For simple values, this should behave exactly the same as Pythons reduce()
    # So I've copied its tests: https://github.com/python/cpython/blob/21cdb711e3b1975398c54141e519ead02670610e/Lib/test/test_functools.py#L771

    def test_reduce(self):
        class Squares:
            def __init__(self, max):
                self.max = max
                self.sofar = []

            def __len__(self):
                return len(self.sofar)

            def __getitem__(self, i):
                if not 0 <= i < self.max:
                    raise IndexError
                n = len(self.sofar)
                while n <= i:
                    self.sofar.append(n * n)
                    n += 1
                return self.sofar[i]

        def add(x, y):
            return x + y

        self.assertEqual(balanced_reduce(add, ["a", "b", "c"], ""), "abc")
        self.assertEqual(
            balanced_reduce(add, [["a", "c"], [], ["d", "w"]], []), ["a", "c", "d", "w"]
        )
        self.assertEqual(balanced_reduce(lambda x, y: x * y, range(2, 8), 1), 5040)
        self.assertEqual(
            balanced_reduce(lambda x, y: x * y, range(2, 21), 1), 2432902008176640000
        )
        self.assertEqual(balanced_reduce(add, Squares(10)), 285)
        self.assertEqual(balanced_reduce(add, Squares(10), 0), 285)
        self.assertEqual(balanced_reduce(add, Squares(0), 0), 0)
        self.assertRaises(TypeError, balanced_reduce)
        self.assertRaises(TypeError, balanced_reduce, 42, 42)
        self.assertRaises(TypeError, balanced_reduce, 42, 42, 42)
        self.assertEqual(
            balanced_reduce(42, "1"), "1"
        )  # func is never called with one item
        self.assertEqual(
            balanced_reduce(42, "", "1"), "1"
        )  # func is never called with one item
        self.assertRaises(TypeError, balanced_reduce, 42, (42, 42))
        self.assertRaises(
            TypeError, balanced_reduce, add, []
        )  # arg 2 must not be empty sequence with no initial value
        self.assertRaises(TypeError, balanced_reduce, add, "")
        self.assertRaises(TypeError, balanced_reduce, add, ())
        self.assertRaises(TypeError, balanced_reduce, add, object())

        class TestFailingIter:
            def __iter__(self):
                raise RuntimeError

        self.assertRaises(RuntimeError, balanced_reduce, add, TestFailingIter())

        self.assertIsNone(balanced_reduce(add, [], None))
        self.assertEqual(balanced_reduce(add, [], 42), 42)

        class BadSeq:
            def __getitem__(self, index):
                raise ValueError

        self.assertRaises(ValueError, balanced_reduce, 42, BadSeq())

    # Test reduce()'s use of iterators.
    def test_iterator_usage(self):
        class SequenceClass:
            def __init__(self, n):
                self.n = n

            def __getitem__(self, i):
                if 0 <= i < self.n:
                    return i
                else:
                    raise IndexError

        from operator import add

        self.assertEqual(balanced_reduce(add, SequenceClass(5)), 10)
        self.assertEqual(balanced_reduce(add, SequenceClass(5), 42), 52)
        self.assertRaises(TypeError, balanced_reduce, add, SequenceClass(0))
        self.assertEqual(balanced_reduce(add, SequenceClass(0), 42), 42)
        self.assertEqual(balanced_reduce(add, SequenceClass(1)), 0)
        self.assertEqual(balanced_reduce(add, SequenceClass(1), 42), 42)

        d = {"one": 1, "two": 2, "three": 3}
        self.assertEqual(balanced_reduce(add, d), "".join(d.keys()))

    # This test is specific to balanced_reduce
    def test_is_balanced(self):
        # Tests that balanced_reduce returns the object as a balanced tree
        class CombinedNode:
            def __init__(self, a, b):
                self.a = a
                self.b = b

            def __repr__(self):
                return f"({self.a} {self.b})"

        self.assertEqual(
            repr(
                balanced_reduce(CombinedNode, ["A", "B", "C", "D", "E", "F", "G", "H"])
            ),
            "(((A B) (C D)) ((E F) (G H)))",
            # Note: functools.reduce will return '(((((((A B) C) D) E) F) G) H)'
        )
