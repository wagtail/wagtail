# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import json

from django.test import TestCase, override_settings
from django.core.urlresolvers import reverse
from django.core import mail
from django.contrib.auth import get_user_model

from taggit.models import Tag

from wagtail.tests.utils import WagtailTestUtils
from wagtail.wagtailcore.models import Page
from wagtail.wagtailadmin.utils import send_mail


class TestHome(TestCase, WagtailTestUtils):
    def setUp(self):
        # Login
        self.login()

    def test_simple(self):
        response = self.client.get(reverse('wagtailadmin_home'))
        self.assertEqual(response.status_code, 200)

    def test_admin_menu(self):
        response = self.client.get(reverse('wagtailadmin_home'))
        self.assertEqual(response.status_code, 200)
        # check that media attached to menu items is correctly pulled in
        self.assertContains(
            response,
            '<script type="text/javascript" src="/static/wagtailadmin/js/explorer-menu.js"></script>'
        )
        # check that custom menu items (including classname / attrs parameters) are pulled in
        self.assertContains(
            response,
            '<a href="http://www.tomroyal.com/teaandkittens/" class="icon icon-kitten" data-fluffy="yes">Kittens!</a>'
        )

        # check that is_shown is respected on menu items
        response = self.client.get(reverse('wagtailadmin_home') + '?hide-kittens=true')
        self.assertNotContains(
            response,
            '<a href="http://www.tomroyal.com/teaandkittens/" class="icon icon-kitten" data-fluffy="yes">Kittens!</a>'
        )

    def test_never_cache_header(self):
        # This tests that wagtailadmins global cache settings have been applied correctly
        response = self.client.get(reverse('wagtailadmin_home'))

        self.assertIn('private', response['Cache-Control'])
        self.assertIn('no-cache', response['Cache-Control'])
        self.assertIn('no-store', response['Cache-Control'])
        self.assertIn('max-age=0', response['Cache-Control'])

    def test_nonascii_email(self):
        # Test that non-ASCII email addresses don't break the admin; previously these would
        # cause a failure when generating Gravatar URLs
        get_user_model().objects.create_superuser(username='snowman', email='☃@thenorthpole.com', password='password')
        # Login
        self.client.login(username='snowman', password='password')
        response = self.client.get(reverse('wagtailadmin_home'))
        self.assertEqual(response.status_code, 200)


class TestEditorHooks(TestCase, WagtailTestUtils):
    def setUp(self):
        self.homepage = Page.objects.get(id=2)
        self.login()

    def test_editor_css_hooks_on_add(self):
        response = self.client.get(reverse('wagtailadmin_pages:add', args=('tests', 'simplepage', self.homepage.id)))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<link rel="stylesheet" href="/path/to/my/custom.css">')

    def test_editor_js_hooks_on_add(self):
        response = self.client.get(reverse('wagtailadmin_pages:add', args=('tests', 'simplepage', self.homepage.id)))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<script src="/path/to/my/custom.js"></script>')

    def test_editor_css_hooks_on_edit(self):
        response = self.client.get(reverse('wagtailadmin_pages:edit', args=(self.homepage.id, )))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<link rel="stylesheet" href="/path/to/my/custom.css">')

    def test_editor_js_hooks_on_edit(self):
        response = self.client.get(reverse('wagtailadmin_pages:edit', args=(self.homepage.id, )))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<script src="/path/to/my/custom.js"></script>')


class TestSendMail(TestCase):
    def test_send_email(self):
        send_mail("Test subject", "Test content", ["nobody@email.com"], "test@email.com")

        # Check that the email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Test subject")
        self.assertEqual(mail.outbox[0].body, "Test content")
        self.assertEqual(mail.outbox[0].to, ["nobody@email.com"])
        self.assertEqual(mail.outbox[0].from_email, "test@email.com")

    @override_settings(WAGTAILADMIN_NOTIFICATION_FROM_EMAIL='anothertest@email.com')
    def test_send_fallback_to_wagtailadmin_notification_from_email_setting(self):
        send_mail("Test subject", "Test content", ["nobody@email.com"])

        # Check that the email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Test subject")
        self.assertEqual(mail.outbox[0].body, "Test content")
        self.assertEqual(mail.outbox[0].to, ["nobody@email.com"])
        self.assertEqual(mail.outbox[0].from_email, "anothertest@email.com")

    @override_settings(DEFAULT_FROM_EMAIL='yetanothertest@email.com')
    def test_send_fallback_to_default_from_email_setting(self):
        send_mail("Test subject", "Test content", ["nobody@email.com"])

        # Check that the email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Test subject")
        self.assertEqual(mail.outbox[0].body, "Test content")
        self.assertEqual(mail.outbox[0].to, ["nobody@email.com"])
        self.assertEqual(mail.outbox[0].from_email, "yetanothertest@email.com")

    def test_send_default_from_email(self):
        send_mail("Test subject", "Test content", ["nobody@email.com"])

        # Check that the email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Test subject")
        self.assertEqual(mail.outbox[0].body, "Test content")
        self.assertEqual(mail.outbox[0].to, ["nobody@email.com"])
        self.assertEqual(mail.outbox[0].from_email, "webmaster@localhost")


class TestExplorerNavView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.homepage = Page.objects.get(id=2).specific
        self.login()

    def test_explorer_nav_view(self):
        response = self.client.get(reverse('wagtailadmin_explorer_nav'))

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed('wagtailadmin/shared/explorer_nav.html')
        self.assertEqual(response.context['nodes'][0][0], self.homepage)


class TestTagsAutocomplete(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()
        Tag.objects.create(name="Test", slug="test")

    def test_tags_autocomplete(self):
        response = self.client.get(reverse('wagtailadmin_tag_autocomplete'), {
            'term': 'test'
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        data = json.loads(response.content.decode('utf-8'))

        self.assertEqual(data, ['Test'])

    def test_tags_autocomplete_partial_match(self):
        response = self.client.get(reverse('wagtailadmin_tag_autocomplete'), {
            'term': 'te'
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        data = json.loads(response.content.decode('utf-8'))

        self.assertEqual(data, ['Test'])

    def test_tags_autocomplete_different_term(self):
        response = self.client.get(reverse('wagtailadmin_tag_autocomplete'), {
            'term': 'hello'
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        data = json.loads(response.content.decode('utf-8'))

        self.assertEqual(data, [])

    def test_tags_autocomplete_no_term(self):
        response = self.client.get(reverse('wagtailadmin_tag_autocomplete'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        data = json.loads(response.content.decode('utf-8'))

        self.assertEqual(data, [])


class TestUserPassesTestPermissionDecorator(TestCase):
    """
    Test for custom user_passes_test permission decorators.
    testapp_bob_only_zone is a view configured to only grant access to users with a first_name of Bob
    """
    def test_user_passes_test(self):
        # create and log in as a user called Bob
        get_user_model().objects.create_superuser(first_name='Bob', last_name='Mortimer', username='test', email='test@email.com', password='password')
        self.client.login(username='test', password='password')

        response = self.client.get(reverse('testapp_bob_only_zone'))
        self.assertEqual(response.status_code, 200)

    def test_user_fails_test(self):
        # create and log in as a user not called Bob
        get_user_model().objects.create_superuser(first_name='Vic', last_name='Reeves', username='test', email='test@email.com', password='password')
        self.client.login(username='test', password='password')

        response = self.client.get(reverse('testapp_bob_only_zone'))
        self.assertRedirects(response, reverse('wagtailadmin_home'))
