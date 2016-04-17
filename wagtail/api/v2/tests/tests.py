from __future__ import absolute_import, unicode_literals

from unittest import TestCase

from ..utils import FieldsParameterParseError, parse_fields_parameter


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
        parsed = parse_fields_parameter('*,test')

        self.assertEqual(parsed, [
            ('*', False, None),
            ('test', False, None),
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
