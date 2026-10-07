from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from wagtail.contrib.redirects.models import Redirect


class TestUpdateCommand(TestCase):
    fixtures = ["test.json"]

    def test_redirect_gets_converted(self):
        Redirect.objects.create(
            old_path="/old-events/", redirect_link="http://localhost/events/"
        )

        out = StringIO()
        call_command("update_redirects", stdout=out)

        redirect = Redirect.objects.first()
        self.assertIsNotNone(redirect.redirect_page)

    def test_redirect_not_converted_when_page_not_found(self):
        Redirect.objects.create(
            old_path="/old-events/", redirect_link="http://localhost/non-existing-page/"
        )

        out = StringIO()
        call_command("update_redirects", stdout=out)

        redirect = Redirect.objects.first()
        self.assertIsNone(redirect.redirect_page)
        self.assertNotEqual(redirect.redirect_link, "")

    def test_external_url_gets_skipped(self):
        Redirect.objects.create(
            old_path="/old-events/", redirect_link="https://google.com/some-page/"
        )

        out = StringIO()
        call_command("update_redirects", stdout=out)

        redirect = Redirect.objects.first()
        self.assertIsNone(redirect.redirect_page)
        self.assertNotEqual(redirect.redirect_link, "")

    def test_nothing_gets_saved_on_dry_run(self):
        Redirect.objects.create(
            old_path="/old-events/", redirect_link="http://localhost/events/"
        )

        out = StringIO()
        call_command("update_redirects", dry_run=True, stdout=out)

        redirect = Redirect.objects.first()
        self.assertIsNone(redirect.redirect_page)
        self.assertNotEqual(redirect.redirect_link, "")
        self.assertIn("Would convert redirect", out.getvalue())

    def test_redirect_converts_without_trailing_slash(self):
        Redirect.objects.create(
            old_path="/old-events/", redirect_link="http://localhost/events"
        )

        out = StringIO()
        call_command("update_redirects", stdout=out)

        redirect = Redirect.objects.first()
        self.assertIsNotNone(redirect.redirect_page)
        self.assertEqual(redirect.redirect_link, "")
