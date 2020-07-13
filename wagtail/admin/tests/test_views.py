from django.test import TestCase, override_settings
from django.urls import reverse

from wagtail.core.models import Page
from wagtail.tests.testapp.models import SimplePage
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
        self.client.login(username='test@email.com', password='password')

        response = self.client.get(reverse('wagtailadmin_login'))
        self.assertRedirects(response, reverse('wagtailadmin_home'))

    def test_already_authenticated_redirect_honour_redirect_get_parameter(self):
        self.client.login(username='test@email.com', password='password')

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


class TestAutocompleteView(TestCase):
    fixtures = ['test.json']

    def setUp(self):
        self.autocomplete_url = reverse('wagtailadmin_model_autocomplete')

    def test_response(self):
        url = self.autocomplete_url + "?type=tests.SimplePage"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        self.client.login(username='siteeditor', password='password')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        self.assertJSONEqual(response.content, {
            'items': [
                {'pk': page.pk, 'label': page.title} for page in SimplePage.objects.order_by('title')
            ]
        })

        page = SimplePage.objects.order_by('title').first()

        # check limits
        response = self.client.get(url + "&limit=1")
        self.assertJSONEqual(response.content, {'items': [
            {'pk': page.pk, 'label': page.title}
        ]})

        # check query
        response = self.client.get(url + "&query=about")
        self.assertJSONEqual(response.content, {'items': [
            {'pk': page.pk, 'label': page.title}
        ]})

        response = self.client.get(url + "&query=a+random+string+that+should+not+exist")
        self.assertJSONEqual(response.content, {'items': []})

        # test the non-default lookup field.
        response = self.client.get(url + "&lookup_fields=content&query=really+good")
        self.assertJSONEqual(response.content, {'items': [
            {'pk': page.pk, 'label': "About us"}
        ]})

        home_page = Page.objects.get(id=2)
        really_good_page = home_page.add_child(instance=SimplePage(title='Really good', content='random content'))

        # test the non-default lookup field.
        response = self.client.get(url + "&lookup_fields=title,content&query=really+good")
        self.assertJSONEqual(response.content, {'items': [
            {'pk': page.pk, 'label': "About us"},
            {'pk': really_good_page.pk, 'label': 'Really good'}
        ]})

    def test_invalid_model_raises_bad_http_request(self):
        self.client.login(username='siteeditor', password='password')

        # no query params
        response = self.client.get(self.autocomplete_url)
        self.assertEqual(response.status_code, 400)

        # bad model string
        response = self.client.get(self.autocomplete_url + "?type=foo")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content, b'Invalid model')

        # bad model lookup
        response = self.client.get(self.autocomplete_url + "?type=tests.SimplePage&lookup_fields=foo")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content, b'Invalid lookup field(s)')

        # finally, a good one
        response = self.client.get(self.autocomplete_url + "?type=tests.SimplePage")
        self.assertEqual(response.status_code, 200)
