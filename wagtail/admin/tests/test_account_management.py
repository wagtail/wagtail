import os
import tempfile

import pytz

from django import VERSION as DJANGO_VERSION
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth import views as auth_views
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core import mail
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse
from django.utils.translation import get_language

from wagtail.admin.localization import (
    WAGTAILADMIN_PROVIDED_LANGUAGES, get_available_admin_languages, get_available_admin_time_zones)
from wagtail.admin.views.account import change_password
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


class TestAccountSection(TestCase, WagtailTestUtils):
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
        # Page should contain a 'Change password' option
        self.assertContains(response, "Change password")
        # Page should contain a 'Change email' option
        self.assertContains(response, "Change email")

    def test_change_email_view(self):
        """
        This tests that the change email view responds with a change email page
        """
        # Get change email page
        response = self.client.get(reverse('wagtailadmin_account_change_email'))

        # Check that the user received a change email page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/account/change_email.html')

    def test_change_email_post(self):
        post_data = {
            'email': 'test@email.com'
        }

        response = self.client.post(reverse('wagtailadmin_account_change_email'), post_data)

        # Check that the user was redirected to the account page
        self.assertRedirects(response, reverse('wagtailadmin_account'))

        # Check that the email was changed
        self.assertEqual(get_user_model().objects.get(pk=self.user.pk).email, post_data['email'])

    def test_change_email_not_valid(self):
        post_data = {
            'email': 'test@email'
        }

        response = self.client.post(reverse('wagtailadmin_account_change_email'), post_data)

        # Check that the user wasn't redirected
        self.assertEqual(response.status_code, 200)

        # Check that a validation error was raised
        self.assertTrue('email' in response.context['form'].errors.keys())

        # Check that the password was not changed
        self.assertNotEqual(get_user_model().objects.get(pk=self.user.pk).email, post_data['email'])

    @override_settings(WAGTAIL_EMAIL_MANAGEMENT_ENABLED=False)
    def test_account_view_with_email_management_disabled(self):
        # Get account page
        response = self.client.get(reverse('wagtailadmin_account'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/account/account.html')
        # Page should NOT contain a 'Change email' option
        self.assertNotContains(response, "Change email")

    @override_settings(WAGTAIL_EMAIL_MANAGEMENT_ENABLED=False)
    def test_change_email_view_disabled(self):
        """
        This tests that the change email view responds with a 404
        when setting WAGTAIL_EMAIL_MANAGEMENT_ENABLED is False
        """
        # Get change email page
        response = self.client.get(reverse('wagtailadmin_account_change_email'))

        # Check that the user received a 404
        self.assertEqual(response.status_code, 404)

    @override_settings(WAGTAIL_PASSWORD_MANAGEMENT_ENABLED=False)
    def test_account_view_with_password_management_disabled(self):
        # Get account page
        response = self.client.get(reverse('wagtailadmin_account'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/account/account.html')
        # Page should NOT contain a 'Change password' option
        self.assertNotContains(response, "Change password")

    def test_change_password_view(self):
        """
        This tests that the change password view responds with a change password page
        """
        # Get change password page
        response = self.client.get(reverse('wagtailadmin_account_change_password'))

        # Check that the user received a change password page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/account/change_password.html')

    @override_settings(WAGTAIL_PASSWORD_MANAGEMENT_ENABLED=False)
    def test_change_password_view_disabled(self):
        """
        This tests that the change password view responds with a 404
        when setting WAGTAIL_PASSWORD_MANAGEMENT_ENABLED is False
        """
        # Get change password page
        response = self.client.get(reverse('wagtailadmin_account_change_password'))

        # Check that the user received a 404
        self.assertEqual(response.status_code, 404)

    def test_change_password_view_post(self):
        """
        This posts a new password to the change password view and checks
        that the users password was changed
        """
        # Post new password to change password page
        post_data = {
            'old_password': 'password',
            'new_password1': 'newpassword',
            'new_password2': 'newpassword',
        }
        response = self.client.post(reverse('wagtailadmin_account_change_password'), post_data)

        # Check that the user was redirected to the account page
        self.assertRedirects(response, reverse('wagtailadmin_account'))

        # Check that the password was changed
        self.assertTrue(get_user_model().objects.get(pk=self.user.pk).check_password('newpassword'))

    def test_change_password_view_post_password_mismatch(self):
        """
        This posts a two passwords that don't match to the password change
        view and checks that a validation error was raised
        """
        # Post new password to change password page
        post_data = {
            'new_password1': 'newpassword',
            'new_password2': 'badpassword',
        }
        response = self.client.post(reverse('wagtailadmin_account_change_password'), post_data)

        # Check that the user wasn't redirected
        self.assertEqual(response.status_code, 200)

        # Check that a validation error was raised
        self.assertTrue('new_password2' in response.context['form'].errors.keys())
        if DJANGO_VERSION >= (3, 0):
            self.assertTrue("The two password fields didn’t match." in response.context['form'].errors['new_password2'])
        else:
            self.assertTrue("The two password fields didn't match." in response.context['form'].errors['new_password2'])

        # Check that the password was not changed
        self.assertTrue(get_user_model().objects.get(pk=self.user.pk).check_password('password'))

    def test_notification_preferences_view(self):
        """
        This tests that the notification preferences view responds with the
        notification preferences page
        """
        # Get notification preferences page
        response = self.client.get(reverse('wagtailadmin_account_notification_preferences'))

        # Check that the user received a notification preferences page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/account/notification_preferences.html')

    def test_notification_preferences_view_post(self):
        """
        This posts to the notification preferences view and checks that the
        user's profile is updated
        """
        # Post new values to the notification preferences page
        post_data = {
            'submitted_notifications': 'false',
            'approved_notifications': 'false',
            'rejected_notifications': 'true',
        }
        response = self.client.post(reverse('wagtailadmin_account_notification_preferences'), post_data)

        # Check that the user was redirected to the account page
        self.assertRedirects(response, reverse('wagtailadmin_account'))

        profile = UserProfile.get_for_user(get_user_model().objects.get(pk=self.user.pk))

        # Check that the notification preferences are as submitted
        self.assertFalse(profile.submitted_notifications)
        self.assertFalse(profile.approved_notifications)
        self.assertTrue(profile.rejected_notifications)

    def test_language_preferences_view(self):
        """
        This tests that the language preferences view responds with an index page
        """
        # Get account page
        response = self.client.get(reverse('wagtailadmin_account_language_preferences'))

        # Check that the user received an account page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/account/language_preferences.html')

        # Page should contain a 'Language Preferences' title
        self.assertContains(response, "Language Preferences")

        # check that current language preference is indicated in HTML header
        self.assertContains(response, '<html class="no-js" lang="en" dir="ltr">')

    def test_language_preferences_view_post(self):
        """
        This posts to the language preferences view and checks that the
        user profile is updated
        """
        # Post new values to the language preferences page
        post_data = {
            'preferred_language': 'es'
        }
        response = self.client.post(reverse('wagtailadmin_account_language_preferences'), post_data)

        # Check that the user was redirected to the account page
        self.assertRedirects(response, reverse('wagtailadmin_account'))

        profile = UserProfile.get_for_user(get_user_model().objects.get(pk=self.user.pk))

        # Check that the language preferences are stored
        self.assertEqual(profile.preferred_language, 'es')

        # check that the updated language preference is now indicated in HTML header
        response = self.client.get(reverse('wagtailadmin_home'))
        self.assertContains(response, '<html class="no-js" lang="es" dir="ltr">')

    def test_unset_language_preferences(self):
        # Post new values to the language preferences page
        post_data = {
            'preferred_language': ''
        }
        response = self.client.post(reverse('wagtailadmin_account_language_preferences'), post_data)

        # Check that the user was redirected to the account page
        self.assertRedirects(response, reverse('wagtailadmin_account'))

        profile = UserProfile.get_for_user(get_user_model().objects.get(pk=self.user.pk))

        # Check that the language preferences are stored
        self.assertEqual(profile.preferred_language, '')

        # Check that the current language is assumed as English
        self.assertEqual(profile.get_preferred_language(), "en")

    def test_language_preferences_reapplies_original_language(self):
        post_data = {
            'preferred_language': 'es'
        }
        response = self.client.post(reverse('wagtailadmin_account_language_preferences'), post_data)
        self.assertRedirects(response, reverse('wagtailadmin_account'))

        self.assertEqual(get_language(), "en")

    def test_change_name(self):
        """
        This tests that the change name view responds with a change name page
        """
        # Get change name page
        response = self.client.get(reverse('wagtailadmin_account_change_name'))

        # Check that the user received a change name page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/account/change_name.html')

    def test_change_name_post(self):
        post_data = {
            'first_name': 'Fox',
            'last_name': 'Mulder',
        }
        response = self.client.post(reverse('wagtailadmin_account_change_name'), post_data)

        # Check that the user was redirected to the account page
        self.assertRedirects(response, reverse('wagtailadmin_account'))

        # Check that the name was changed
        self.assertEqual(get_user_model().objects.get(pk=self.user.pk).first_name, post_data['first_name'])
        self.assertEqual(get_user_model().objects.get(pk=self.user.pk).last_name, post_data['last_name'])

    @override_settings(WAGTAILADMIN_PERMITTED_LANGUAGES=[('en', 'English'), ('es', 'Spanish')])
    def test_available_admin_languages_with_permitted_languages(self):
        self.assertListEqual(get_available_admin_languages(), [('en', 'English'), ('es', 'Spanish')])

    def test_available_admin_languages_by_default(self):
        self.assertListEqual(get_available_admin_languages(), WAGTAILADMIN_PROVIDED_LANGUAGES)

    @override_settings(WAGTAILADMIN_PERMITTED_LANGUAGES=[('en', 'English')])
    def test_not_show_options_if_only_one_language_is_permitted(self):
        response = self.client.post(reverse('wagtailadmin_account'))
        self.assertNotContains(response, 'Language Preferences')

    def test_current_time_zone_view(self):
        """
        This tests that the current time zone view responds with an index page
        """
        # Get account page
        response = self.client.get(reverse('wagtailadmin_account_current_time_zone'))

        # Check that the user received an account page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/account/current_time_zone.html')

        # Page should contain a 'Set Time Zone' title
        self.assertContains(response, "Set Time Zone")

    def test_current_time_zone_view_post(self):
        """
        This posts to the current time zone view and checks that the
        user profile is updated
        """
        # Post new values to the current time zone page
        post_data = {
            'current_time_zone': 'Pacific/Fiji'
        }
        response = self.client.post(reverse('wagtailadmin_account_current_time_zone'), post_data)

        # Check that the user was redirected to the account page
        self.assertRedirects(response, reverse('wagtailadmin_account'))

        profile = UserProfile.get_for_user(get_user_model().objects.get(pk=self.user.pk))

        # Check that the current time zone is stored
        self.assertEqual(profile.current_time_zone, 'Pacific/Fiji')

    def test_unset_current_time_zone(self):
        # Post new values to the current time zone page
        post_data = {
            'current_time_zone': ''
        }
        response = self.client.post(reverse('wagtailadmin_account_current_time_zone'), post_data)

        # Check that the user was redirected to the account page
        self.assertRedirects(response, reverse('wagtailadmin_account'))

        profile = UserProfile.get_for_user(get_user_model().objects.get(pk=self.user.pk))

        # Check that the current time zone are stored
        self.assertEqual(profile.current_time_zone, '')

    @override_settings(WAGTAIL_USER_TIME_ZONES=['Africa/Addis_Ababa', 'America/Argentina/Buenos_Aires'])
    def test_available_admin_time_zones_with_permitted_time_zones(self):
        self.assertListEqual(get_available_admin_time_zones(),
                             ['Africa/Addis_Ababa', 'America/Argentina/Buenos_Aires'])

    def test_available_admin_time_zones_by_default(self):
        self.assertListEqual(get_available_admin_time_zones(), pytz.common_timezones)

    @override_settings(WAGTAIL_USER_TIME_ZONES=['Europe/London'])
    def test_not_show_options_if_only_one_time_zone_is_permitted(self):
        response = self.client.post(reverse('wagtailadmin_account'))
        self.assertNotContains(response, 'Set Time Zone')


class TestAvatarSection(TestCase, WagtailTestUtils):
    def _create_image(self):
        from PIL import Image

        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            image = Image.new('RGB', (200, 200), 'white')
            image.save(f, 'JPEG')

        return open(f.name, mode='rb')

    def setUp(self):
        self.user = self.login()
        self.avatar = self._create_image()
        self.other_avatar = self._create_image()

    def tearDown(self):
        self.avatar.close()
        self.other_avatar.close()

    def test_avatar_preferences_view(self):
        """
        This tests that the change user profile(avatar) view responds with an index page
        """
        response = self.client.get(reverse('wagtailadmin_account_change_avatar'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/account/change_avatar.html')
        self.assertContains(response, "Change profile picture")

    def test_set_custom_avatar_stores_and_get_custom_avatar(self):
        response = self.client.post(reverse('wagtailadmin_account_change_avatar'),
                                    {'avatar': self.avatar},
                                    follow=True)

        self.assertEqual(response.status_code, 200)

        profile = UserProfile.get_for_user(get_user_model().objects.get(pk=self.user.pk))
        self.assertIn(os.path.basename(self.avatar.name), profile.avatar.url)

    def test_user_upload_another_image_removes_previous_one(self):
        response = self.client.post(reverse('wagtailadmin_account_change_avatar'),
                                    {'avatar': self.avatar},
                                    follow=True)
        self.assertEqual(response.status_code, 200)

        profile = UserProfile.get_for_user(get_user_model().objects.get(pk=self.user.pk))
        old_avatar_path = profile.avatar.path

        # Upload a new avatar
        new_response = self.client.post(reverse('wagtailadmin_account_change_avatar'),
                                        {'avatar': self.other_avatar},
                                        follow=True)
        self.assertEqual(new_response.status_code, 200)

        # Check old avatar doesn't exist anymore in filesystem
        with self.assertRaises(FileNotFoundError):
            open(old_avatar_path)


class TestAccountManagementForNonModerator(TestCase, WagtailTestUtils):
    """
    Tests of reduced-functionality for editors
    """
    def setUp(self):
        # Create a non-moderator user
        self.submitter = self.create_user('submitter', 'submitter@example.com', 'password')
        self.submitter.groups.add(Group.objects.get(name='Editors'))

        self.login(username='submitter', password='password')

    def test_notification_preferences_form_is_reduced_for_non_moderators(self):
        """
        This tests that a user without publish permissions is not shown the
        notification preference for 'submitted' items
        """
        response = self.client.get(reverse('wagtailadmin_account_notification_preferences'))
        self.assertIn('approved_notifications', response.context['form'].fields.keys())
        self.assertIn('rejected_notifications', response.context['form'].fields.keys())
        self.assertNotIn('submitted_notifications', response.context['form'].fields.keys())


class TestAccountManagementForAdminOnlyUser(TestCase, WagtailTestUtils):
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

    def test_notification_preferences_view_redirects_for_admin_only_users(self):
        """
        Test that the user is not shown the notification preferences view but instead
        redirected to the account page
        """
        response = self.client.get(reverse('wagtailadmin_account_notification_preferences'))
        self.assertRedirects(response, reverse('wagtailadmin_account'))

    def test_notification_preferences_link_not_shown_for_admin_only_users(self):
        """
        Test that the user is not even shown the link to the notification
        preferences view
        """
        expected_url = reverse('wagtailadmin_account_notification_preferences')

        response = self.client.get(reverse('wagtailadmin_account'))
        account_urls = [item['url'] for item in response.context['items']]
        self.assertFalse(expected_url in account_urls)
        self.assertNotContains(response, expected_url)
        # safety check that checking for absence/presence of urls works
        self.assertContains(response, reverse('wagtailadmin_home'))


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

    def test_password_reset_sensitive_post_parameters(self):
        request = RequestFactory().post('wagtailadmin_password_reset_confirm', data={})
        request.user = get_user_model().objects.get(email='test@email.com')
        change_password(request)
        self.assertTrue(hasattr(request, 'sensitive_post_parameters'))
        self.assertEqual(request.sensitive_post_parameters, '__ALL__')
