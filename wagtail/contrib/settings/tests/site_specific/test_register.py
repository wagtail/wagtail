from django.test import TestCase
from django.urls import reverse

from wagtail.contrib.settings.registry import Registry
from wagtail.test.testapp.models import NotYetRegisteredSiteSetting
from wagtail.test.utils import WagtailTestUtils


class TestRegister(TestCase, WagtailTestUtils):
    def setUp(self):
        self.registry = Registry()
        self.login()

    def test_register(self):
        self.assertNotIn(NotYetRegisteredSiteSetting, self.registry)
        NowRegisteredSetting = self.registry.register_decorator(
            NotYetRegisteredSiteSetting
        )
        self.assertIn(NotYetRegisteredSiteSetting, self.registry)
        self.assertIs(NowRegisteredSetting, NotYetRegisteredSiteSetting)

    def test_icon(self):
        admin = self.client.get(reverse("wagtailadmin_home"))
        self.assertContains(admin, "icon-setting-tag")
