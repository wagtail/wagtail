# -*- coding: utf-8 -*
from __future__ import unicode_literals

from django.test import TestCase

from django.utils.text import slugify
from wagtail.wagtailcore.utils import cautious_slugify


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
