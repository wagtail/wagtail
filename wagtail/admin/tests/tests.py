# -*- coding: utf-8 -*-

import json
import unittest

from django import VERSION as DJANGO_VERSION
from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.core import mail
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from taggit.models import Tag

from wagtail.admin.auth import user_has_any_page_permission
from wagtail.admin.mail import send_mail
from wagtail.admin.menu import MenuItem
from wagtail.core.models import Page
from wagtail.tests.testapp.models import RestaurantTag
from wagtail.tests.utils import WagtailTestUtils


class TestHome(TestCase, WagtailTestUtils):
    def setUp(self):
        # Login
        self.login()

    def test_simple(self):
        response = self.client.get(reverse('wagtailadmin_home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Welcome to the Test Site Wagtail CMS")

    def test_admin_menu(self):
        response = self.client.get(reverse('wagtailadmin_home'))
        self.assertEqual(response.status_code, 200)
        # check that media attached to menu items is correctly pulled in
        if DJANGO_VERSION >= (3, 1):
            self.assertContains(
                response,
                '<script src="/static/testapp/js/kittens.js"></script>',
                html=True
            )
        else:
            self.assertContains(
                response,
                '<script type="text/javascript" src="/static/testapp/js/kittens.js"></script>',
                html=True
            )

        # check that custom menu items (including classname / attrs parameters) are pulled in
        self.assertContains(
            response,
            '<a href="http://www.tomroyal.com/teaandkittens/" class="icon icon-kitten" data-fluffy="yes">Kittens!</a>',
            html=True
        )

        # Check that the explorer menu item is here, with the right start page.
        self.assertContains(
            response,
            'data-explorer-start-page="1"'
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

        self.assertIn('no-cache', response['Cache-Control'])
        self.assertIn('no-store', response['Cache-Control'])
        self.assertIn('max-age=0', response['Cache-Control'])
        self.assertIn('must-revalidate', response['Cache-Control'])

    @unittest.skipIf(settings.AUTH_USER_MODEL == 'emailuser.EmailUser', "Only applicable to CustomUser")
    def test_nonascii_email(self):
        # Test that non-ASCII email addresses don't break the admin; previously these would
        # cause a failure when generating Gravatar URLs
        self.create_superuser(username='snowman', email='☃@thenorthpole.com', password='password')
        # Login
        self.assertTrue(self.client.login(username='snowman', password='password'))
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

    def test_send_html_email(self):
        """Test that the kwarg 'html_message' works as expected on send_mail by creating 'alternatives' on the EmailMessage object"""

        send_mail("Test HTML subject", "TEXT content", ["has.html@email.com"], html_message="<h2>Test HTML content</h2>")
        send_mail("Test TEXT subject", "TEXT content", ["mr.plain.text@email.com"])

        # Check that the emails were sent
        self.assertEqual(len(mail.outbox), 2)

        # check that the first email is the HTML email
        email_message = mail.outbox[0]
        self.assertEqual(email_message.subject, "Test HTML subject")
        self.assertEqual(email_message.alternatives, [('<h2>Test HTML content</h2>', 'text/html')])
        self.assertEqual(email_message.body, "TEXT content")  # note: plain text will alwasy be added to body, even with alternatives
        self.assertEqual(email_message.to, ["has.html@email.com"])

        # confirm that without html_message kwarg we do not get 'alternatives'
        email_message = mail.outbox[1]
        self.assertEqual(email_message.subject, "Test TEXT subject")
        self.assertEqual(email_message.alternatives, [])
        self.assertEqual(email_message.body, "TEXT content")
        self.assertEqual(email_message.to, ["mr.plain.text@email.com"])


class TestTagsAutocomplete(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()
        Tag.objects.create(name="Test", slug="test")
        RestaurantTag.objects.create(name="Italian", slug="italian")
        RestaurantTag.objects.create(name="Indian", slug="indian")

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

    def test_tags_autocomplete_custom_model(self):
        response = self.client.get(
            reverse('wagtailadmin_tag_model_autocomplete', args=('tests', 'restauranttag')),
            {'term': 'ital'}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        data = json.loads(response.content.decode('utf-8'))

        self.assertEqual(data, ['Italian'])

        # should not return results from the standard Tag model
        response = self.client.get(
            reverse('wagtailadmin_tag_model_autocomplete', args=('tests', 'restauranttag')),
            {'term': 'test'}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        data = json.loads(response.content.decode('utf-8'))

        self.assertEqual(data, [])


class TestMenuItem(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()
        response = self.client.get(reverse('wagtailadmin_home'))
        self.request = response.wsgi_request

    def test_menuitem_reverse_lazy_url_pass(self):
        menuitem = MenuItem(_('Test'), reverse_lazy('wagtailadmin_home'))
        self.assertEqual(menuitem.is_active(self.request), True)


class TestUserPassesTestPermissionDecorator(TestCase, WagtailTestUtils):
    """
    Test for custom user_passes_test permission decorators.
    testapp_bob_only_zone is a view configured to only grant access to users with a first_name of Bob
    """
    def test_user_passes_test(self):
        # create and log in as a user called Bob
        self.create_superuser(first_name='Bob', last_name='Mortimer', username='test', password='password')
        self.login(username='test', password='password')

        response = self.client.get(reverse('testapp_bob_only_zone'))
        self.assertEqual(response.status_code, 200)

    def test_user_fails_test(self):
        # create and log in as a user not called Bob
        self.create_superuser(first_name='Vic', last_name='Reeves', username='test', password='password')
        self.login(username='test', password='password')

        response = self.client.get(reverse('testapp_bob_only_zone'))
        self.assertRedirects(response, reverse('wagtailadmin_home'))

    def test_user_fails_test_ajax(self):
        # create and log in as a user not called Bob
        self.create_superuser(first_name='Vic', last_name='Reeves', username='test', password='password')
        self.login(username='test', password='password')

        response = self.client.get(reverse('testapp_bob_only_zone'), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 403)


class TestUserHasAnyPagePermission(TestCase, WagtailTestUtils):
    def test_superuser(self):
        user = self.create_superuser(
            username='superuser', email='admin@example.com', password='p')
        self.assertTrue(user_has_any_page_permission(user))

    def test_inactive_superuser(self):
        user = self.create_superuser(
            username='superuser', email='admin@example.com', password='p')
        user.is_active = False
        self.assertFalse(user_has_any_page_permission(user))

    def test_editor(self):
        user = self.create_user(
            username='editor', email='ed@example.com', password='p')
        editors = Group.objects.get(name='Editors')
        user.groups.add(editors)
        self.assertTrue(user_has_any_page_permission(user))

    def test_moderator(self):
        user = self.create_user(
            username='moderator', email='mod@example.com', password='p')
        editors = Group.objects.get(name='Moderators')
        user.groups.add(editors)
        self.assertTrue(user_has_any_page_permission(user))

    def test_no_permissions(self):
        user = self.create_user(
            username='pleb', email='pleb@example.com', password='p')
        user.user_permissions.add(
            Permission.objects.get(content_type__app_label='wagtailadmin', codename='access_admin')
        )
        self.assertFalse(user_has_any_page_permission(user))


class Test404(TestCase, WagtailTestUtils):
    def test_admin_404_template_used_append_slash_true(self):
        self.login()
        with self.settings(APPEND_SLASH=True):
            response = self.client.get('/admin/sdfgdsfgdsfgsdf', follow=True)

            # Check 404 error after CommonMiddleware redirect
            self.assertEqual(response.status_code, 404)
            self.assertTemplateUsed(response, 'wagtailadmin/404.html')

    def test_not_logged_in_redirect(self):
        response = self.client.get('/admin/sdfgdsfgdsfgsdf/')

        # Check that the user was redirected to the login page and that next was set correctly
        self.assertRedirects(response, reverse('wagtailadmin_login') + '?next=/admin/sdfgdsfgdsfgsdf/')


class TestAdminURLAppendSlash(TestCase, WagtailTestUtils):
    def setUp(self):
        # Find root page
        self.root_page = Page.objects.get(id=2)

    def test_return_correct_view_for_correct_url_without_ending_slash(self):
        self.login()
        with self.settings(APPEND_SLASH=True):
            # Remove trailing slash from URL
            response = self.client.get(reverse('wagtailadmin_explore_root')[:-1], follow=True)

            # Check that correct page is returned after CommonMiddleware redirect
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'wagtailadmin/pages/index.html')
            self.assertEqual(Page.objects.get(id=1), response.context['parent_page'])
            self.assertTrue(response.context['pages'].paginator.object_list.filter(id=self.root_page.id).exists())


class TestRemoveStaleContentTypes(TestCase):
    def test_remove_stale_content_types_preserves_access_admin_permission(self):
        call_command('remove_stale_contenttypes', interactive=False)
        self.assertTrue(
            Permission.objects.filter(content_type__app_label='wagtailadmin', codename='access_admin').exists()
        )
