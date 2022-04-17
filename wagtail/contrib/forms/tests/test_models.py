# -*- coding: utf-8 -*-
import unittest

from django import VERSION as DJANGO_VERSION
from django.core import mail
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings

from wagtail.contrib.forms.models import FormSubmission
from wagtail.contrib.forms.tests.utils import (
    make_form_page,
    make_form_page_with_custom_submission,
    make_form_page_with_redirect,
    make_types_test_form_page,
)
from wagtail.models import Page
from wagtail.test.testapp.models import (
    CustomFormPageSubmission,
    ExtendedFormField,
    FormField,
    FormPageWithCustomFormBuilder,
    JadeFormPage,
)
from wagtail.test.utils import WagtailTestUtils


class TestFormSubmission(TestCase):
    def setUp(self):
        # Create a form page
        self.form_page = make_form_page()

    def test_get_form(self):
        response = self.client.get("/contact-us/")

        # Check response
        self.assertContains(
            response, """<label for="id_your_email">Your email</label>"""
        )
        self.assertTemplateUsed(response, "tests/form_page.html")
        self.assertTemplateNotUsed(response, "tests/form_page_landing.html")

        # HTML in help text should be escaped
        self.assertContains(response, "&lt;em&gt;please&lt;/em&gt; be polite")

        # check that variables defined in get_context are passed through to the template (#1429)
        self.assertContains(response, "<p>hello world</p>")

    @unittest.skipIf(
        (4, 0) <= DJANGO_VERSION < (4, 0, 2),
        "help_text is erroneously escaped in Django 4.0 - 4.0.1: https://code.djangoproject.com/ticket/33419",
    )
    @override_settings(WAGTAILFORMS_HELP_TEXT_ALLOW_HTML=True)
    def test_get_form_without_help_text_escaping(self):
        response = self.client.get("/contact-us/")
        # HTML in help text should not be escaped
        self.assertContains(response, "<em>please</em> be polite")

    def test_label_escaping(self):
        FormField.objects.filter(label="Your message").update(
            label="Your <em>wonderful</em> message"
        )
        response = self.client.get("/contact-us/")
        self.assertContains(
            response,
            """<label for="id_your_message">Your &lt;em&gt;wonderful&lt;/em&gt; message</label>""",
        )

    def test_post_invalid_form(self):
        response = self.client.post(
            "/contact-us/",
            {"your_email": "bob", "your_message": "hello world", "your_choices": ""},
        )

        # Check response
        self.assertContains(response, "Enter a valid email address.")
        self.assertTemplateUsed(response, "tests/form_page.html")
        self.assertTemplateNotUsed(response, "tests/form_page_landing.html")

    def test_post_valid_form(self):
        response = self.client.post(
            "/contact-us/",
            {
                "your_email": "bob@example.com",
                "your_message": "hello world",
                "your_choices": {"foo": "", "bar": "", "baz": ""},
            },
        )

        # Check response
        self.assertContains(response, "Thank you for your feedback.")
        self.assertTemplateNotUsed(response, "tests/form_page.html")
        self.assertTemplateUsed(response, "tests/form_page_landing.html")

        # check that variables defined in get_context are passed through to the template (#1429)
        self.assertContains(response, "<p>hello world</p>")

        # check the default form_submission is added to the context
        self.assertContains(response, "<li>your_email: bob@example.com</li>")

        # Check that an email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "The subject")
        self.assertIn("Your message: hello world", mail.outbox[0].body)
        self.assertEqual(mail.outbox[0].to, ["to@email.com"])
        self.assertEqual(mail.outbox[0].from_email, "from@email.com")

        # Check that form submission was saved correctly
        form_page = Page.objects.get(url_path="/home/contact-us/")
        self.assertTrue(
            FormSubmission.objects.filter(
                page=form_page, form_data__your_message="hello world"
            ).exists()
        )

    def test_post_unicode_characters(self):
        self.client.post(
            "/contact-us/",
            {
                "your_email": "bob@example.com",
                "your_message": "こんにちは、世界",
                "your_choices": {"foo": "", "bar": "", "baz": ""},
            },
        )

        # Check the email
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Your message: こんにちは、世界", mail.outbox[0].body)

        # Check the form submission
        submission = FormSubmission.objects.get()
        self.assertEqual(submission.form_data["your_message"], "こんにちは、世界")

    def test_post_multiple_values(self):
        response = self.client.post(
            "/contact-us/",
            {
                "your_email": "bob@example.com",
                "your_message": "hello world",
                "your_choices": {"foo": "on", "bar": "on", "baz": "on"},
            },
        )

        # Check response
        self.assertContains(response, "Thank you for your feedback.")
        self.assertTemplateNotUsed(response, "tests/form_page.html")
        self.assertTemplateUsed(response, "tests/form_page_landing.html")

        # Check that the three checkbox values were saved correctly
        form_page = Page.objects.get(url_path="/home/contact-us/")
        submission = FormSubmission.objects.filter(
            page=form_page, form_data__your_message="hello world"
        )
        self.assertEqual(submission[0].form_data["your_choices"], ["foo", "bar", "baz"])

        # Check that the all the multiple checkbox values are serialised in the
        # email correctly
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("bar", mail.outbox[0].body)
        self.assertIn("foo", mail.outbox[0].body)
        self.assertIn("baz", mail.outbox[0].body)

    def test_post_blank_checkbox(self):
        response = self.client.post(
            "/contact-us/",
            {
                "your_email": "bob@example.com",
                "your_message": "hello world",
                "your_choices": {},
            },
        )

        # Check response
        self.assertContains(response, "Thank you for your feedback.")
        self.assertTemplateNotUsed(response, "tests/form_page.html")
        self.assertTemplateUsed(response, "tests/form_page_landing.html")

        # Check that the checkbox was serialised in the email correctly
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Your choices: ", mail.outbox[0].body)

    def test_invalid_from_address(self):
        with self.assertRaises(ValidationError):
            make_form_page(from_address="not an email")


class TestFormWithCustomSubmission(TestCase, WagtailTestUtils):
    def setUp(self):
        # Create a form page
        self.form_page = make_form_page_with_custom_submission()

        self.user = self.login()

    def test_get_form(self):
        response = self.client.get("/contact-us/")

        # Check response
        self.assertContains(
            response, """<label for="id_your_email">Your email</label>"""
        )
        self.assertTemplateUsed(response, "tests/form_page_with_custom_submission.html")
        self.assertTemplateNotUsed(
            response, "tests/form_page_with_custom_submission_landing.html"
        )
        self.assertNotContains(response, "<div>You must log in first.</div>", html=True)
        self.assertContains(response, "<p>Boring intro text</p>", html=True)

        # check that variables defined in get_context are passed through to the template (#1429)
        self.assertContains(response, "<p>hello world</p>")

    def test_get_form_with_anonymous_user(self):
        self.client.logout()

        response = self.client.get("/contact-us/")

        # Check response
        self.assertNotContains(
            response, """<label for="id_your_email">Your email</label>"""
        )
        self.assertTemplateUsed(response, "tests/form_page_with_custom_submission.html")
        self.assertTemplateNotUsed(
            response, "tests/form_page_with_custom_submission_landing.html"
        )
        self.assertContains(response, "<div>You must log in first.</div>", html=True)
        self.assertNotContains(response, "<p>Boring intro text</p>", html=True)

        # check that variables defined in get_context are passed through to the template (#1429)
        self.assertContains(response, "<p>hello world</p>")

    def test_post_invalid_form(self):
        response = self.client.post(
            "/contact-us/",
            {"your_email": "bob", "your_message": "hello world", "your_choices": ""},
        )

        # Check response
        self.assertContains(response, "Enter a valid email address.")
        self.assertTemplateUsed(response, "tests/form_page_with_custom_submission.html")
        self.assertTemplateNotUsed(
            response, "tests/form_page_with_custom_submission_landing.html"
        )

    def test_post_valid_form(self):
        response = self.client.post(
            "/contact-us/",
            {
                "your_email": "bob@example.com",
                "your_message": "hello world",
                "your_choices": {"foo": "", "bar": "", "baz": ""},
            },
        )

        # Check response
        self.assertContains(response, "Thank you for your patience!")
        self.assertTemplateNotUsed(
            response, "tests/form_page_with_custom_submission.html"
        )
        self.assertTemplateUsed(
            response, "tests/form_page_with_custom_submission_landing.html"
        )

        # check that variables defined in get_context are passed through to the template (#1429)
        self.assertContains(response, "<p>hello world</p>")

        # check that the custom form_submission is added to the context
        self.assertContains(response, "<p>User email: test@email.com</p>")

        # Check that an email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "The subject")
        self.assertIn("Your message: hello world", mail.outbox[0].body)
        self.assertEqual(mail.outbox[0].to, ["to@email.com"])
        self.assertEqual(mail.outbox[0].from_email, "from@email.com")

        # Check that form submission was saved correctly
        form_page = Page.objects.get(url_path="/home/contact-us/")
        self.assertTrue(
            CustomFormPageSubmission.objects.filter(
                page=form_page, form_data__your_message="hello world"
            ).exists()
        )

    def test_post_form_twice(self):
        # First submission
        response = self.client.post(
            "/contact-us/",
            {
                "your_email": "bob@example.com",
                "your_message": "hello world",
                "your_choices": {"foo": "", "bar": "", "baz": ""},
            },
        )

        # Check response
        self.assertTemplateNotUsed(
            response, "tests/form_page_with_custom_submission.html"
        )
        self.assertTemplateUsed(
            response, "tests/form_page_with_custom_submission_landing.html"
        )
        self.assertContains(response, "<p>Thank you for your patience!</p>", html=True)
        self.assertNotContains(
            response, "<div>The form is already filled.</div>", html=True
        )

        # Check that first form submission was saved correctly
        submissions_qs = CustomFormPageSubmission.objects.filter(
            user=self.user, page=self.form_page
        )
        self.assertEqual(submissions_qs.count(), 1)
        self.assertTrue(
            submissions_qs.filter(form_data__your_message="hello world").exists()
        )

        # Second submission
        response = self.client.post(
            "/contact-us/",
            {
                "your_email": "bob@example.com",
                "your_message": "hello world",
                "your_choices": {"foo": "", "bar": "", "baz": ""},
            },
        )

        # Check response
        self.assertTemplateUsed(response, "tests/form_page_with_custom_submission.html")
        self.assertTemplateNotUsed(
            response, "tests/form_page_with_custom_submission_landing.html"
        )
        self.assertNotContains(
            response, "<p>Thank you for your patience!</p>", html=True
        )
        self.assertContains(
            response, "<div>The form is already filled.</div>", html=True
        )
        self.assertNotContains(response, "<div>You must log in first.</div>", html=True)
        self.assertNotContains(response, "<p>Boring intro text</p>", html=True)

        # Check that first submission exists and second submission wasn't saved
        submissions_qs = CustomFormPageSubmission.objects.filter(
            user=self.user, page=self.form_page
        )
        self.assertEqual(submissions_qs.count(), 1)
        self.assertEqual(submissions_qs.get().form_data["your_message"], "hello world")

    def test_post_unicode_characters(self):
        self.client.post(
            "/contact-us/",
            {
                "your_email": "bob@example.com",
                "your_message": "こんにちは、世界",
                "your_choices": {"foo": "", "bar": "", "baz": ""},
            },
        )

        # Check the email
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Your message: こんにちは、世界", mail.outbox[0].body)

        # Check the form submission
        submission = CustomFormPageSubmission.objects.get()
        self.assertEqual(submission.form_data["your_message"], "こんにちは、世界")

    def test_post_multiple_values(self):
        response = self.client.post(
            "/contact-us/",
            {
                "your_email": "bob@example.com",
                "your_message": "hello world",
                "your_choices": {"foo": "on", "bar": "on", "baz": "on"},
            },
        )

        # Check response
        self.assertContains(response, "Thank you for your patience!")
        self.assertTemplateNotUsed(
            response, "tests/form_page_with_custom_submission.html"
        )
        self.assertTemplateUsed(
            response, "tests/form_page_with_custom_submission_landing.html"
        )

        # Check that the three checkbox values were saved correctly
        form_page = Page.objects.get(url_path="/home/contact-us/")
        submission = CustomFormPageSubmission.objects.filter(
            page=form_page, form_data__your_message="hello world"
        )

        self.assertEqual(submission[0].form_data["your_choices"], ["foo", "bar", "baz"])

    def test_post_blank_checkbox(self):
        response = self.client.post(
            "/contact-us/",
            {
                "your_email": "bob@example.com",
                "your_message": "hello world",
                "your_choices": {},
            },
        )

        # Check response
        self.assertContains(response, "Thank you for your patience!")
        self.assertTemplateNotUsed(
            response, "tests/form_page_with_custom_submission.html"
        )
        self.assertTemplateUsed(
            response, "tests/form_page_with_custom_submission_landing.html"
        )

        # Check that the checkbox was serialised in the email correctly
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Your choices: None", mail.outbox[0].body)


class TestFormSubmissionWithMultipleRecipients(TestCase):
    def setUp(self):
        # Create a form page
        self.form_page = make_form_page(to_address="to@email.com, another@email.com")

    def test_invalid_to_address(self):
        with self.assertRaises(ValidationError):
            make_form_page(to_address="not an email")

        with self.assertRaises(ValidationError):
            make_form_page(to_address="to@email.com, not an email")

    def test_post_valid_form(self):
        response = self.client.post(
            "/contact-us/",
            {
                "your_email": "bob@example.com",
                "your_message": "hello world",
                "your_choices": {"foo": "", "bar": "", "baz": ""},
            },
        )

        # Check response
        self.assertContains(response, "Thank you for your feedback.")
        self.assertTemplateNotUsed(response, "tests/form_page.html")
        self.assertTemplateUsed(response, "tests/form_page_landing.html")

        # check that variables defined in get_context are passed through to the template (#1429)
        self.assertContains(response, "<p>hello world</p>")

        # Check that one email was sent, but to two recipients
        self.assertEqual(len(mail.outbox), 1)

        self.assertEqual(mail.outbox[0].subject, "The subject")
        self.assertIn("Your message: hello world", mail.outbox[0].body)
        self.assertEqual(mail.outbox[0].from_email, "from@email.com")
        self.assertEqual(set(mail.outbox[0].to), {"to@email.com", "another@email.com"})

        # Check that form submission was saved correctly
        form_page = Page.objects.get(url_path="/home/contact-us/")
        self.assertTrue(
            FormSubmission.objects.filter(
                page=form_page, form_data__your_message="hello world"
            ).exists()
        )


class TestFormSubmissionWithMultipleRecipientsAndWithCustomSubmission(
    TestCase, WagtailTestUtils
):
    def setUp(self):
        # Create a form page
        self.form_page = make_form_page_with_custom_submission(
            to_address="to@email.com, another@email.com"
        )

        self.user = self.login()

    def test_post_valid_form(self):
        response = self.client.post(
            "/contact-us/",
            {
                "your_email": "bob@example.com",
                "your_message": "hello world",
                "your_choices": {"foo": "", "bar": "", "baz": ""},
            },
        )

        # Check response
        self.assertContains(response, "Thank you for your patience!")
        self.assertTemplateNotUsed(
            response, "tests/form_page_with_custom_submission.html"
        )
        self.assertTemplateUsed(
            response, "tests/form_page_with_custom_submission_landing.html"
        )

        # check that variables defined in get_context are passed through to the template (#1429)
        self.assertContains(response, "<p>hello world</p>")

        # Check that one email was sent, but to two recipients
        self.assertEqual(len(mail.outbox), 1)

        self.assertEqual(mail.outbox[0].subject, "The subject")
        self.assertIn("Your message: hello world", mail.outbox[0].body)
        self.assertEqual(mail.outbox[0].from_email, "from@email.com")
        self.assertEqual(set(mail.outbox[0].to), {"to@email.com", "another@email.com"})

        # Check that form submission was saved correctly
        form_page = Page.objects.get(url_path="/home/contact-us/")
        self.assertTrue(
            CustomFormPageSubmission.objects.filter(
                page=form_page, form_data__your_message="hello world"
            ).exists()
        )


class TestFormWithRedirect(TestCase):
    def setUp(self):
        # Create a form page
        self.form_page = make_form_page_with_redirect(
            to_address="to@email.com, another@email.com"
        )

    def test_post_valid_form(self):
        response = self.client.post(
            "/contact-us/",
            {
                "your_email": "bob@example.com",
                "your_message": "hello world",
                "your_choices": {"foo": "", "bar": "", "baz": ""},
            },
        )

        # Check response
        self.assertRedirects(response, "/")

        # Check that one email was sent, but to two recipients
        self.assertEqual(len(mail.outbox), 1)

        self.assertEqual(mail.outbox[0].subject, "The subject")
        self.assertIn("Your message: hello world", mail.outbox[0].body)
        self.assertEqual(mail.outbox[0].from_email, "from@email.com")
        self.assertEqual(set(mail.outbox[0].to), {"to@email.com", "another@email.com"})

        # Check that form submission was saved correctly
        form_page = Page.objects.get(url_path="/home/contact-us/")
        self.assertTrue(
            FormSubmission.objects.filter(
                page=form_page, form_data__your_message="hello world"
            ).exists()
        )


class TestFormPageWithCustomFormBuilder(TestCase, WagtailTestUtils):
    def setUp(self):

        home_page = Page.objects.get(url_path="/home/")
        form_page = home_page.add_child(
            instance=FormPageWithCustomFormBuilder(
                title="Support Request",
                slug="support-request",
                to_address="it@jenkins.com",
                from_address="support@jenkins.com",
                subject="Support Request Submitted",
            )
        )
        ExtendedFormField.objects.create(
            page=form_page,
            sort_order=1,
            label="Name",
            field_type="singleline",  # singleline field will be max_length 120
            required=True,
        )
        ExtendedFormField.objects.create(
            page=form_page,
            sort_order=1,
            label="Device IP Address",
            field_type="ipaddress",
            required=True,
        )

    def test_get_form(self):
        response = self.client.get("/support-request/")

        # Check response
        self.assertTemplateUsed(
            response, "tests/form_page_with_custom_form_builder.html"
        )
        self.assertTemplateNotUsed(
            response, "tests/form_page_with_custom_form_builder_landing.html"
        )
        self.assertContains(response, "<title>Support Request</title>", html=True)
        # check that max_length attribute has been passed into form
        self.assertContains(
            response,
            '<input type="text" name="name" required maxlength="120" id="id_name" />',
            html=True,
        )
        # check ip address field has rendered
        self.assertContains(
            response,
            '<input type="text" name="device_ip_address" required id="id_device_ip_address" />',
            html=True,
        )

    def test_post_invalid_form(self):
        response = self.client.post(
            "/support-request/",
            {
                "name": "very long name longer than 120 characters" * 3,  # invalid
                "device_ip_address": "192.0.2.30",  # valid
            },
        )
        # Check response with invalid character count
        self.assertContains(
            response, "Ensure this value has at most 120 characters (it has 123)"
        )
        self.assertTemplateUsed(
            response, "tests/form_page_with_custom_form_builder.html"
        )
        self.assertTemplateNotUsed(
            response, "tests/form_page_with_custom_form_builder_landing.html"
        )

        response = self.client.post(
            "/support-request/",
            {
                "name": "Ron Johnson",  # valid
                "device_ip_address": "3300.192.0.2.30",  # invalid
            },
        )
        # Check response with invalid character count
        self.assertContains(response, "Enter a valid IPv4 or IPv6 address.")
        self.assertTemplateUsed(
            response, "tests/form_page_with_custom_form_builder.html"
        )
        self.assertTemplateNotUsed(
            response, "tests/form_page_with_custom_form_builder_landing.html"
        )

    def test_post_valid_form(self):
        response = self.client.post(
            "/support-request/",
            {
                "name": "Ron Johnson",
                "device_ip_address": "192.0.2.30",
            },
        )

        # Check response
        self.assertContains(response, "Thank you for submitting a Support Request.")
        self.assertContains(response, "Ron Johnson")
        self.assertContains(response, "192.0.2.30")
        self.assertTemplateNotUsed(
            response, "tests/form_page_with_custom_form_builder.html"
        )
        self.assertTemplateUsed(
            response, "tests/form_page_with_custom_form_builder_landing.html"
        )


class TestCleanedDataEmails(TestCase):
    def setUp(self):
        # Create a form page
        self.form_page = make_types_test_form_page()

    def test_empty_field_presence(self):
        self.client.post("/contact-us/", {})

        # Check the email
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Single line text: ", mail.outbox[0].body)
        self.assertIn("Multiline: ", mail.outbox[0].body)
        self.assertIn("Email: ", mail.outbox[0].body)
        self.assertIn("Number: ", mail.outbox[0].body)
        self.assertIn("URL: ", mail.outbox[0].body)
        self.assertIn("Checkbox: ", mail.outbox[0].body)
        self.assertIn("Checkboxes: ", mail.outbox[0].body)
        self.assertIn("Drop down: ", mail.outbox[0].body)
        self.assertIn("Multiple select: ", mail.outbox[0].body)
        self.assertIn("Radio buttons: ", mail.outbox[0].body)
        self.assertIn("Date: ", mail.outbox[0].body)
        self.assertIn("Datetime: ", mail.outbox[0].body)

    def test_email_field_order(self):
        self.client.post("/contact-us/", {})

        line_beginnings = [
            "Single line text: ",
            "Multiline: ",
            "Email: ",
            "Number: ",
            "URL: ",
            "Checkbox: ",
            "Checkboxes: ",
            "Drop down: ",
            "Multiple select: ",
            "Radio buttons: ",
            "Date: ",
            "Datetime: ",
        ]

        # Check the email
        self.assertEqual(len(mail.outbox), 1)
        email_lines = mail.outbox[0].body.split("\n")

        for beginning in line_beginnings:
            message_line = email_lines.pop(0)
            self.assertTrue(message_line.startswith(beginning))

    @override_settings(SHORT_DATE_FORMAT="m/d/Y")
    def test_date_normalization(self):
        self.client.post(
            "/contact-us/",
            {
                "date": "12/31/17",
            },
        )

        # Check the email
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Date: 12/31/2017", mail.outbox[0].body)

        self.client.post(
            "/contact-us/",
            {
                "date": "12/31/1917",
            },
        )

        # Check the email
        self.assertEqual(len(mail.outbox), 2)
        self.assertIn("Date: 12/31/1917", mail.outbox[1].body)

    @override_settings(SHORT_DATETIME_FORMAT="m/d/Y P")
    def test_datetime_normalization(self):
        self.client.post(
            "/contact-us/",
            {
                "datetime": "12/31/17 4:00:00",
            },
        )

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Datetime: 12/31/2017 4 a.m.", mail.outbox[0].body)

        self.client.post(
            "/contact-us/",
            {
                "datetime": "12/31/1917 21:19",
            },
        )

        self.assertEqual(len(mail.outbox), 2)
        self.assertIn("Datetime: 12/31/1917 9:19 p.m.", mail.outbox[1].body)

        self.client.post(
            "/contact-us/",
            {
                "datetime": "1910-12-21 21:19:12",
            },
        )

        self.assertEqual(len(mail.outbox), 3)
        self.assertIn("Datetime: 12/21/1910 9:19 p.m.", mail.outbox[2].body)


class TestIssue798(TestCase, WagtailTestUtils):
    fixtures = ["test.json"]

    def setUp(self):
        self.login(username="siteeditor", password="password")
        self.form_page = Page.objects.get(url_path="/home/contact-us/").specific

        # Add a number field to the page
        FormField.objects.create(
            page=self.form_page,
            label="Your favourite number",
            field_type="number",
        )

    def test_post(self):
        response = self.client.post(
            "/contact-us/",
            {
                "your_email": "bob@example.com",
                "your_message": "hello world",
                "your_choices": {"foo": "", "bar": "", "baz": ""},
                "your_favourite_number": "7.3",
            },
        )

        # Check response
        self.assertTemplateUsed(response, "tests/form_page_landing.html")

        # Check that form submission was saved correctly
        self.assertTrue(
            FormSubmission.objects.filter(
                page=self.form_page, form_data__your_message="hello world"
            ).exists()
        )
        self.assertTrue(
            FormSubmission.objects.filter(
                page=self.form_page, form_data__your_favourite_number="7.3"
            ).exists()
        )


class TestNonHtmlExtension(TestCase):
    fixtures = ["test.json"]

    def test_non_html_extension(self):
        form_page = JadeFormPage(title="test")
        self.assertEqual(
            form_page.landing_page_template, "tests/form_page_landing.jade"
        )
