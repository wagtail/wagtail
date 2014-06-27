from django.test import TestCase
from django.core.urlresolvers import reverse

from wagtail.tests.utils import WagtailTestUtils
from wagtail.tests.models import TestSetting
from wagtail.wagtailcore.models import Site


class TestSettingIndexView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

    def get(self, params={}):
        return self.client.get(reverse('wagtailsettings_index'), params)

    def test_status_code(self):
        self.assertEqual(self.get().status_code, 200)

    def test_displays_setting(self):
        self.assertContains(self.get(), "Test setting")


class TestSettingCreateView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

    def get(self, params={}):
        return self.client.get(
            reverse('wagtailsettings_edit', args=('tests', 'testsetting')),
            params)

    def post(self, post_data={}):
        return self.client.post(
            reverse('wagtailsettings_edit', args=('tests', 'testsetting')),
            post_data)

    def test_status_code(self):
        self.assertEqual(self.get().status_code, 200)

    def test_edit_invalid(self):
        response = self.post(post_data={'foo': 'bar'})
        self.assertContains(response, "The setting could not be saved due to errors.")
        self.assertContains(response, "This field is required.")

    def test_edit(self):
        response = self.post(post_data={'title': 'Edited site title',
                                        'email': 'test@example.com'})
        self.assertEqual(response.status_code, 302)

        default_site = Site.objects.get(is_default_site=True)
        setting = TestSetting.objects.get(site=default_site)
        self.assertEqual(setting.title, 'Edited site title')
        self.assertEqual(setting.email, 'test@example.com')


class TestSettingEditView(TestCase, WagtailTestUtils):
    def setUp(self):
        default_site = Site.objects.get(is_default_site=True)

        self.test_setting = TestSetting()
        self.test_setting.title = 'Site title'
        self.test_setting.email = 'initial@example.com'
        self.test_setting.site = default_site
        self.test_setting.save()

        self.login()

    def get(self, params={}):
        return self.client.get(
            reverse('wagtailsettings_edit', args=('tests', 'testsetting')),
            params)

    def post(self, post_data={}):
        return self.client.post(
            reverse('wagtailsettings_edit', args=('tests', 'testsetting')),
            post_data)

    def test_status_code(self):
        self.assertEqual(self.get().status_code, 200)

    def test_non_existant_model(self):
        response = self.client.get(
            reverse('wagtailsettings_edit', args=('tests', 'foo')))
        self.assertEqual(response.status_code, 404)

    def test_edit_invalid(self):
        response = self.post(post_data={'foo': 'bar'})
        self.assertContains(response, "The setting could not be saved due to errors.")
        self.assertContains(response, "This field is required.")

    def test_edit(self):
        response = self.post(post_data={'title': 'Edited site title',
                                        'email': 'test@example.com'})
        self.assertEqual(response.status_code, 302)

        default_site = Site.objects.get(is_default_site=True)
        setting = TestSetting.objects.get(site=default_site)
        self.assertEqual(setting.title, 'Edited site title')
        self.assertEqual(setting.email, 'test@example.com')
