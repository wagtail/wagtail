from __future__ import unicode_literals

from django.test import TestCase, override_settings
from django.core.urlresolvers import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core import mail

from wagtail.tests.utils import WagtailTestUtils
from wagtail.wagtailusers.models import UserProfile


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

        # Check that the user recieved a login page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/login.html')

    def test_login_view_post(self):
        """
        This posts user credentials to the login view and checks that
        the user was logged in successfully
        """
        # Create user to log in with
        get_user_model().objects.create_superuser(username='test', email='test@email.com', password='password')

        # Post credentials to the login page
        response = self.client.post(reverse('wagtailadmin_login'), {
            'username': 'test',
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
            str(get_user_model().objects.get(username='test').id)
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
        get_user_model().objects.create(username='unprivileged', password='123')
        self.client.login(username='unprivileged', password='123')

        # Get login page
        response = self.client.get(reverse('wagtailadmin_login'))

        # Check that the user recieved a login page and was not redirected
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


class TestAccountSection(TestCase, WagtailTestUtils):
    """
    This tests that the accounts section is working
    """
    def setUp(self):
        self.login()

    def test_account_view(self):
        """
        This tests that the accounts view responds with an index page
        """
        # Get account page
        response = self.client.get(reverse('wagtailadmin_account'))

        # Check that the user recieved an account page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/account/account.html')
        # Page should contain a 'Change password' option
        self.assertContains(response, "Change password")

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

        # Check that the user recieved a change password page
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

        # Check that the user recieved a 404
        self.assertEqual(response.status_code, 404)

    def test_change_password_view_post(self):
        """
        This posts a new password to the change password view and checks
        that the users password was changed
        """
        # Post new password to change password page
        post_data = {
            'new_password1': 'newpassword',
            'new_password2': 'newpassword',
        }
        response = self.client.post(reverse('wagtailadmin_account_change_password'), post_data)

        # Check that the user was redirected to the account page
        self.assertRedirects(response, reverse('wagtailadmin_account'))

        # Check that the password was changed
        self.assertTrue(get_user_model().objects.get(username='test').check_password('newpassword'))

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
        self.assertTrue("The two password fields didn't match." in response.context['form'].errors['new_password2'])

        # Check that the password was not changed
        self.assertTrue(get_user_model().objects.get(username='test').check_password('password'))

    def test_notification_preferences_view(self):
        """
        This tests that the notification preferences view responds with the
        notification preferences page
        """
        # Get notification preferences page
        response = self.client.get(reverse('wagtailadmin_account_notification_preferences'))

        # Check that the user recieved a notification preferences page
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

        profile = UserProfile.get_for_user(get_user_model().objects.get(username='test'))

        # Check that the notification preferences are as submitted
        self.assertFalse(profile.submitted_notifications)
        self.assertFalse(profile.approved_notifications)
        self.assertTrue(profile.rejected_notifications)


class TestAccountManagementForNonModerator(TestCase, WagtailTestUtils):
    """
    Tests of reduced-functionality for editors
    """
    def setUp(self):
        # Create a non-moderator user
        self.submitter = get_user_model().objects.create_user('submitter', 'submitter@example.com', 'password')
        self.submitter.groups.add(Group.objects.get(name='Editors'))

        self.client.login(username=self.submitter.username, password='password')

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

        self.admin_only_user = get_user_model().objects.create_user(
            'admin_only_user',
            'admin_only_user@example.com',
            'password'
        )
        self.admin_only_user.groups.add(admin_only_group)

        self.client.login(username=self.admin_only_user.username, password='password')

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
        response = self.client.get(reverse('wagtailadmin_account'))
        self.assertEqual(response.context['show_notification_preferences'], False)
        self.assertNotContains(response, reverse('wagtailadmin_account_notification_preferences'))
        # safety check that checking for absence/presence of urls works
        self.assertContains(response, reverse('wagtailadmin_home'))


class TestPasswordReset(TestCase, WagtailTestUtils):
    """
    This tests that the password reset is working
    """
    def setUp(self):
        # Create a user
        get_user_model().objects.create_superuser(username='test', email='test@email.com', password='password')

    def test_password_reset_view(self):
        """
        This tests that the password reset view returns a password reset page
        """
        # Get password reset page
        response = self.client.get(reverse('wagtailadmin_password_reset'))

        # Check that the user recieved a password reset page
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

        # Check that the user wasn't redirected
        self.assertEqual(response.status_code, 200)

        # Check that a validation error was raised
        self.assertTrue('__all__' in response.context['form'].errors.keys())
        self.assertTrue("This email address is not recognised." in response.context['form'].errors['__all__'])

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
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode

        # Get user
        self.user = get_user_model().objects.get(username='test')

        # Generate a password reset token
        self.password_reset_token = PasswordResetTokenGenerator().make_token(self.user)

        # Generate a password reset uid
        self.password_reset_uid = urlsafe_base64_encode(force_bytes(self.user.pk))

        # Create url_args
        self.url_kwargs = dict(uidb64=self.password_reset_uid, token=self.password_reset_token)

    def test_password_reset_confirm_view(self):
        """
        This tests that the password reset confirm view returns a password reset confirm page
        """
        self.setup_password_reset_confirm_tests()

        # Get password reset confirm page
        response = self.client.get(reverse('wagtailadmin_password_reset_confirm', kwargs=self.url_kwargs))

        # Check that the user recieved a password confirm done page
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
        self.assertTrue(get_user_model().objects.get(username='test').check_password('newpassword'))

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
        self.assertTrue("The two password fields didn't match." in response.context['form'].errors['new_password2'])

        # Check that the password was not changed
        self.assertTrue(get_user_model().objects.get(username='test').check_password('password'))

    def test_password_reset_done_view(self):
        """
        This tests that the password reset done view returns a password reset done page
        """
        # Get password reset done page
        response = self.client.get(reverse('wagtailadmin_password_reset_done'))

        # Check that the user recieved a password reset done page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/account/password_reset/done.html')

    def test_password_reset_complete_view(self):
        """
        This tests that the password reset complete view returns a password reset complete page
        """
        # Get password reset complete page
        response = self.client.get(reverse('wagtailadmin_password_reset_complete'))

        # Check that the user recieved a password reset complete page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/account/password_reset/complete.html')
