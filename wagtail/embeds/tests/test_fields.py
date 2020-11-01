from unittest import TestCase

from django.core.validators import URLValidator
from django.db.models import TextField
from django.forms.fields import URLField as FormURLField
from django.utils.translation import gettext_lazy as _

from ..fields import URLField


class TestURLField(TestCase):
    def test_is_text_field(self):
        self.assertIsInstance(URLField(), TextField)

    def test_description(self):
        self.assertEqual(URLField.description, _("URL"))

    def test_validator(self):
        self.assertEqual(URLField.default_validators, [URLValidator()])

    def test_formfield(self):
        self.assertIsInstance(URLField().formfield(), FormURLField)
