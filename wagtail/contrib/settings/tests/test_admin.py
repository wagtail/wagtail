from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils.text import capfirst

from wagtail.contrib.settings.registry import SettingMenuItem
from wagtail.tests.testapp.models import IconSetting, TestSetting
from wagtail.tests.utils import WagtailTestUtils
from wagtail.wagtailcore.models import Site


class TestSettingMenu(TestCase, WagtailTestUtils):

    def login_only_admin(self):
        """ Log in with a user that only has permission to access the admin """
        user = get_user_model().objects.create_user(
            username='test', email='test@email.com', password='password')
        user.user_permissions.add(Permission.objects.get_by_natural_key(
            codename='access_admin',
            app_label='wagtailadmin',
            model='admin'))
        self.client.login(username='test', password='password')
        return user

    def test_menu_item_in_admin(self):
        self.login()
        response = self.client.get(reverse('wagtailadmin_home'))

        self.assertContains(response, capfirst(TestSetting._meta.verbose_name))
        self.assertContains(response, reverse('wagtailsettings_edit', args=('tests', 'testsetting')))

    def test_menu_item_no_permissions(self):
        self.login_only_admin()
        response = self.client.get(reverse('wagtailadmin_home'))

        self.assertNotContains(response, TestSetting._meta.verbose_name)
        self.assertNotContains(response, reverse('wagtailsettings_edit', args=('tests', 'testsetting')))

    def test_menu_item_icon(self):
        menu_item = SettingMenuItem(IconSetting, icon='tag', classnames='test-class')
        classnames = set(menu_item.classnames.split(' '))
        self.assertEqual(classnames, {'icon', 'icon-tag', 'test-class'})


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
