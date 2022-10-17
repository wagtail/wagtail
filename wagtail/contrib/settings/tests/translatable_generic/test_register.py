from django.test import TestCase
from django.urls import reverse

from wagtail.contrib.settings.registry import Registry
from wagtail.test.testapp.models import NotYetRegisteredTranslatableGenericSetting
from wagtail.test.utils import WagtailTestUtils


class TranslatableGenericSettingRegisterTestCase(TestCase, WagtailTestUtils):
    def setUp(self):
        self.registry = Registry()
        self.login()

    def test_register(self):
        self.assertNotIn(NotYetRegisteredTranslatableGenericSetting, self.registry)
        NowRegisteredTranslatableGenericSetting = self.registry.register_decorator(
            NotYetRegisteredTranslatableGenericSetting
        )
        self.assertIn(NotYetRegisteredTranslatableGenericSetting, self.registry)
        self.assertIs(
            NowRegisteredTranslatableGenericSetting,
            NotYetRegisteredTranslatableGenericSetting,
        )

    def test_icon(self):
        admin = self.client.get(reverse("wagtailadmin_home"))
        self.assertContains(admin, "icon-setting-tag")
