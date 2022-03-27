import json
import unittest

from django.conf import settings
from django.db import connections
from django.test import TestCase

from wagtail.test.utils import WagtailTestUtils

from .fields import ConvertedValue, ConvertedValueField


@unittest.skipUnless(
    settings.AUTH_USER_MODEL == "customuser.CustomUser", "Only applicable to CustomUser"
)
class TestConvertedValueField(TestCase, WagtailTestUtils):
    def setUp(self):
        self.user = self.login()

        User = self.user.__class__
        self.pk_field = User._meta.get_field(User._meta.pk.name)
        self.pk_db_value = self.pk_field.get_db_prep_value(
            self.user.pk, connections["default"]
        )

    def test_db_value_is_different(self):
        self.assertEqual(self.user.pk, self.pk_db_value)
        self.assertNotEqual(str(self.user.pk), str(self.pk_db_value))

    def test_custom_user_primary_key_is_hashable(self):
        hash(self.user.pk)

    def test_custom_user_primary_key_is_jsonable(self):
        json_str = json.dumps({"pk": self.user.pk}, separators=(",", ":"))
        self.assertEqual(json_str, '{"pk":"%s"}' % self.user.pk)

        # verify the json string uses the display value and not the db value
        self.assertNotEqual(json_str, '{"pk":"%s"}' % self.pk_db_value)

    def test_custom_user_primary_key(self):
        self.assertIsInstance(self.user.pk, ConvertedValue)

    def test_custom_user_primary_key_is_converted_value_field(self):
        self.assertIsInstance(self.pk_field, ConvertedValueField)
