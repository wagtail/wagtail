from wagtail.tests.utils import unittest, WagtailTestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core import mail


class TestAuthentication(WagtailTestCase):
    """
    This tests that users can login and logout of the admin interface
    """
    def setUp(self):
        self.login()

    def test_login_view(self):
        """
        This tests that the login view responds with a login page
        """
        # Logout so we can test the login view
        self.client.logout()

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
        # Logout so we can test the login view
        self.client.logout()

        # Post credentials to the login page
        post_data = {
            'username': 'test',
            'password': 'password',
        }
        response = self.client.post(reverse('wagtailadmin_login'), post_data)

        # Check that the user was redirected to the dashboard
        self.assertEqual(response.status_code, 302)
        self.assertURLEqual(response.url, reverse('wagtailadmin_home'))

        # Check that the user was logged in
        self.assertTrue('_auth_user_id' in self.client.session)
        self.assertEqual(self.client.session['_auth_user_id'], User.objects.get(username='test').id)

    @unittest.expectedFailure # See: https://github.com/torchbox/wagtail/issues/25
    def test_already_logged_in_redirect(self):
        """
        This tests that a user who is already logged in is automatically
        redirected to the admin dashboard if they try to access the login
        page
        """
        # Get login page
        response = self.client.get(reverse('wagtailadmin_login'))

        # Check that the user was redirected to the dashboard
        self.assertEqual(response.status_code, 302)
        self.assertURLEqual(response.url, reverse('wagtailadmin_home'))

    def test_logout(self):
        """
        This tests that the user can logout
        """
        # Get logout page page
        response = self.client.get(reverse('wagtailadmin_logout'))

        # Check that the user was redirected to the login page
        self.assertEqual(response.status_code, 302)
        self.assertURLEqual(response.url, reverse('wagtailadmin_login'))

        # Check that the user was logged out
        self.assertFalse('_auth_user_id' in self.client.session)


class TestAccountSection(WagtailTestCase):
    """
    This tests that the accounts section is working
    """
    def setUp(self):
        self.login()

    def test_account_view(self):
        """
        This tests that the login view responds with a login page
        """
        # Get account page
        response = self.client.get(reverse('wagtailadmin_account'))

        # Check that the user recieved an account page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/account/account.html')

    def test_change_password_view(self):
        """
        This tests that the change password view responds with a change password page
        """
        # Get change password page
        response = self.client.get(reverse('wagtailadmin_account_change_password'))

        # Check that the user recieved a change password page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/account/change_password.html')

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
        self.assertEqual(response.status_code, 302)
        self.assertURLEqual(response.url, reverse('wagtailadmin_account'))

        # Check that the password was changed
        self.assertTrue(User.objects.get(username='test').check_password('newpassword'))

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
        self.assertTrue(User.objects.get(username='test').check_password('password'))


class TestPasswordReset(WagtailTestCase):
    """
    This tests that the password reset is working
    """
    def setUp(self):
        # Create a user
        User.objects.create_superuser(username='test', email='test@email.com', password='password')

    def test_password_reset_view(self):
        """
        This tests that the password reset view returns a password reset page
        """
        # Get password reset page
        response = self.client.get(reverse('password_reset'))

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
        response = self.client.post(reverse('password_reset'), post_data)

        # Check that the user was redirected to the done page
        self.assertEqual(response.status_code, 302)
        self.assertURLEqual(response.url, reverse('password_reset_done'))

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
        response = self.client.post(reverse('password_reset'), post_data)

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
        response = self.client.post(reverse('password_reset'), post_data)

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
        self.user = User.objects.get(username='test')

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
        response = self.client.get(reverse('password_reset_confirm', kwargs=self.url_kwargs))

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
        response = self.client.post(reverse('password_reset_confirm', kwargs=self.url_kwargs), post_data)

        # Check that the user was redirected to the complete page
        self.assertEqual(response.status_code, 302)
        self.assertURLEqual(response.url, reverse('password_reset_complete'))

        # Check that the password was changed
        self.assertTrue(User.objects.get(username='test').check_password('newpassword'))

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
        response = self.client.post(reverse('password_reset_confirm', kwargs=self.url_kwargs), post_data)

        # Check that the user wasn't redirected
        self.assertEqual(response.status_code, 200)

        # Check that a validation error was raised
        self.assertTrue('new_password2' in response.context['form'].errors.keys())
        self.assertTrue("The two password fields didn't match." in response.context['form'].errors['new_password2'])

        # Check that the password was not changed
        self.assertTrue(User.objects.get(username='test').check_password('password'))

    def test_password_reset_done_view(self):
        """
        This tests that the password reset done view returns a password reset done page
        """
        # Get password reset done page
        response = self.client.get(reverse('password_reset_done'))

        # Check that the user recieved a password reset done page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/account/password_reset/done.html')

    def test_password_reset_complete_view(self):
        """
        This tests that the password reset complete view returns a password reset complete page
        """
        # Get password reset complete page
        response = self.client.get(reverse('password_reset_complete'))

        # Check that the user recieved a password reset complete page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/account/password_reset/complete.html')
