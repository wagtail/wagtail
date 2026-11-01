from unittest import mock, skipUnless

from django import VERSION as DJANGO_VERSION
from django.core.mail import get_connection
from django.test import SimpleTestCase, override_settings

from wagtail.admin.mail import send_mail

MAILER_OPTIONS = {
    "host": "smtp.example.com",
    "username": "mailer-user",
    "password": "mailer-password",
    "use_tls": True,
}

MAILERS = {
    "default": {
        "BACKEND": "django.core.mail.backends.smtp.EmailBackend",
        "OPTIONS": MAILER_OPTIONS,
    }
}


class SendMailConnectionTests(SimpleTestCase):
    def test_connection_is_created_without_arguments_when_none_are_given(self):
        with mock.patch("wagtail.admin.mail.get_connection") as get_connection_mock:
            send_mail(
                "Subject",
                "Message",
                ["recipient@example.com"],
                from_email="sender@example.com",
            )

        get_connection_mock.assert_called_once_with()

    def test_provided_auth_arguments_are_passed_on(self):
        with mock.patch("wagtail.admin.mail.get_connection") as get_connection_mock:
            send_mail(
                "Subject",
                "Message",
                ["recipient@example.com"],
                from_email="sender@example.com",
                auth_user="user",
                auth_password="password",
                fail_silently=True,
            )

        get_connection_mock.assert_called_once_with(
            username="user", password="password", fail_silently=True
        )


@skipUnless(
    DJANGO_VERSION >= (6, 1),
    "The MAILERS setting requires Django 6.1 or above",
)
class MailerCredentialsTests(SimpleTestCase):
    def build_connection_recorder(self):
        connections = []

        def build_connection(**kwargs):
            connections.append(get_connection(**kwargs))
            return mock.MagicMock()

        return connections, build_connection

    def test_configured_credentials_are_used_when_no_auth_arguments_are_given(self):
        connections, build_connection = self.build_connection_recorder()
        patcher = mock.patch(
            "wagtail.admin.mail.get_connection",
            side_effect=build_connection,
        )
        with override_settings(MAILERS=MAILERS), patcher:
            send_mail(
                "Subject",
                "Message",
                ["recipient@example.com"],
                from_email="sender@example.com",
            )

        self.assertEqual(connections[0].username, "mailer-user")
        self.assertEqual(connections[0].password, "mailer-password")

    def test_configured_credentials_are_overridden_by_the_auth_arguments(self):
        connections, build_connection = self.build_connection_recorder()
        patcher = mock.patch(
            "wagtail.admin.mail.get_connection",
            side_effect=build_connection,
        )
        with override_settings(MAILERS=MAILERS), patcher:
            send_mail(
                "Subject",
                "Message",
                ["recipient@example.com"],
                from_email="sender@example.com",
                auth_user="other-user",
                auth_password="other-password",
            )

        self.assertEqual(connections[0].username, "other-user")
        self.assertEqual(connections[0].password, "other-password")
