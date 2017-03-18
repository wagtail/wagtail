from django.test import TestCase
from wagtail.tests.utils import WagtailTestUtils

from .fields import ConvertedValue, ConvertedValueField


class TestConvertedValueField(TestCase, WagtailTestUtils):
    def setUp(self):
        self.user = self.login()
    
    def test_user_created(self):
        self.assertTrue(self.user)
    
    def test_custom_user_primary_key(self):
        self.assertIsInstance(self.user.pk, ConvertedValue)
    
    def test_custom_user_primary_key_is_converted_value_field(self):
        User = self.user.__class__
        pk_field = User._meta.get_field(User._meta.pk.name)
        self.assertIsInstance(pk_field, ConvertedValueField)
