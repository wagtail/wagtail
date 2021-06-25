import unittest

import pytz

from django import VERSION as DJANGO_VERSION
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth import views as auth_views
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

from wagtail.admin.localization import (
    WAGTAILADMIN_PROVIDED_LANGUAGES, get_available_admin_languages, get_available_admin_time_zones)
from wagtail.admin.views.account import account, profile_tab
from wagtail.images.tests.utils import get_test_image_file
from wagtail.tests.utils import WagtailTestUtils
from wagtail.users.models import UserProfile


class TestAuthentication(TestCase, WagtailTestUtils):
    """
    This tests that users can login and logout of the admin interface
    """
    def test_login_view(self):
        """
        This tests that the login view responds with a login page
        """
        # Get login page
        response = self.client.get(reverse('wagtailadmin_login'))

        # Check that the user received a login page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/login.html')

    def test_login_view_post(self):
        """
        This posts user credentials to the login view and checks that
        the user was logged in successfully
        """
        # Create user to log in with
        self.create_superuser(username='test', email='test@email.com', password='password')

        # Post credentials to the login page
        response = self.client.post(reverse('wagtailadmin_login'), {
            'username': 'test@email.com' if settings.AUTH_USER_MODEL == 'emailuser.EmailUser' else 'test',
            'password': 'password',

            # NOTE: This is set using a hidden field in reality
            'next': reverse('wagtailadmin_home'),
        })

        # Check that the user was redirected to the dashboard
        self.assertRedirects(response, reverse('wagtailadmin_home'))

        # Check that the user was logged in
        self.assertTrue('_auth_user_id' in self.client.session)
        self.assertEqual(
            str(self.client.session['_auth_user_id']),
            str(get_user_model().objects.get(email='test@email.com').pk)
        )

    def test_already_logged_in_redirect(self):
        """
        This tests that a user who is already logged in is automatically
        redirected to the admin dashboard if they try to access the login
        page
        """
        # Login
        self.login()

        # Get login page
        response = self.client.get(reverse('wagtailadmin_login'))

        # Check that the user was redirected to the dashboard
        self.assertRedirects(response, reverse('wagtailadmin_home'))

    def test_logged_in_as_non_privileged_user_doesnt_redirect(self):
        """
        This tests that if the user is logged in but hasn't got permission
        to access the admin, they are not redirected to the admin

        This tests issue #431
        """
        # Login as unprivileged user
        self.create_user(username='unprivileged', password='123')
        self.login(username='unprivileged', password='123')

        # Get login page
        response = self.client.get(reverse('wagtailadmin_login'))

        # Check that the user received a login page and was not redirected
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/login.html')

    def test_logout(self):
        """
        This tests that the user can logout
        """
        # Login
        self.login()

        # Get logout page
        response = self.client.get(reverse('wagtailadmin_logout'))

        # Check that the user was redirected to the login page
        self.assertRedirects(response, reverse('wagtailadmin_login'))

        # Check that the user was logged out
        self.assertFalse('_auth_user_id' in self.client.session)

    def test_not_logged_in_redirect(self):
        """
        This tests that a not logged in user is redirected to the
        login page
        """
        # Get dashboard
        response = self.client.get(reverse('wagtailadmin_home'))

        # Check that the user was redirected to the login page and that next was set correctly
        self.assertRedirects(response, reverse('wagtailadmin_login') + '?next=' + reverse('wagtailadmin_home'))

    def test_not_logged_in_gives_403_to_ajax_requests(self):
        """
        This tests that a not logged in user is given a 403 error on AJAX requests
        """
        # Get dashboard
        response = self.client.get(reverse('wagtailadmin_home'), HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        # AJAX requests should be given a 403 error instead of being redirected
        self.assertEqual(response.status_code, 403)

    def test_not_logged_in_redirect_default_settings(self):
        """
        This does the same as the above test but checks that it
        redirects to the correct place when the user has not set
        the LOGIN_URL setting correctly
        """
        # Get dashboard with default LOGIN_URL setting
        with self.settings(LOGIN_URL='django.contrib.auth.views.login'):
            response = self.client.get(reverse('wagtailadmin_home'))

        # Check that the user was redirected to the login page and that next was set correctly
        # Note: The user will be redirected to 'django.contrib.auth.views.login' but
        # this must be the same URL as 'wagtailadmin_login'
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('wagtailadmin_login') + '?next=' + reverse('wagtailadmin_home'))

    def test_logged_in_no_permission_redirect(self):
        """
        This tests that a logged in user without admin access permissions is
        redirected to the login page, with an error message
        """
        # Login as unprivileged user
        self.create_user(username='unprivileged', password='123')
        self.login(username='unprivileged', password='123')

        # Get dashboard
        response = self.client.get(reverse('wagtailadmin_home'), follow=True)

        # Check that the user was redirected to the login page and that next was set correctly
        self.assertRedirects(response, reverse('wagtailadmin_login') + '?next=' + reverse('wagtailadmin_home'))
        self.assertContains(response, 'You do not have permission to access the admin')

    def test_logged_in_no_permission_gives_403_to_ajax_requests(self):
        """
        This tests that a logged in user without admin access permissions is
        given a 403 error on ajax requests
        """
        # Login as unprivileged user
        self.create_user(username='unprivileged', password='123')
        self.login(username='unprivileged', password='123')

        # Get dashboard
        response = self.client.get(reverse('wagtailadmin_home'), HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        # AJAX requests should be given a 403 error instead of being redirected
        self.assertEqual(response.status_code, 403)


class TestAccountSectionUtilsMixin:
    def assertPanelActive(self, response, name):
        panels = set()
        for panelset in response.context['panels_by_tab'].values():
            for panel in panelset:
                panels.add(panel.name)
        self.assertIn(name, panels, "Panel %s not active in response" % name)

    def assertPanelNotActive(self, response, name):
        panels = set()
        for panelset in response.context['panels_by_tab'].values():
            for panel in panelset:
                panels.add(panel.name)
        self.assertNotIn(name, panels, "Panel %s active in response" % name)

    def post_form(self, extra_post_data):
        post_data = {
            'name_email-first_name': 'Test',
            'name_email-last_name': 'User',
            'name_email-email': self.user.email,
            'notifications-submitted_notifications': 'false',
            'notifications-approved_notifications': 'false',
            'notifications-rejected_notifications': 'true',
            'notifications-updated_comments_notifications': 'true',
            'locale-preferred_language': 'es',
            'locale-current_time_zone': 'Europe/London',
        }
        post_data.update(extra_post_data)
        return self.client.post(reverse('wagtailadmin_account'), post_data)


class TestAccountSection(TestCase, WagtailTestUtils, TestAccountSectionUtilsMixin):
    """
    This tests that the accounts section is working
    """
    def setUp(self):
        self.user = self.login()

    def test_account_view(self):
        """
        This tests that the accounts view responds with an index page
        """
        # Get account page
        response = self.client.get(reverse('wagtailadmin_account'))

        # Check that the user received an account page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/account/account.html')

        self.assertPanelActive(response, 'name_email')
        self.assertPanelActive(response, 'notifications')
        self.assertPanelActive(response, 'locale')
        self.assertPanelActive(response, 'password')

        # These fields may hide themselves
        self.assertContains(response, "Email:")
        self.assertContains(response, "Preferred language:")

        if settings.USE_TZ:
            self.assertContains(response, "Current time zone:")
        else:
            self.assertNotContains(response, "Current time zone:")

        # Form media should be included on the page
        self.assertContains(response, 'vendor/colorpicker.js')

    def test_change_name_post(self):
        response = self.post_form({
            'name_email-first_name': 'Fox',
            'name_email-last_name': 'Mulder',
        })

        # Check that the user was redirected to the account page
        self.assertRedirects(response, reverse('wagtailadmin_account'))

        # Check that the name was changed
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Fox')
        self.assertEqual(self.user.last_name, 'Mulder')

    def test_change_email_post(self):
        response = self.post_form({
            'name_email-email': 'test@email.com',
        })

        # Check that the user was redirected to the account page
        self.assertRedirects(response, reverse('wagtailadmin_account'))

        # Check that the email was changed
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'test@email.com')

    def test_change_email_not_valid(self):
        response = self.post_form({
            'name_email-email': 'test@email',
        })

        # Check that the user wasn't redirected
        self.assertEqual(response.status_code, 200)

        # Check that a validation error was raised
        self.assertTrue('email' in response.context['panels_by_tab'][profile_tab][0].get_form().errors.keys())

        # Check that the email was not changed
        self.user.refresh_from_db()
        self.assertNotEqual(self.user.email, 'test@email')

    @override_settings(WAGTAIL_EMAIL_MANAGEMENT_ENABLED=False)
    def test_with_email_management_disabled(self):
        # Get account page
        response = self.client.get(reverse('wagtailadmin_account'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/account/account.html')
        self.assertNotContains(response, "Email:")

    @override_settings(WAGTAIL_PASSWORD_MANAGEMENT_ENABLED=False)
    def test_account_view_with_password_management_disabled(self):
        # Get account page
        response = self.client.get(reverse('wagtailadmin_account'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/account/account.html')
        # Page should NOT contain a 'Change password' option
        self.assertNotContains(response, "Change password")

    @override_settings(WAGTAIL_PASSWORD_MANAGEMENT_ENABLED=False)
    def test_change_password_view_disabled(self):
        response = self.client.get(reverse('wagtailadmin_account'))
        self.assertPanelNotActive(response, 'password')

    def test_change_password(self):
        response = self.post_form({
            'password-old_password': 'password',
            'password-new_password1': 'newpassword',
            'password-new_password2': 'newpassword',
        })

        # Check that the user was redirected to the account page
        self.assertRedirects(response, reverse('wagtailadmin_account'))

        # Check that the password was changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpassword'))

    def test_change_password_post_password_mismatch(self):
        response = self.post_form({
            'password-old_password': 'password',
            'password-new_password1': 'newpassword',
            'password-new_password2': 'badpassword',
        })

        # Check that the user wasn't redirected
        self.assertEqual(response.status_code, 200)

        # Find password panel through context
        password_panel = None
        for panelset in response.context['panels_by_tab'].values():
            for panel in panelset:
                if panel.name == 'password':
                    password_panel = panel
                    break

        # Check that a validation error was raised
        password_form = password_panel.get_form()
        self.assertTrue('new_password2' in password_form.errors.keys())
        if DJANGO_VERSION >= (3, 0):
            self.assertTrue("The two password fields didn’t match." in password_form.errors['new_password2'])
        else:
            self.assertTrue("The two password fields didn't match." in password_form.errors['new_password2'])

        # Check that the password was not changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('password'))

    def test_change_notifications(self):
        response = self.post_form({
            'submitted_notifications': 'false',
            'approved_notifications': 'false',
            'rejected_notifications': 'true',
            'updated_comments_notifications': 'true',
        })

        # Check that the user was redirected to the account page
        self.assertRedirects(response, reverse('wagtailadmin_account'))

        profile = UserProfile.get_for_user(get_user_model().objects.get(pk=self.user.pk))

        # Check that the notification preferences are as submitted
        self.assertFalse(profile.submitted_notifications)
        self.assertFalse(profile.approved_notifications)
        self.assertTrue(profile.rejected_notifications)
        self.assertTrue(profile.updated_comments_notifications)

    def test_change_language_preferences(self):
        response = self.post_form({
            'locale-preferred_language': 'es',
        })

        # Check that the user was redirected to the account page
        self.assertRedirects(response, reverse('wagtailadmin_account'))

        profile = UserProfile.get_for_user(self.user)
        profile.refresh_from_db()

        # Check that the language preferences are stored
        self.assertEqual(profile.preferred_language, 'es')

        # check that the updated language preference is now indicated in HTML header
        response = self.client.get(reverse('wagtailadmin_home'))
        self.assertContains(response, '<html class="no-js" lang="es" dir="ltr">')

    def test_unset_language_preferences(self):
        profile = UserProfile.get_for_user(self.user)
        profile.preferred_language = 'en'
        profile.save()

        response = self.post_form({
            'locale-preferred_language': '',
        })

        # Check that the user was redirected to the account page
        self.assertRedirects(response, reverse('wagtailadmin_account'))

        # Check that the language preferences are stored
        profile.refresh_from_db()
        self.assertEqual(profile.preferred_language, '')

        # Check that the current language is assumed as English
        self.assertEqual(profile.get_preferred_language(), "en")

    @override_settings(WAGTAILADMIN_PERMITTED_LANGUAGES=[('en', 'English'), ('es', 'Spanish')])
    def test_available_admin_languages_with_permitted_languages(self):
        self.assertListEqual(get_available_admin_languages(), [('en', 'English'), ('es', 'Spanish')])

    def test_available_admin_languages_by_default(self):
        self.assertListEqual(get_available_admin_languages(), WAGTAILADMIN_PROVIDED_LANGUAGES)

    @override_settings(WAGTAILADMIN_PERMITTED_LANGUAGES=[('en', 'English')])
    def test_not_show_options_if_only_one_language_is_permitted(self):
        response = self.client.get(reverse('wagtailadmin_account'))
        self.assertNotContains(response, "Preferred language:")

    @unittest.skipUnless(settings.USE_TZ, "Timezone support is disabled")
    def test_change_current_time_zone(self):
        response = self.post_form({
            'locale-current_time_zone': 'Pacific/Fiji',
        })

        # Check that the user was redirected to the account page
        self.assertRedirects(response, reverse('wagtailadmin_account'))

        profile = UserProfile.get_for_user(self.user)
        profile.refresh_from_db()

        # Check that the current time zone is stored
        self.assertEqual(profile.current_time_zone, 'Pacific/Fiji')

    @unittest.skipUnless(settings.USE_TZ, "Timezone support is disabled")
    def test_unset_current_time_zone(self):
        response = self.post_form({
            'locale-current_time_zone': '',
        })

        # Check that the user was redirected to the account page
        self.assertRedirects(response, reverse('wagtailadmin_account'))

        profile = UserProfile.get_for_user(self.user)
        profile.refresh_from_db()

        # Check that the current time zone are stored
        self.assertEqual(profile.current_time_zone, '')

    @unittest.skipUnless(settings.USE_TZ, "Timezone support is disabled")
    @override_settings(WAGTAIL_USER_TIME_ZONES=['Africa/Addis_Ababa', 'America/Argentina/Buenos_Aires'])
    def test_available_admin_time_zones_with_permitted_time_zones(self):
        self.assertListEqual(get_available_admin_time_zones(),
                             ['Africa/Addis_Ababa', 'America/Argentina/Buenos_Aires'])

    @unittest.skipUnless(settings.USE_TZ, "Timezone support is disabled")
    def test_available_admin_time_zones_by_default(self):
        self.assertListEqual(get_available_admin_time_zones(), pytz.common_timezones)

    @unittest.skipUnless(settings.USE_TZ, "Timezone support is disabled")
    @override_settings(WAGTAIL_USER_TIME_ZONES=['Europe/London'])
    def test_not_show_options_if_only_one_time_zone_is_permitted(self):
        response = self.client.get(reverse('wagtailadmin_account'))
        self.assertNotContains(response, "Current time zone:")

    @unittest.skipIf(settings.USE_TZ, "Timezone support is enabled")
    def test_not_show_options_if_timezone_support_disabled(self):
        response = self.client.get(reverse('wagtailadmin_account'))
        self.assertNotContains(response, "Current time zone:")

    @unittest.skipUnless(settings.USE_TZ, "Timezone support is disabled")
    @override_settings(
        WAGTAIL_USER_TIME_ZONES=['Europe/London'],
        WAGTAILADMIN_PERMITTED_LANGUAGES=[('en', 'English')]
    )
    def test_doesnt_render_locale_panel_when_only_one_timezone_and_one_locale_permitted(self):
        response = self.client.get(reverse('wagtailadmin_account'))
        self.assertPanelNotActive(response, 'locale')

    def test_sensitive_post_parameters(self):
        request = RequestFactory().post('wagtailadmin_account', data={})
        request.user = self.user
        account(request)
        self.assertTrue(hasattr(request, 'sensitive_post_parameters'))
        self.assertEqual(request.sensitive_post_parameters, '__ALL__')


class TestAccountUploadAvatar(TestCase, WagtailTestUtils, TestAccountSectionUtilsMixin):
    def setUp(self):
        self.user = self.login()
        self.avatar = get_test_image_file()
        self.other_avatar = get_test_image_file()

    def test_account_view(self):
        """
        This tests that the account view renders a "Upload a profile picture:" field
        """
        response = self.client.get(reverse('wagtailadmin_account'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Upload a profile picture:")

    def test_set_custom_avatar_stores_and_get_custom_avatar(self):
        response = self.post_form({
            'avatar-avatar': SimpleUploadedFile('other.png', self.other_avatar.file.getvalue())
        })
        # Check that the user was redirected to the account page
        self.assertRedirects(response, reverse('wagtailadmin_account'))

        profile = UserProfile.get_for_user(self.user)
        profile.refresh_from_db()
        self.assertIn('other.png', profile.avatar.url)

    def test_user_upload_another_image_removes_previous_one(self):
        profile = UserProfile.get_for_user(self.user)
        profile.avatar = self.avatar
        profile.save()

        old_avatar_path = profile.avatar.path

        # Upload a new avatar
        response = self.post_form({
            'avatar-avatar': SimpleUploadedFile('other.png', self.other_avatar.file.getvalue())
        })
        # Check that the user was redirected to the account page
        self.assertRedirects(response, reverse('wagtailadmin_account'))

        # Check the avatar was changed
        profile.refresh_from_db()
        self.assertIn('other.png', profile.avatar.url)

        # Check old avatar doesn't exist anymore in filesystem
        with self.assertRaises(FileNotFoundError):
            open(old_avatar_path)

    def test_no_value_preserves_current_avatar(self):
        """
        Tests that submitting a blank value for avatar doesn't remove it.
        """
        profile = UserProfile.get_for_user(self.user)
        profile.avatar = self.avatar
        profile.save()

        # Upload a new avatar
        response = self.post_form({})
        # Check that the user was redirected to the account page
        self.assertRedirects(response, reverse('wagtailadmin_account'))

        # Check the avatar was changed
        profile.refresh_from_db()
        self.assertIn('test.png', profile.avatar.url)

    def test_clear_removes_current_avatar(self):
        """
        Tests that submitting a blank value for avatar doesn't remove it.
        """
        profile = UserProfile.get_for_user(self.user)
        profile.avatar = self.avatar
        profile.save()

        # Upload a new avatar
        response = self.post_form({
            'avatar-clear': 'on'
        })
        # Check that the user was redirected to the account page
        self.assertRedirects(response, reverse('wagtailadmin_account'))

        # Check the avatar was changed
        profile.refresh_from_db()
        self.assertIn('test.png', profile.avatar.url)


class TestAccountManagementForNonModerator(TestCase, WagtailTestUtils):
    """
    Tests of reduced-functionality for editors
    """
    def setUp(self):
        # Create a non-moderator user
        self.submitter = self.create_user('submitter', 'submitter@example.com', 'password')
        self.submitter.groups.add(Group.objects.get(name='Editors'))

        self.login(username='submitter', password='password')

    def test_notification_preferences_panel_reduced_for_non_moderators(self):
        """
        This tests that a user without publish permissions is not shown the
        notification preference for 'submitted' items
        """
        response = self.client.get(reverse('wagtailadmin_account'))

        # Find notifications panel through context
        notifications_panel = None
        for panelset in response.context['panels_by_tab'].values():
            for panel in panelset:
                if panel.name == 'notifications':
                    notifications_panel = panel
                    break

        notifications_form = notifications_panel.get_form()
        self.assertIn('approved_notifications', notifications_form.fields.keys())
        self.assertIn('rejected_notifications', notifications_form.fields.keys())
        self.assertNotIn('submitted_notifications', notifications_form.fields.keys())
        self.assertIn('updated_comments_notifications', notifications_form.fields.keys())


class TestAccountManagementForAdminOnlyUser(TestCase, WagtailTestUtils, TestAccountSectionUtilsMixin):
    """
    Tests for users with no edit/publish permissions at all
    """
    def setUp(self):
        # Create a non-moderator user
        admin_only_group = Group.objects.create(name='Admin Only')
        admin_only_group.permissions.add(Permission.objects.get(codename='access_admin'))

        self.admin_only_user = self.create_user(
            'admin_only_user',
            'admin_only_user@example.com',
            'password'
        )
        self.admin_only_user.groups.add(admin_only_group)

        self.login(username='admin_only_user', password='password')

    def test_notification_preferences_not_rendered_for_admin_only_users(self):
        """
        Test that the user is not shown the notification preferences panel
        """
        response = self.client.get(reverse('wagtailadmin_account'))
        self.assertPanelNotActive(response, 'notifications')


class TestPasswordReset(TestCase, WagtailTestUtils):
    """
    This tests that the password reset is working
    """
    def setUp(self):
        # Create a user
        self.create_superuser(username='test', email='test@email.com', password='password')

    def test_password_reset_view(self):
        """
        This tests that the password reset view returns a password reset page
        """
        # Get password reset page
        response = self.client.get(reverse('wagtailadmin_password_reset'))

        # Check that the user received a password reset page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/account/password_reset/form.html')

    def test_password_reset_view_post(self):
        """
        This posts an email address to the password reset view and
        checks that a password reset email was sent
        """
        # Post email address to password reset view
        post_data = {
            'email': 'test@email.com',
        }
        response = self.client.post(reverse('wagtailadmin_password_reset'), post_data)

        # Check that the user was redirected to the done page
        self.assertRedirects(response, reverse('wagtailadmin_password_reset_done'))

        # Check that a password reset email was sent to the user
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['test@email.com'])
        self.assertEqual(mail.outbox[0].subject, "Password reset")

    def test_password_reset_view_post_unknown_email(self):
        """
        This posts an unknown email address to the password reset view and
        checks that the password reset form raises a validation error
        """
        post_data = {
            'email': 'unknown@email.com',
        }
        response = self.client.post(reverse('wagtailadmin_password_reset'), post_data)

        # Check that the user was redirected to the done page
        self.assertRedirects(response,
                             reverse('wagtailadmin_password_reset_done'))

        # Check that an email was not sent
        self.assertEqual(len(mail.outbox), 0)

    def test_password_reset_view_post_invalid_email(self):
        """
        This posts an incalid email address to the password reset view and
        checks that the password reset form raises a validation error
        """
        post_data = {
            'email': 'Hello world!',
        }
        response = self.client.post(reverse('wagtailadmin_password_reset'), post_data)

        # Check that the user wasn't redirected
        self.assertEqual(response.status_code, 200)

        # Check that a validation error was raised
        self.assertTrue('email' in response.context['form'].errors.keys())
        self.assertTrue("Enter a valid email address." in response.context['form'].errors['email'])

        # Check that an email was not sent
        self.assertEqual(len(mail.outbox), 0)

    def setup_password_reset_confirm_tests(self):
        from django.utils.encoding import force_bytes, force_str
        from django.utils.http import urlsafe_base64_encode

        # Get user
        self.user = get_user_model().objects.get(email='test@email.com')

        # Generate a password reset token
        self.password_reset_token = PasswordResetTokenGenerator().make_token(self.user)

        # Generate a password reset uid
        self.password_reset_uid = force_str(urlsafe_base64_encode(force_bytes(self.user.pk)))

        # Create url_args
        if DJANGO_VERSION >= (3, 0):
            token = auth_views.PasswordResetConfirmView.reset_url_token
        else:
            token = auth_views.INTERNAL_RESET_URL_TOKEN

        self.url_kwargs = dict(uidb64=self.password_reset_uid, token=token)

        # Add token to session object
        s = self.client.session
        s.update({
            auth_views.INTERNAL_RESET_SESSION_TOKEN: self.password_reset_token,
        })
        s.save()

    def test_password_reset_confirm_view_invalid_link(self):
        """
        This tests that the password reset view shows an error message if the link is invalid
        """
        self.setup_password_reset_confirm_tests()

        # Create invalid url_args
        self.url_kwargs = dict(uidb64=self.password_reset_uid, token="invalid-token")

        # Get password reset confirm page
        response = self.client.get(reverse('wagtailadmin_password_reset_confirm', kwargs=self.url_kwargs))

        # Check that the user received a password confirm done page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/account/password_reset/confirm.html')
        self.assertFalse(response.context['validlink'])
        self.assertContains(response, 'The password reset link was invalid, possibly because it has already been used.')
        self.assertContains(response, 'Request a new password reset')

    def test_password_reset_confirm_view(self):
        """
        This tests that the password reset confirm view returns a password reset confirm page
        """
        self.setup_password_reset_confirm_tests()

        # Get password reset confirm page
        response = self.client.get(reverse('wagtailadmin_password_reset_confirm', kwargs=self.url_kwargs))

        # Check that the user received a password confirm done page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/account/password_reset/confirm.html')

    def test_password_reset_confirm_view_post(self):
        """
        This posts a new password to the password reset confirm view and checks
        that the users password was changed
        """
        self.setup_password_reset_confirm_tests()

        # Post new password to change password page
        post_data = {
            'new_password1': 'newpassword',
            'new_password2': 'newpassword',
        }
        response = self.client.post(reverse('wagtailadmin_password_reset_confirm', kwargs=self.url_kwargs), post_data)

        # Check that the user was redirected to the complete page
        self.assertRedirects(response, reverse('wagtailadmin_password_reset_complete'))

        # Check that the password was changed
        self.assertTrue(get_user_model().objects.get(email='test@email.com').check_password('newpassword'))

    def test_password_reset_confirm_view_post_password_mismatch(self):
        """
        This posts a two passwords that don't match to the password reset
        confirm view and checks that a validation error was raised
        """
        self.setup_password_reset_confirm_tests()

        # Post new password to change password page
        post_data = {
            'new_password1': 'newpassword',
            'new_password2': 'badpassword',
        }
        response = self.client.post(reverse('wagtailadmin_password_reset_confirm', kwargs=self.url_kwargs), post_data)

        # Check that the user wasn't redirected
        self.assertEqual(response.status_code, 200)

        # Check that a validation error was raised
        self.assertTrue('new_password2' in response.context['form'].errors.keys())

        if DJANGO_VERSION >= (3, 0):
            self.assertTrue("The two password fields didn’t match." in response.context['form'].errors['new_password2'])
        else:
            self.assertTrue("The two password fields didn't match." in response.context['form'].errors['new_password2'])

        # Check that the password was not changed
        self.assertTrue(get_user_model().objects.get(email='test@email.com').check_password('password'))

    def test_password_reset_done_view(self):
        """
        This tests that the password reset done view returns a password reset done page
        """
        # Get password reset done page
        response = self.client.get(reverse('wagtailadmin_password_reset_done'))

        # Check that the user received a password reset done page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/account/password_reset/done.html')

    def test_password_reset_complete_view(self):
        """
        This tests that the password reset complete view returns a password reset complete page
        """
        # Get password reset complete page
        response = self.client.get(reverse('wagtailadmin_password_reset_complete'))

        # Check that the user received a password reset complete page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/account/password_reset/complete.html')
