# -*- coding: utf-8 -*
from django.test import TestCase
from django.utils.text import slugify

from wagtail.core.utils import (
    accepts_kwarg, camelcase_to_underscore, cautious_slugify,
    safe_snake_case, string_to_ascii)


class TestCamelCaseToUnderscore(TestCase):

    def test_camelcase_to_underscore(self):
        test_cases = [
            ('HelloWorld', 'hello_world'),
            ('longValueWithVarious subStrings', 'long_value_with_various sub_strings')
        ]

        for (original, expected_result) in test_cases:
            self.assertEqual(camelcase_to_underscore(original), expected_result)


class TestStringToAscii(TestCase):

    def test_string_to_ascii(self):
        test_cases = [
            (u'30 \U0001d5c4\U0001d5c6/\U0001d5c1', '30 km/h'),
            (u'\u5317\u4EB0', 'Bei Jing '),
            ('ぁ あ ぃ い ぅ う ぇ', 'a a i i u u e'),
            ('Ա Բ Գ Դ Ե Զ Է Ը Թ Ժ Ի Լ Խ Ծ Կ Հ Ձ Ղ Ճ Մ Յ Ն', 'A B G D E Z E E T` Zh I L Kh Ts K H Dz Gh Ch M Y N'),
            ('Спорт!', 'Sport!'),
            ('Straßenbahn', 'Strassenbahn'),
            ('Hello world', 'Hello world'),
            ('Ā ā Ă ă Ą ą Ć ć Ĉ ĉ Ċ ċ Č č Ď ď Đ', 'A a A a A a C c C c C c C c D d D'),
            ('〔山脈〕', '[Shan Mo ] '),
        ]

        for (original, expected_result) in test_cases:
            self.assertEqual(string_to_ascii(original), expected_result)


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


class TestSafeSnakeCase(TestCase):

    def test_strings_with_latin_chars(self):
        test_cases = [
            ('', ''),
            ('???', ''),
            ('using-Hyphen', 'using_hyphen'),
            ('en–⁠dash', 'endash'),  # unicode non-letter characters stripped
            ('  em—dash ', 'emdash'),  # unicode non-letter characters stripped
            ('horizontal―BAR', 'horizontalbar'),  # unicode non-letter characters stripped
            ('Hello world', 'hello_world'),
            ('Hello_world', 'hello_world'),
            ('Hellö wörld', 'hello_world'),
            ('Hello   world', 'hello_world'),
            ('   Hello world   ', 'hello_world'),
            ('Hello, world!', 'hello_world'),
            ('Hello*world', 'helloworld'),
            ('Screenshot_2020-05-29 Screenshot(1).png', 'screenshot_2020_05_29_screenshot1png')
        ]

        for (original, expected_result) in test_cases:
            self.assertEqual(safe_snake_case(original), expected_result)

    def test_strings_with__non_latin_chars(self):
        test_cases = [
            ('Straßenbahn Straßenbahn', 'straxdfenbahn_straxdfenbahn'),
            ('Сп орт!', 'u0421u043f_u043eu0440u0442'),
        ]

        for (original, expected_result) in test_cases:
            self.assertEqual(safe_snake_case(original), expected_result)


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
