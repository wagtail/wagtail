import json

from django.test import TestCase
from wagtail.tests.utils import WagtailTestUtils

from .fields import ConvertedValue, ConvertedValueField


class TestConvertedValueField(TestCase, WagtailTestUtils):
    def setUp(self):
        self.user = self.login()
    
    def test_custom_user_primary_key_is_hashable(self):
        hash(self.user.pk)
    
    def test_custom_user_primary_key_is_jsonable(self):
        json_str = json.dumps({'pk': self.user.pk}, separators=(',',':'))
        self.assertEqual(json_str, '{"pk":"%s"}' % self.user.pk)
    
    def test_custom_user_primary_key(self):
        self.assertIsInstance(self.user.pk, ConvertedValue)
    
    def test_custom_user_primary_key_is_converted_value_field(self):
        User = self.user.__class__
        pk_field = User._meta.get_field(User._meta.pk.name)
        self.assertIsInstance(pk_field, ConvertedValueField)
