from django.test import TestCase, override_settings
from django.urls import reverse

from wagtail.core.models import Page
from wagtail.tests.utils import WagtailTestUtils


class TestLoginView(TestCase, WagtailTestUtils):
    fixtures = ['test.json']

    def setUp(self):
        self.user = self.create_test_user()
        self.homepage = Page.objects.get(url_path='/home/')

    def test_success_redirect(self):
        response = self.client.post(reverse('wagtailadmin_login'), {
            'username': 'test@email.com',
            'password': 'password',
        })
        self.assertRedirects(response, reverse('wagtailadmin_home'))

    def test_success_redirect_honour_redirect_get_parameter(self):
        homepage_admin_url = reverse('wagtailadmin_pages:edit', args=[self.homepage.pk])
        login_url = reverse('wagtailadmin_login') + '?next={}'.format(homepage_admin_url)
        response = self.client.post(login_url, {
            'username': 'test@email.com',
            'password': 'password',
        })
        self.assertRedirects(response, homepage_admin_url)

    def test_success_redirect_honour_redirect_post_parameter(self):
        homepage_admin_url = reverse('wagtailadmin_pages:edit', args=[self.homepage.pk])
        response = self.client.post(reverse('wagtailadmin_login'), {
            'username': 'test@email.com',
            'password': 'password',
            'next': homepage_admin_url,
        })
        self.assertRedirects(response, homepage_admin_url)

    def test_already_authenticated_redirect(self):
        self.login(username='test@email.com', password='password')

        response = self.client.get(reverse('wagtailadmin_login'))
        self.assertRedirects(response, reverse('wagtailadmin_home'))

    def test_already_authenticated_redirect_honour_redirect_get_parameter(self):
        self.login(username='test@email.com', password='password')

        homepage_admin_url = reverse('wagtailadmin_pages:edit', args=[self.homepage.pk])
        login_url = reverse('wagtailadmin_login') + '?next={}'.format(homepage_admin_url)
        response = self.client.get(login_url)
        self.assertRedirects(response, homepage_admin_url)

    @override_settings(LANGUAGE_CODE='de')
    def test_language_code(self):
        response = self.client.get(reverse('wagtailadmin_login'))
        self.assertContains(response, '<html class="no-js" lang="de" dir="ltr">')

    @override_settings(LANGUAGE_CODE='he')
    def test_bidi_language_changes_dir_attribute(self):
        response = self.client.get(reverse('wagtailadmin_login'))
        self.assertContains(response, '<html class="no-js" lang="he" dir="rtl">')

    @override_settings(WAGTAILADMIN_USER_LOGIN_FORM="wagtail.admin.tests.test_forms.CustomLoginForm")
    def test_login_page_renders_extra_fields(self):
        response = self.client.get(reverse('wagtailadmin_login'))
        self.assertContains(response, '<input type="text" name="captcha" required id="id_captcha">')

    def test_session_expire_on_browser_close(self):
        self.client.post(reverse('wagtailadmin_login'), {
            'username': 'test@email.com',
            'password': 'password',
        })
        self.assertTrue(self.client.session.get_expire_at_browser_close())

    @override_settings(SESSION_COOKIE_AGE=7)
    def test_session_expiry_remember(self):
        self.client.post(reverse('wagtailadmin_login'), {
            'username': 'test@email.com',
            'password': 'password',
            'remember': True
        })
        self.assertFalse(self.client.session.get_expire_at_browser_close())
        self.assertEqual(self.client.session.get_expiry_age(), 7)
