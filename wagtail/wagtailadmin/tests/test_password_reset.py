from django.test import TestCase
from django.test.utils import override_settings
from django.core import mail

from wagtail.tests.utils import WagtailTestUtils
from wagtail.wagtailcore.models import Site


class TestUserPasswordReset(TestCase, WagtailTestUtils):
    fixtures = ['test.json']

    # need to clear urlresolver caches before/after tests, because we override ROOT_URLCONF
    # in some tests here
    def setUp(self):
        from django.core.urlresolvers import clear_url_caches
        clear_url_caches()

    def tearDown(self):
        from django.core.urlresolvers import clear_url_caches
        clear_url_caches()

    @override_settings(ROOT_URLCONF="wagtail.wagtailadmin.urls")
    def test_email_found_default_url(self):
        response = self.client.post('/password_reset/', {'email': 'siteeditor@example.com'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("testserver", mail.outbox[0].body)

    @override_settings(ROOT_URLCONF="wagtail.wagtailadmin.urls", BASE_URL='http://mysite.com')
    def test_email_found_base_url(self):
        response = self.client.post('/password_reset/', {'email': 'siteeditor@example.com'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("mysite.com", mail.outbox[0].body)
