from __future__ import absolute_import, unicode_literals

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils.text import capfirst

from wagtail.contrib.settings.registry import SettingMenuItem
from wagtail.tests.testapp.models import FileUploadSetting, IconSetting, TestSetting
from wagtail.tests.utils import WagtailTestUtils
from wagtail.wagtailcore import hooks
from wagtail.wagtailcore.models import Page, Site


class TestSettingMenu(TestCase, WagtailTestUtils):

    def login_only_admin(self):
        """ Log in with a user that only has permission to access the admin """
        user = get_user_model().objects.create_user(
            username='test', email='test@email.com', password='password')
        user.user_permissions.add(Permission.objects.get_by_natural_key(
            codename='access_admin', app_label='wagtailadmin', model='admin'))
        self.assertTrue(self.client.login(username='test', password='password'))
        return user

    def test_menu_item_in_admin(self):
        self.login()
        response = self.client.get(reverse('wagtailadmin_home'))

        self.assertContains(response, capfirst(TestSetting._meta.verbose_name))
        self.assertContains(response, reverse('wagtailsettings:edit', args=('tests', 'testsetting')))

    def test_menu_item_no_permissions(self):
        self.login_only_admin()
        response = self.client.get(reverse('wagtailadmin_home'))

        self.assertNotContains(response, TestSetting._meta.verbose_name)
        self.assertNotContains(response, reverse('wagtailsettings:edit', args=('tests', 'testsetting')))

    def test_menu_item_icon(self):
        menu_item = SettingMenuItem(IconSetting, icon='tag', classnames='test-class')
        classnames = set(menu_item.classnames.split(' '))
        self.assertEqual(classnames, {'icon', 'icon-tag', 'test-class'})


class BaseTestSettingView(TestCase, WagtailTestUtils):
    def get(self, site_pk=1, params={}, setting=TestSetting):
        url = self.edit_url(setting=setting, site_pk=site_pk)
        return self.client.get(url, params)

    def post(self, site_pk=1, post_data={}, setting=TestSetting):
        url = self.edit_url(setting=setting, site_pk=site_pk)
        return self.client.post(url, post_data)

    def edit_url(self, setting, site_pk=1):
        args = [setting._meta.app_label, setting._meta.model_name, site_pk]
        return reverse('wagtailsettings:edit', args=args)


class TestSettingCreateView(BaseTestSettingView):
    def setUp(self):
        self.login()

    def test_get_edit(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        # there should be a menu item highlighted as active
        self.assertContains(response, "menu-active")

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

    def test_file_upload_multipart(self):
        response = self.get(setting=FileUploadSetting)
        # Ensure the form supports file uploads
        self.assertContains(response, 'enctype="multipart/form-data"')


class TestSettingEditView(BaseTestSettingView):
    def setUp(self):
        default_site = Site.objects.get(is_default_site=True)

        self.test_setting = TestSetting()
        self.test_setting.title = 'Site title'
        self.test_setting.email = 'initial@example.com'
        self.test_setting.site = default_site
        self.test_setting.save()

        self.login()

    def test_get_edit(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        # there should be a menu item highlighted as active
        self.assertContains(response, "menu-active")

    def test_non_existant_model(self):
        response = self.client.get(reverse('wagtailsettings:edit', args=['test', 'foo', 1]))
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


class TestMultiSite(BaseTestSettingView):
    def setUp(self):
        self.default_site = Site.objects.get(is_default_site=True)
        self.other_site = Site.objects.create(hostname='example.com', root_page=Page.objects.get(pk=2))
        self.login()

    def test_redirect_to_default(self):
        """
        Should redirect to the setting for the default site.
        """
        start_url = reverse('wagtailsettings:edit', args=[
            'tests', 'testsetting'])
        dest_url = 'http://testserver' + reverse('wagtailsettings:edit', args=[
            'tests', 'testsetting', self.default_site.pk])
        response = self.client.get(start_url, follow=True)
        self.assertRedirects(response, dest_url, status_code=302, fetch_redirect_response=False)

    def test_redirect_to_current(self):
        """
        Should redirect to the setting for the current site taken from the URL,
        by default
        """
        start_url = reverse('wagtailsettings:edit', args=[
            'tests', 'testsetting'])
        dest_url = 'http://example.com' + reverse('wagtailsettings:edit', args=[
            'tests', 'testsetting', self.other_site.pk])
        response = self.client.get(start_url, follow=True, HTTP_HOST=self.other_site.hostname)
        self.assertRedirects(response, dest_url, status_code=302, fetch_redirect_response=False)

    def test_with_no_current_site(self):
        """
        Redirection should not break if the current request does not correspond to a site
        """
        self.default_site.is_default_site = False
        self.default_site.save()

        start_url = reverse('wagtailsettings:edit', args=[
            'tests', 'testsetting'])
        response = self.client.get(start_url, follow=True, HTTP_HOST="noneoftheabove.example.com")
        self.assertEqual(302, response.redirect_chain[0][1])

    def test_switcher(self):
        """ Check that the switcher form exists in the page """
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="settings-site-switch"')

    def test_unknown_site(self):
        """ Check that unknown sites throw a 404 """
        response = self.get(site_pk=3)
        self.assertEqual(response.status_code, 404)

    def test_edit(self):
        """
        Check that editing settings in multi-site mode edits the correct
        setting, and leaves the other ones alone
        """
        TestSetting.objects.create(
            title='default',
            email='default@example.com',
            site=self.default_site)
        TestSetting.objects.create(
            title='other',
            email='other@example.com',
            site=self.other_site)
        response = self.post(site_pk=self.other_site.pk, post_data={
            'title': 'other-new', 'email': 'other-other@example.com'})
        self.assertEqual(response.status_code, 302)

        # Check that the correct setting was updated
        other_setting = TestSetting.for_site(self.other_site)
        self.assertEqual(other_setting.title, 'other-new')
        self.assertEqual(other_setting.email, 'other-other@example.com')

        # Check that the other setting was not updated
        default_setting = TestSetting.for_site(self.default_site)
        self.assertEqual(default_setting.title, 'default')
        self.assertEqual(default_setting.email, 'default@example.com')


class TestAdminPermission(TestCase, WagtailTestUtils):
    def test_registered_permission(self):
        permission = Permission.objects.get_by_natural_key(
            app_label='tests', model='testsetting', codename='change_testsetting')
        for fn in hooks.get_hooks('register_permissions'):
            if permission in fn():
                break
        else:
            self.fail('Change permission for tests.TestSetting not registered')
