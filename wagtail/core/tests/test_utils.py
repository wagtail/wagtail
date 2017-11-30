# -*- coding: utf-8 -*
from django.test import TestCase
from django.utils.text import slugify

from wagtail.core.utils import accepts_kwarg, cautious_slugify


class TestCautiousSlugify(TestCase):

    def test_behaves_same_as_slugify_for_latin_chars(self):
        test_cases = [
            ('', ''),
            ('???', ''),
            ('Hello world', 'hello-world'),
            ('Hello_world', 'hello_world'),
            ('Hellö wörld', 'hello-world'),
            ('Hello   world', 'hello-world'),
            ('   Hello world   ', 'hello-world'),
            ('Hello, world!', 'hello-world'),
            ('Hello*world', 'helloworld'),
            ('Hello☃world', 'helloworld'),
        ]

        for (original, expected_result) in test_cases:
            self.assertEqual(slugify(original), expected_result)
            self.assertEqual(cautious_slugify(original), expected_result)

    def test_escapes_non_latin_chars(self):
        test_cases = [
            ('Straßenbahn', 'straxdfenbahn'),
            ('Спорт!', 'u0421u043fu043eu0440u0442'),
            ('〔山脈〕', 'u5c71u8108'),
        ]

        for (original, expected_result) in test_cases:
            self.assertEqual(cautious_slugify(original), expected_result)


class TestAcceptsKwarg(TestCase):
    def test_accepts_kwarg(self):
        def func_without_banana(apple, orange=42):
            pass

        def func_with_banana(apple, banana=42):
            pass

        def func_with_kwargs(apple, **kwargs):
            pass

        self.assertFalse(accepts_kwarg(func_without_banana, 'banana'))
        self.assertTrue(accepts_kwarg(func_with_banana, 'banana'))
        self.assertTrue(accepts_kwarg(func_with_kwargs, 'banana'))
