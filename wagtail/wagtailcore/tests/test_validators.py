from django.test import TestCase
from django.core.exceptions import ValidationError

from wagtail.wagtailcore.validators import validate_not_whitespace


class TestValidators(TestCase):

    def test_not_whitespace(self):
        validate_not_whitespace('bar')

        for test_value in (' ', '\t', '\r', '\n', '\r\n'):
            with self.assertRaises(ValidationError):
                validate_not_whitespace(test_value)
