from django.test import TestCase
from django.urls import reverse

from wagtail.contrib.settings.registry import Registry
from wagtail.test.testapp.models import SimplePage
from wagtail.test.utils import WagtailTestUtils


class TestRegister(TestCase, WagtailTestUtils):
    def setUp(self):
        self.registry = Registry()
        self.login()

    def test_register_invalid_setting_model(self):
        self.assertNotIn(SimplePage, self.registry)

        with self.assertRaises(NotImplementedError):
            self.registry.register_decorator(SimplePage)

        self.assertNotIn(SimplePage, self.registry)


class TestEditSettingView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.user = self.login()

    def test_inexistent_model(self):
        response = self.client.get(
            reverse("wagtailsettings:edit", args=["test", "foo", 1])
        )
        self.assertEqual(response.status_code, 404)

    def test_invalid_model(self):
        args = [SimplePage._meta.app_label, SimplePage._meta.model_name, 1]
        response = self.client.get(reverse("wagtailsettings:edit", args=args))
        self.assertEqual(response.status_code, 404)
