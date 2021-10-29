from django.contrib.messages import get_messages
from django.test import TestCase, override_settings
from django.urls import reverse

from wagtail.admin.admin_url_finder import AdminURLFinder
from wagtail.core.models import Locale, Page
from wagtail.tests.utils import WagtailTestUtils


class TestLocaleIndexView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

    def get(self, params={}):
        return self.client.get(reverse('wagtaillocales:index'), params)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/generic/index.html')


class TestLocaleCreateView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()
        self.english = Locale.objects.get()

    def get(self, params={}):
        return self.client.get(reverse('wagtaillocales:add'), params)

    def post(self, post_data={}):
        return self.client.post(reverse('wagtaillocales:add'), post_data)

    def test_default_language(self):
        # we should have loaded with a single locale
        self.assertEqual(self.english.language_code, 'en')
        self.assertEqual(self.english.get_display_name(), "English")

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtaillocales/create.html')

        self.assertEqual(response.context['form'].fields['language_code'].choices, [
            ('fr', 'French')
        ])

    def test_create(self):
        response = self.post({
            'language_code': "fr",
        })

        # Should redirect back to index
        self.assertRedirects(response, reverse('wagtaillocales:index'))

        # Check that the locale was created
        self.assertTrue(Locale.objects.filter(language_code='fr').exists())

    def test_duplicate_not_allowed(self):
        response = self.post({
            'language_code': "en",
        })

        # Should return the form with errors
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'language_code', ['Select a valid choice. en is not one of the available choices.'])

    def test_language_code_must_be_in_settings(self):
        response = self.post({
            'language_code': "ja",
        })

        # Should return the form with errors
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'language_code', ['Select a valid choice. ja is not one of the available choices.'])


class TestLocaleEditView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.user = self.login()
        self.english = Locale.objects.get()

    def get(self, params=None, locale=None):
        locale = locale or self.english
        return self.client.get(reverse('wagtaillocales:edit', args=[locale.id]), params or {})

    def post(self, post_data=None, locale=None):
        post_data = post_data or {}
        locale = locale or self.english
        post_data.setdefault('language_code', locale.language_code)
        return self.client.post(reverse('wagtaillocales:edit', args=[locale.id]), post_data)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtaillocales/edit.html')

        self.assertEqual(response.context['form'].fields['language_code'].choices, [
            ('en', 'English'),  # Note: Current value is displayed even though it's in use
            ('fr', 'French')
        ])

        url_finder = AdminURLFinder(self.user)
        expected_url = '/admin/locales/%d/' % self.english.id
        self.assertEqual(url_finder.get_edit_url(self.english), expected_url)

    def test_invalid_language(self):
        invalid = Locale.objects.create(language_code='foo')

        response = self.get(locale=invalid)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtaillocales/edit.html')

        self.assertEqual(response.context['form'].fields['language_code'].choices, [
            (None, 'Select a new language'),  # This is shown instead of the current value if invalid
            ('fr', 'French')
        ])

    def test_edit(self):
        response = self.post({
            'language_code': 'fr',
        })

        # Should redirect back to index
        self.assertRedirects(response, reverse('wagtaillocales:index'))

        # Check that the locale was edited
        self.english.refresh_from_db()
        self.assertEqual(self.english.language_code, 'fr')

    def test_edit_duplicate_not_allowed(self):
        french = Locale.objects.create(language_code='fr')

        response = self.post({
            'language_code': "en",
        }, locale=french)

        # Should return the form with errors
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'language_code', ['Select a valid choice. en is not one of the available choices.'])

    def test_edit_language_code_must_be_in_settings(self):
        response = self.post({
            'language_code': "ja",
        })

        # Should return the form with errors
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'language_code', ['Select a valid choice. ja is not one of the available choices.'])


class TestLocaleDeleteView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()
        self.english = Locale.objects.get()

    def get(self, params={}, locale=None):
        locale = locale or self.english
        return self.client.get(reverse('wagtaillocales:delete', args=[locale.id]), params)

    def post(self, post_data={}, locale=None):
        locale = locale or self.english
        return self.client.post(reverse('wagtaillocales:delete', args=[locale.id]), post_data)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/generic/confirm_delete.html')

    def test_delete_locale(self):
        french = Locale.objects.create(language_code='fr')

        response = self.post(locale=french)

        # Should redirect back to index
        self.assertRedirects(response, reverse('wagtaillocales:index'))

        # Check that the locale was deleted
        self.assertFalse(Locale.objects.filter(language_code='fr').exists())

    def test_cannot_delete_locales_with_pages(self):
        # create a French locale so that the deletion is not rejected on grounds of being the only
        # existing locale
        Locale.objects.create(language_code='fr')

        response = self.post()

        self.assertEqual(response.status_code, 200)

        # Check error message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(messages[0].level_tag, 'error')
        self.assertEqual(messages[0].message, "This locale cannot be deleted because there are pages and/or other objects using it.\n\n\n\n\n")

        # Check that the locale was not deleted
        self.assertTrue(Locale.objects.filter(language_code='en').exists())

    @override_settings(
        LANGUAGE_CODE='de-at',
        WAGTAIL_CONTENT_LANGUAGES=[
            ('en', 'English'),
            ('fr', 'French'),
            ('de', 'German'),
            ('pl', 'Polish'),
            ('ja', 'Japanese')
        ]
    )
    def test_can_delete_default_locale(self):
        # The presence of the locale on the root page node (if that's the only thing using the
        # locale) should not prevent deleting it

        for lang in ('fr', 'de', 'pl', 'ja'):
            Locale.objects.create(language_code=lang)

        self.assertTrue(Page.get_first_root_node().locale.language_code, 'en')
        Page.objects.filter(depth__gt=1).delete()
        response = self.post()

        # Should redirect back to index
        self.assertRedirects(response, reverse('wagtaillocales:index'))

        # Check that the locale was deleted
        self.assertFalse(Locale.objects.filter(language_code='en').exists())

        # root node's locale should now have been reassigned to the one matching the current
        # LANGUAGE_CODE
        self.assertTrue(Page.get_first_root_node().locale.language_code, 'de')

    @override_settings(
        LANGUAGE_CODE='de-at',
        WAGTAIL_CONTENT_LANGUAGES=[
            ('en', 'English'),
            ('fr', 'French'),
            ('de', 'German'),
            ('pl', 'Polish'),
            ('ja', 'Japanese')
        ]
    )
    def test_can_delete_default_locale_when_language_code_has_no_locale(self):
        Locale.objects.create(language_code='fr')

        self.assertTrue(Page.get_first_root_node().locale.language_code, 'en')
        Page.objects.filter(depth__gt=1).delete()
        response = self.post()

        # Should redirect back to index
        self.assertRedirects(response, reverse('wagtaillocales:index'))

        # Check that the locale was deleted
        self.assertFalse(Locale.objects.filter(language_code='en').exists())

        # root node's locale should now have been reassigned to 'fr' despite that not matching
        # LANGUAGE_CODE (because it's the only remaining Locale record)
        self.assertTrue(Page.get_first_root_node().locale.language_code, 'fr')

    def test_cannot_delete_last_remaining_locale(self):
        Page.objects.filter(depth__gt=1).delete()

        response = self.post()

        self.assertEqual(response.status_code, 200)

        # Check error message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(messages[0].level_tag, 'error')
        self.assertEqual(messages[0].message, "This locale cannot be deleted because there are no other locales.\n\n\n\n\n")

        # Check that the locale was not deleted
        self.assertTrue(Locale.objects.filter(language_code='en').exists())
