import warnings
from unittest import mock, skipIf, skipUnless

from django import VERSION as DJANGO_VERSION
from django.core.mail import get_connection
from django.core.mail.backends.smtp import EmailBackend as SMTPEmailBackend
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
    },
    "other": {
        "BACKEND": "django.core.mail.backends.smtp.EmailBackend",
        "OPTIONS": {**MAILER_OPTIONS, "username": "other-mailer-user"},
    },
}


class SendMailConnectionTests(SimpleTestCase):
    @skipIf(DJANGO_VERSION >= (6, 1), "Django 6.1 and above use the default mailer")
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

    def send_mail_without_deprecation_warnings(self, **kwargs):
        from django.utils.deprecation import RemovedInDjango2028Warning

        with (
            override_settings(MAILERS=MAILERS),
            mock.patch.object(
                SMTPEmailBackend, "send_messages", autospec=True
            ) as send_messages_mock,
            warnings.catch_warnings(),
        ):
            warnings.simplefilter("error", RemovedInDjango2028Warning)
            send_mail(
                "Subject",
                "Message",
                ["recipient@example.com"],
                from_email="sender@example.com",
                **kwargs,
            )

        return send_messages_mock.call_args.args[0]

    def test_configured_credentials_are_used_when_no_auth_arguments_are_given(self):
        connection = self.send_mail_without_deprecation_warnings()

        self.assertEqual(connection.username, "mailer-user")
        self.assertEqual(connection.password, "mailer-password")

    def test_using_selects_the_mailer(self):
        connection = self.send_mail_without_deprecation_warnings(using="other")
        self.assertEqual(connection.username, "other-mailer-user")

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
