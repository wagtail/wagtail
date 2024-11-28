from django.test import TestCase
from django.urls import reverse

from wagtail.contrib.settings.registry import Registry
from wagtail.test.testapp.models import NotYetRegisteredGenericSetting
from wagtail.test.utils import WagtailTestUtils


class GenericSettingRegisterTestCase(WagtailTestUtils, TestCase):
    def setUp(self):
        self.registry = Registry()
        self.login()

    def test_register(self):
        self.assertNotIn(NotYetRegisteredGenericSetting, self.registry)
        NowRegisteredGenericSetting = self.registry.register_decorator(
            NotYetRegisteredGenericSetting
        )
        self.assertIn(NotYetRegisteredGenericSetting, self.registry)
        self.assertIs(NowRegisteredGenericSetting, NotYetRegisteredGenericSetting)

    def test_icon(self):
        admin = self.client.get(reverse("wagtailadmin_home"))
        self.assertContains(admin, '"tag"')
