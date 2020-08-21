from unittest import TestCase

from django.test import RequestFactory, override_settings
from django.utils.encoding import force_bytes

from wagtail.core.models import Page, Site
from ..utils import FieldsParameterParseError, get_base_url, parse_boolean, parse_fields_parameter


class DynamicBaseUrl(object):
    def __str__(self):
        return 'https://www.example.com'

    def __bytes__(self):
        return force_bytes(self.__str__())

    def decode(self, *args, **kwargs):
        return self.__bytes__().decode(*args, **kwargs)


class TestGetBaseUrl(TestCase):
    def test_get_base_url(self):
        self.assertIsNone(get_base_url())

    def test_get_base_url_from_siteless_request(self):
        request = RequestFactory().get('/', HTTP_HOST='other.example.com')
        self.assertIsNone(get_base_url(request))

    def test_get_base_url_from_request(self):
        Site.objects.create(
            hostname='other.example.com',
            port=80,
            root_page=Page.objects.all().first(),
        )
        request = RequestFactory().get('/', HTTP_HOST='other.example.com')
        self.assertEqual(get_base_url(request), 'http://other.example.com')

    @override_settings(WAGTAILAPI_BASE_URL='https://bar.example.com')
    def get_base_url_from_setting_string(self):
        self.assertEqual(get_base_url(), 'https://bar.example.com')

    @override_settings(WAGTAILAPI_BASE_URL=b'https://baz.example.com')
    def get_base_url_from_setting_bytes(self):
        self.assertEqual(get_base_url(), 'https://baz.example.com')

    @override_settings(WAGTAILAPI_BASE_URL=DynamicBaseUrl())
    def get_base_url_from_setting_object(self):
        self.assertEqual(get_base_url(), 'https://www.example.com')


class TestParseFieldsParameter(TestCase):
    # GOOD STUFF

    def test_valid_single_field(self):
        parsed = parse_fields_parameter('test')

        self.assertEqual(parsed, [
            ('test', False, None),
        ])

    def test_valid_multiple_fields(self):
        parsed = parse_fields_parameter('test,another_test')

        self.assertEqual(parsed, [
            ('test', False, None),
            ('another_test', False, None),
        ])

    def test_valid_negated_field(self):
        parsed = parse_fields_parameter('-test')

        self.assertEqual(parsed, [
            ('test', True, None),
        ])

    def test_valid_nested_fields(self):
        parsed = parse_fields_parameter('test(foo,bar)')

        self.assertEqual(parsed, [
            ('test', False, [
                ('foo', False, None),
                ('bar', False, None),
            ]),
        ])

    def test_valid_star_field(self):
        parsed = parse_fields_parameter('*,-test')

        self.assertEqual(parsed, [
            ('*', False, None),
            ('test', True, None),
        ])

    def test_valid_star_with_additional_field(self):
        # Note: '*,test' is not allowed but '*,test(foo)' is
        parsed = parse_fields_parameter('*,test(foo)')

        self.assertEqual(parsed, [
            ('*', False, None),
            ('test', False, [
                ('foo', False, None),
            ]),
        ])

    def test_valid_underscore_field(self):
        parsed = parse_fields_parameter('_,test')

        self.assertEqual(parsed, [
            ('_', False, None),
            ('test', False, None),
        ])

    def test_valid_field_with_underscore_in_middle(self):
        parsed = parse_fields_parameter('a_test')

        self.assertEqual(parsed, [
            ('a_test', False, None),
        ])

    def test_valid_negated_field_with_underscore_in_middle(self):
        parsed = parse_fields_parameter('-a_test')

        self.assertEqual(parsed, [
            ('a_test', True, None),
        ])

    def test_valid_field_with_underscore_at_beginning(self):
        parsed = parse_fields_parameter('_test')

        self.assertEqual(parsed, [
            ('_test', False, None),
        ])

    def test_valid_field_with_underscore_at_end(self):
        parsed = parse_fields_parameter('test_')

        self.assertEqual(parsed, [
            ('test_', False, None),
        ])

    # BAD STUFF

    def test_invalid_char(self):
        with self.assertRaises(FieldsParameterParseError) as e:
            parse_fields_parameter('test#')

        self.assertEqual(str(e.exception), "unexpected char '#' at position 4")

    def test_invalid_whitespace_before_identifier(self):
        with self.assertRaises(FieldsParameterParseError) as e:
            parse_fields_parameter(' test')

        self.assertEqual(str(e.exception), "unexpected whitespace at position 0")

    def test_invalid_whitespace_after_identifier(self):
        with self.assertRaises(FieldsParameterParseError) as e:
            parse_fields_parameter('test ')

        self.assertEqual(str(e.exception), "unexpected whitespace at position 4")

    def test_invalid_whitespace_after_comma(self):
        with self.assertRaises(FieldsParameterParseError) as e:
            parse_fields_parameter('test, test')

        self.assertEqual(str(e.exception), "unexpected whitespace at position 5")

    def test_invalid_whitespace_before_comma(self):
        with self.assertRaises(FieldsParameterParseError) as e:
            parse_fields_parameter('test ,test')

        self.assertEqual(str(e.exception), "unexpected whitespace at position 4")

    def test_invalid_unexpected_negation_operator(self):
        with self.assertRaises(FieldsParameterParseError) as e:
            parse_fields_parameter('test-')

        self.assertEqual(str(e.exception), "unexpected char '-' at position 4")

    def test_invalid_unexpected_open_bracket(self):
        with self.assertRaises(FieldsParameterParseError) as e:
            parse_fields_parameter('test,(foo)')

        self.assertEqual(str(e.exception), "unexpected char '(' at position 5")

    def test_invalid_unexpected_close_bracket(self):
        with self.assertRaises(FieldsParameterParseError) as e:
            parse_fields_parameter('test)')

        self.assertEqual(str(e.exception), "unexpected char ')' at position 4")

    def test_invalid_unexpected_comma_in_middle(self):
        with self.assertRaises(FieldsParameterParseError) as e:
            parse_fields_parameter('test,,foo')

        self.assertEqual(str(e.exception), "unexpected char ',' at position 5")

    def test_invalid_unexpected_comma_at_end(self):
        with self.assertRaises(FieldsParameterParseError) as e:
            parse_fields_parameter('test,foo,')

        self.assertEqual(str(e.exception), "unexpected char ',' at position 9")

    def test_invalid_unclosed_bracket(self):
        with self.assertRaises(FieldsParameterParseError) as e:
            parse_fields_parameter('test(foo')

        self.assertEqual(str(e.exception), "unexpected end of input (did you miss out a close bracket?)")

    def test_invalid_subfields_on_negated_field(self):
        with self.assertRaises(FieldsParameterParseError) as e:
            parse_fields_parameter('-test(foo)')

        self.assertEqual(str(e.exception), "unexpected char '(' at position 5")

    def test_invalid_star_field_in_wrong_position(self):
        with self.assertRaises(FieldsParameterParseError) as e:
            parse_fields_parameter('test,*')

        self.assertEqual(str(e.exception), "'*' must be in the first position")

    def test_invalid_negated_star(self):
        with self.assertRaises(FieldsParameterParseError) as e:
            parse_fields_parameter('-*')

        self.assertEqual(str(e.exception), "'*' cannot be negated")

    def test_invalid_star_with_nesting(self):
        with self.assertRaises(FieldsParameterParseError) as e:
            parse_fields_parameter('*(foo,bar)')

        self.assertEqual(str(e.exception), "unexpected char '(' at position 1")

    def test_invalid_star_with_chars_after(self):
        with self.assertRaises(FieldsParameterParseError) as e:
            parse_fields_parameter('*foo')

        self.assertEqual(str(e.exception), "unexpected char 'f' at position 1")

    def test_invalid_star_with_chars_before(self):
        with self.assertRaises(FieldsParameterParseError) as e:
            parse_fields_parameter('foo*')

        self.assertEqual(str(e.exception), "unexpected char '*' at position 3")

    def test_invalid_star_with_additional_field(self):
        with self.assertRaises(FieldsParameterParseError) as e:
            parse_fields_parameter('*,foo')

        self.assertEqual(str(e.exception), "additional fields with '*' doesn't make sense")

    def test_invalid_underscore_in_wrong_position(self):
        with self.assertRaises(FieldsParameterParseError) as e:
            parse_fields_parameter('test,_')

        self.assertEqual(str(e.exception), "'_' must be in the first position")

    def test_invalid_negated_underscore(self):
        with self.assertRaises(FieldsParameterParseError) as e:
            parse_fields_parameter('-_')

        self.assertEqual(str(e.exception), "'_' cannot be negated")

    def test_invalid_underscore_with_nesting(self):
        with self.assertRaises(FieldsParameterParseError) as e:
            parse_fields_parameter('_(foo,bar)')

        self.assertEqual(str(e.exception), "unexpected char '(' at position 1")

    def test_invalid_underscore_with_negated_field(self):
        with self.assertRaises(FieldsParameterParseError) as e:
            parse_fields_parameter('_,-foo')

        self.assertEqual(str(e.exception), "negated fields with '_' doesn't make sense")

    def test_invalid_star_and_underscore(self):
        with self.assertRaises(FieldsParameterParseError) as e:
            parse_fields_parameter('*,_')

        self.assertEqual(str(e.exception), "'_' must be in the first position")


class TestParseBoolean(TestCase):
    # GOOD STUFF

    def test_valid_true(self):
        parsed = parse_boolean('true')

        self.assertEqual(parsed, True)

    def test_valid_false(self):
        parsed = parse_boolean('false')

        self.assertEqual(parsed, False)

    def test_valid_1(self):
        parsed = parse_boolean('1')

        self.assertEqual(parsed, True)

    def test_valid_0(self):
        parsed = parse_boolean('0')

        self.assertEqual(parsed, False)

    # BAD STUFF

    def test_invalid(self):
        with self.assertRaises(ValueError) as e:
            parse_boolean('foo')

        self.assertEqual(str(e.exception), "expected 'true' or 'false', got 'foo'")

    def test_invalid_integer(self):
        with self.assertRaises(ValueError) as e:
            parse_boolean('2')

        self.assertEqual(str(e.exception), "expected 'true' or 'false', got '2'")
