from __future__ import absolute_import, unicode_literals

from django.core.urlresolvers import reverse
from django.test import TestCase

from wagtail.contrib.settings.registry import Registry
from wagtail.tests.testapp.models import NotYetRegisteredSetting
from wagtail.tests.utils import WagtailTestUtils


class TestRegister(TestCase, WagtailTestUtils):
    def setUp(self):
        self.registry = Registry()
        self.login()

    def test_register(self):
        self.assertNotIn(NotYetRegisteredSetting, self.registry)
        NowRegisteredSetting = self.registry.register_decorator(NotYetRegisteredSetting)
        self.assertIn(NotYetRegisteredSetting, self.registry)
        self.assertIs(NowRegisteredSetting, NotYetRegisteredSetting)

    def test_icon(self):
        admin = self.client.get(reverse('wagtailadmin_home'))
        self.assertContains(admin, 'icon icon-tag')
