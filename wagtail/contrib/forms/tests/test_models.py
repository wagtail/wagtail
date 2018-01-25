# -*- coding: utf-8 -*-
import json

from django.core import mail
from django.test import TestCase

from wagtail.contrib.forms.models import FormSubmission
from wagtail.contrib.forms.tests.utils import (
    make_form_page, make_form_page_with_custom_submission, make_form_page_with_redirect)
from wagtail.core.models import Page
from wagtail.tests.testapp.models import (
    CustomFormPageSubmission, ExtendedFormField, FormField, FormPageWithCustomFormBuilder,
    JadeFormPage)
from wagtail.tests.utils import WagtailTestUtils


class TestFormSubmission(TestCase):
    def setUp(self):
        # Create a form page
        self.form_page = make_form_page()

    def test_get_form(self):
        response = self.client.get('/contact-us/')

        # Check response
        self.assertContains(response, """<label for="id_your-email">Your email</label>""")
        self.assertTemplateUsed(response, 'tests/form_page.html')
        self.assertTemplateNotUsed(response, 'tests/form_page_landing.html')

        # check that variables defined in get_context are passed through to the template (#1429)
        self.assertContains(response, "<p>hello world</p>")

    def test_post_invalid_form(self):
        response = self.client.post('/contact-us/', {
            'your-email': 'bob',
            'your-message': 'hello world',
            'your-choices': ''
        })

        # Check response
        self.assertContains(response, "Enter a valid email address.")
        self.assertTemplateUsed(response, 'tests/form_page.html')
        self.assertTemplateNotUsed(response, 'tests/form_page_landing.html')

    def test_post_valid_form(self):
        response = self.client.post('/contact-us/', {
            'your-email': 'bob@example.com',
            'your-message': 'hello world',
            'your-choices': {'foo': '', 'bar': '', 'baz': ''}
        })

        # Check response
        self.assertContains(response, "Thank you for your feedback.")
        self.assertTemplateNotUsed(response, 'tests/form_page.html')
        self.assertTemplateUsed(response, 'tests/form_page_landing.html')

        # check that variables defined in get_context are passed through to the template (#1429)
        self.assertContains(response, "<p>hello world</p>")

        # check the default form_submission is added to the context
        self.assertContains(response, "<li>your-email: bob@example.com</li>")

        # Check that an email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "The subject")
        self.assertIn("Your message: hello world", mail.outbox[0].body)
        self.assertEqual(mail.outbox[0].to, ['to@email.com'])
        self.assertEqual(mail.outbox[0].from_email, 'from@email.com')

        # Check that form submission was saved correctly
        form_page = Page.objects.get(url_path='/home/contact-us/')
        self.assertTrue(FormSubmission.objects.filter(page=form_page, form_data__contains='hello world').exists())

    def test_post_unicode_characters(self):
        self.client.post('/contact-us/', {
            'your-email': 'bob@example.com',
            'your-message': 'こんにちは、世界',
            'your-choices': {'foo': '', 'bar': '', 'baz': ''}
        })

        # Check the email
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Your message: こんにちは、世界", mail.outbox[0].body)

        # Check the form submission
        submission = FormSubmission.objects.get()
        submission_data = json.loads(submission.form_data)
        self.assertEqual(submission_data['your-message'], 'こんにちは、世界')

    def test_post_multiple_values(self):
        response = self.client.post('/contact-us/', {
            'your-email': 'bob@example.com',
            'your-message': 'hello world',
            'your-choices': {'foo': 'on', 'bar': 'on', 'baz': 'on'}
        })

        # Check response
        self.assertContains(response, "Thank you for your feedback.")
        self.assertTemplateNotUsed(response, 'tests/form_page.html')
        self.assertTemplateUsed(response, 'tests/form_page_landing.html')

        # Check that the three checkbox values were saved correctly
        form_page = Page.objects.get(url_path='/home/contact-us/')
        submission = FormSubmission.objects.filter(
            page=form_page, form_data__contains='hello world'
        )
        self.assertIn("foo", submission[0].form_data)
        self.assertIn("bar", submission[0].form_data)
        self.assertIn("baz", submission[0].form_data)

        # Check that the all the multiple checkbox values are serialised in the
        # email correctly
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("bar", mail.outbox[0].body)
        self.assertIn("foo", mail.outbox[0].body)
        self.assertIn("baz", mail.outbox[0].body)

    def test_post_blank_checkbox(self):
        response = self.client.post('/contact-us/', {
            'your-email': 'bob@example.com',
            'your-message': 'hello world',
            'your-choices': {},
        })

        # Check response
        self.assertContains(response, "Thank you for your feedback.")
        self.assertTemplateNotUsed(response, 'tests/form_page.html')
        self.assertTemplateUsed(response, 'tests/form_page_landing.html')

        # Check that the checkbox was serialised in the email correctly
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Your choices: ", mail.outbox[0].body)


class TestFormWithCustomSubmission(TestCase, WagtailTestUtils):
    def setUp(self):
        # Create a form page
        self.form_page = make_form_page_with_custom_submission()

        self.user = self.login()

    def test_get_form(self):
        response = self.client.get('/contact-us/')

        # Check response
        self.assertContains(response, """<label for="id_your-email">Your email</label>""")
        self.assertTemplateUsed(response, 'tests/form_page_with_custom_submission.html')
        self.assertTemplateNotUsed(response, 'tests/form_page_with_custom_submission_landing.html')
        self.assertNotContains(response, '<div>You must log in first.</div>', html=True)
        self.assertContains(response, '<p>Boring intro text</p>', html=True)

        # check that variables defined in get_context are passed through to the template (#1429)
        self.assertContains(response, "<p>hello world</p>")

    def test_get_form_with_anonymous_user(self):
        self.client.logout()

        response = self.client.get('/contact-us/')

        # Check response
        self.assertNotContains(response, """<label for="id_your-email">Your email</label>""")
        self.assertTemplateUsed(response, 'tests/form_page_with_custom_submission.html')
        self.assertTemplateNotUsed(response, 'tests/form_page_with_custom_submission_landing.html')
        self.assertContains(response, '<div>You must log in first.</div>', html=True)
        self.assertNotContains(response, '<p>Boring intro text</p>', html=True)

        # check that variables defined in get_context are passed through to the template (#1429)
        self.assertContains(response, "<p>hello world</p>")

    def test_post_invalid_form(self):
        response = self.client.post('/contact-us/', {
            'your-email': 'bob',
            'your-message': 'hello world',
            'your-choices': ''
        })

        # Check response
        self.assertContains(response, "Enter a valid email address.")
        self.assertTemplateUsed(response, 'tests/form_page_with_custom_submission.html')
        self.assertTemplateNotUsed(response, 'tests/form_page_with_custom_submission_landing.html')

    def test_post_valid_form(self):
        response = self.client.post('/contact-us/', {
            'your-email': 'bob@example.com',
            'your-message': 'hello world',
            'your-choices': {'foo': '', 'bar': '', 'baz': ''}
        })

        # Check response
        self.assertContains(response, "Thank you for your patience!")
        self.assertTemplateNotUsed(response, 'tests/form_page_with_custom_submission.html')
        self.assertTemplateUsed(response, 'tests/form_page_with_custom_submission_landing.html')

        # check that variables defined in get_context are passed through to the template (#1429)
        self.assertContains(response, "<p>hello world</p>")

        # check that the custom form_submission is added to the context
        self.assertContains(response, "<p>Username: test@email.com</p>")

        # Check that an email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "The subject")
        self.assertIn("Your message: hello world", mail.outbox[0].body)
        self.assertEqual(mail.outbox[0].to, ['to@email.com'])
        self.assertEqual(mail.outbox[0].from_email, 'from@email.com')

        # Check that form submission was saved correctly
        form_page = Page.objects.get(url_path='/home/contact-us/')
        self.assertTrue(CustomFormPageSubmission.objects.filter(page=form_page, form_data__contains='hello world').exists())

    def test_post_form_twice(self):
        # First submission
        response = self.client.post('/contact-us/', {
            'your-email': 'bob@example.com',
            'your-message': 'hello world',
            'your-choices': {'foo': '', 'bar': '', 'baz': ''}
        })

        # Check response
        self.assertTemplateNotUsed(response, 'tests/form_page_with_custom_submission.html')
        self.assertTemplateUsed(response, 'tests/form_page_with_custom_submission_landing.html')
        self.assertContains(response, '<p>Thank you for your patience!</p>', html=True)
        self.assertNotContains(response, '<div>The form is already filled.</div>', html=True)

        # Check that first form submission was saved correctly
        submissions_qs = CustomFormPageSubmission.objects.filter(user=self.user, page=self.form_page)
        self.assertEqual(submissions_qs.count(), 1)
        self.assertTrue(submissions_qs.filter(form_data__contains='hello world').exists())

        # Second submission
        response = self.client.post('/contact-us/', {
            'your-email': 'bob@example.com',
            'your-message': 'hello world',
            'your-choices': {'foo': '', 'bar': '', 'baz': ''}
        })

        # Check response
        self.assertTemplateUsed(response, 'tests/form_page_with_custom_submission.html')
        self.assertTemplateNotUsed(response, 'tests/form_page_with_custom_submission_landing.html')
        self.assertNotContains(response, '<p>Thank you for your patience!</p>', html=True)
        self.assertContains(response, '<div>The form is already filled.</div>', html=True)
        self.assertNotContains(response, '<div>You must log in first.</div>', html=True)
        self.assertNotContains(response, '<p>Boring intro text</p>', html=True)

        # Check that first submission exists and second submission wasn't saved
        submissions_qs = CustomFormPageSubmission.objects.filter(user=self.user, page=self.form_page)
        self.assertEqual(submissions_qs.count(), 1)
        self.assertTrue(submissions_qs.filter(form_data__contains='hello world').exists())
        self.assertFalse(submissions_qs.filter(form_data__contains='hello cruel world').exists())

    def test_post_unicode_characters(self):
        self.client.post('/contact-us/', {
            'your-email': 'bob@example.com',
            'your-message': 'こんにちは、世界',
            'your-choices': {'foo': '', 'bar': '', 'baz': ''}
        })

        # Check the email
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Your message: こんにちは、世界", mail.outbox[0].body)

        # Check the form submission
        submission = CustomFormPageSubmission.objects.get()
        submission_data = json.loads(submission.form_data)
        self.assertEqual(submission_data['your-message'], 'こんにちは、世界')

    def test_post_multiple_values(self):
        response = self.client.post('/contact-us/', {
            'your-email': 'bob@example.com',
            'your-message': 'hello world',
            'your-choices': {'foo': 'on', 'bar': 'on', 'baz': 'on'}
        })

        # Check response
        self.assertContains(response, "Thank you for your patience!")
        self.assertTemplateNotUsed(response, 'tests/form_page_with_custom_submission.html')
        self.assertTemplateUsed(response, 'tests/form_page_with_custom_submission_landing.html')

        # Check that the three checkbox values were saved correctly
        form_page = Page.objects.get(url_path='/home/contact-us/')
        submission = CustomFormPageSubmission.objects.filter(
            page=form_page, form_data__contains='hello world'
        )
        self.assertIn("foo", submission[0].form_data)
        self.assertIn("bar", submission[0].form_data)
        self.assertIn("baz", submission[0].form_data)

    def test_post_blank_checkbox(self):
        response = self.client.post('/contact-us/', {
            'your-email': 'bob@example.com',
            'your-message': 'hello world',
            'your-choices': {},
        })

        # Check response
        self.assertContains(response, "Thank you for your patience!")
        self.assertTemplateNotUsed(response, 'tests/form_page_with_custom_submission.html')
        self.assertTemplateUsed(response, 'tests/form_page_with_custom_submission_landing.html')

        # Check that the checkbox was serialised in the email correctly
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Your choices: None", mail.outbox[0].body)


class TestFormSubmissionWithMultipleRecipients(TestCase):
    def setUp(self):
        # Create a form page
        self.form_page = make_form_page(to_address='to@email.com, another@email.com')

    def test_post_valid_form(self):
        response = self.client.post('/contact-us/', {
            'your-email': 'bob@example.com',
            'your-message': 'hello world',
            'your-choices': {'foo': '', 'bar': '', 'baz': ''}
        })

        # Check response
        self.assertContains(response, "Thank you for your feedback.")
        self.assertTemplateNotUsed(response, 'tests/form_page.html')
        self.assertTemplateUsed(response, 'tests/form_page_landing.html')

        # check that variables defined in get_context are passed through to the template (#1429)
        self.assertContains(response, "<p>hello world</p>")

        # Check that one email was sent, but to two recipients
        self.assertEqual(len(mail.outbox), 1)

        self.assertEqual(mail.outbox[0].subject, "The subject")
        self.assertIn("Your message: hello world", mail.outbox[0].body)
        self.assertEqual(mail.outbox[0].from_email, 'from@email.com')
        self.assertEqual(set(mail.outbox[0].to), {'to@email.com', 'another@email.com'})

        # Check that form submission was saved correctly
        form_page = Page.objects.get(url_path='/home/contact-us/')
        self.assertTrue(FormSubmission.objects.filter(page=form_page, form_data__contains='hello world').exists())


class TestFormSubmissionWithMultipleRecipientsAndWithCustomSubmission(TestCase, WagtailTestUtils):
    def setUp(self):
        # Create a form page
        self.form_page = make_form_page_with_custom_submission(
            to_address='to@email.com, another@email.com'
        )

        self.user = self.login()

    def test_post_valid_form(self):
        response = self.client.post('/contact-us/', {
            'your-email': 'bob@example.com',
            'your-message': 'hello world',
            'your-choices': {'foo': '', 'bar': '', 'baz': ''}
        })

        # Check response
        self.assertContains(response, "Thank you for your patience!")
        self.assertTemplateNotUsed(response, 'tests/form_page_with_custom_submission.html')
        self.assertTemplateUsed(response, 'tests/form_page_with_custom_submission_landing.html')

        # check that variables defined in get_context are passed through to the template (#1429)
        self.assertContains(response, "<p>hello world</p>")

        # Check that one email was sent, but to two recipients
        self.assertEqual(len(mail.outbox), 1)

        self.assertEqual(mail.outbox[0].subject, "The subject")
        self.assertIn("Your message: hello world", mail.outbox[0].body)
        self.assertEqual(mail.outbox[0].from_email, 'from@email.com')
        self.assertEqual(set(mail.outbox[0].to), {'to@email.com', 'another@email.com'})

        # Check that form submission was saved correctly
        form_page = Page.objects.get(url_path='/home/contact-us/')
        self.assertTrue(
            CustomFormPageSubmission.objects.filter(page=form_page, form_data__contains='hello world').exists()
        )


class TestFormWithRedirect(TestCase):
    def setUp(self):
        # Create a form page
        self.form_page = make_form_page_with_redirect(to_address='to@email.com, another@email.com')

    def test_post_valid_form(self):
        response = self.client.post('/contact-us/', {
            'your-email': 'bob@example.com',
            'your-message': 'hello world',
            'your-choices': {'foo': '', 'bar': '', 'baz': ''}
        })

        # Check response
        self.assertRedirects(response, '/')

        # Check that one email was sent, but to two recipients
        self.assertEqual(len(mail.outbox), 1)

        self.assertEqual(mail.outbox[0].subject, "The subject")
        self.assertIn("Your message: hello world", mail.outbox[0].body)
        self.assertEqual(mail.outbox[0].from_email, 'from@email.com')
        self.assertEqual(set(mail.outbox[0].to), {'to@email.com', 'another@email.com'})

        # Check that form submission was saved correctly
        form_page = Page.objects.get(url_path='/home/contact-us/')
        self.assertTrue(FormSubmission.objects.filter(page=form_page, form_data__contains='hello world').exists())


class TestFormPageWithCustomFormBuilder(TestCase, WagtailTestUtils):

    def setUp(self):

        home_page = Page.objects.get(url_path='/home/')
        form_page = home_page.add_child(
            instance=FormPageWithCustomFormBuilder(
                title='Support Request',
                slug='support-request',
                to_address='it@jenkins.com',
                from_address='support@jenkins.com',
                subject='Support Request Submitted',
            )
        )
        ExtendedFormField.objects.create(
            page=form_page,
            sort_order=1,
            label='Name',
            field_type='singleline',  # singleline field will be max_length 120
            required=True,
        )
        ExtendedFormField.objects.create(
            page=form_page,
            sort_order=1,
            label='Device IP Address',
            field_type='ipaddress',
            required=True,
        )

    def test_get_form(self):
        response = self.client.get('/support-request/')

        # Check response
        self.assertTemplateUsed(response, 'tests/form_page_with_custom_form_builder.html')
        self.assertTemplateNotUsed(response, 'tests/form_page_with_custom_form_builder_landing.html')
        self.assertContains(response, '<title>Support Request</title>', html=True)
        # check that max_length attribute has been passed into form
        self.assertContains(response, '<input type="text" name="name" required maxlength="120" id="id_name" />', html=True)
        # check ip address field has rendered
        self.assertContains(response, '<input type="text" name="device-ip-address" required id="id_device-ip-address" />', html=True)

    def test_post_invalid_form(self):
        response = self.client.post('/support-request/', {
            'name': 'very long name longer than 120 characters' * 3,  # invalid
            'device-ip-address': '192.0.2.30',  # valid
        })
        # Check response with invalid character count
        self.assertContains(response, 'Ensure this value has at most 120 characters (it has 123)')
        self.assertTemplateUsed(response, 'tests/form_page_with_custom_form_builder.html')
        self.assertTemplateNotUsed(response, 'tests/form_page_with_custom_form_builder_landing.html')

        response = self.client.post('/support-request/', {
            'name': 'Ron Johnson',  # valid
            'device-ip-address': '3300.192.0.2.30',  # invalid
        })
        # Check response with invalid character count
        self.assertContains(response, 'Enter a valid IPv4 or IPv6 address.')
        self.assertTemplateUsed(response, 'tests/form_page_with_custom_form_builder.html')
        self.assertTemplateNotUsed(response, 'tests/form_page_with_custom_form_builder_landing.html')

    def test_post_valid_form(self):
        response = self.client.post('/support-request/', {
            'name': 'Ron Johnson',
            'device-ip-address': '192.0.2.30',
        })

        # Check response
        self.assertContains(response, 'Thank you for submitting a Support Request.')
        self.assertContains(response, 'Ron Johnson')
        self.assertContains(response, '192.0.2.30')
        self.assertTemplateNotUsed(response, 'tests/form_page_with_custom_form_builder.html')
        self.assertTemplateUsed(response, 'tests/form_page_with_custom_form_builder_landing.html')


class TestIssue798(TestCase):
    fixtures = ['test.json']

    def setUp(self):
        self.assertTrue(self.client.login(username='siteeditor', password='password'))
        self.form_page = Page.objects.get(url_path='/home/contact-us/').specific

        # Add a number field to the page
        FormField.objects.create(
            page=self.form_page,
            label="Your favourite number",
            field_type='number',
        )

    def test_post(self):
        response = self.client.post('/contact-us/', {
            'your-email': 'bob@example.com',
            'your-message': 'hello world',
            'your-choices': {'foo': '', 'bar': '', 'baz': ''},
            'your-favourite-number': '7.3',
        })

        # Check response
        self.assertTemplateUsed(response, 'tests/form_page_landing.html')

        # Check that form submission was saved correctly
        self.assertTrue(FormSubmission.objects.filter(page=self.form_page, form_data__contains='7.3').exists())


class TestNonHtmlExtension(TestCase):
    fixtures = ['test.json']

    def test_non_html_extension(self):
        form_page = JadeFormPage(title="test")
        self.assertEqual(form_page.landing_page_template, "tests/form_page_landing.jade")
