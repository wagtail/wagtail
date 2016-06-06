# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import json

from django import forms
from django.core import mail
from django.core.urlresolvers import reverse
from django.test import TestCase

from wagtail.tests.testapp.models import FormField, FormPage
from wagtail.tests.utils import WagtailTestUtils
from wagtail.wagtailcore.models import Page
from wagtail.wagtailforms.forms import FormBuilder
from wagtail.wagtailforms.models import FormSubmission


def make_form_page(**kwargs):
    kwargs.setdefault('title', "Contact us")
    kwargs.setdefault('slug', "contact-us")
    kwargs.setdefault('to_address', "to@email.com")
    kwargs.setdefault('from_address', "from@email.com")
    kwargs.setdefault('subject', "The subject")

    home_page = Page.objects.get(url_path='/home/')
    form_page = home_page.add_child(instance=FormPage(**kwargs))

    FormField.objects.create(
        page=form_page,
        sort_order=1,
        label="Your email",
        field_type='email',
        required=True,
    )
    FormField.objects.create(
        page=form_page,
        sort_order=2,
        label="Your message",
        field_type='multiline',
        required=True,
    )
    FormField.objects.create(
        page=form_page,
        sort_order=3,
        label="Your choices",
        field_type='checkboxes',
        required=False,
        choices='foo,bar,baz',
    )

    return form_page


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
        self.assertIn("Your choices: None", mail.outbox[0].body)


class TestFormBuilder(TestCase):
    def setUp(self):
        # Create a form page
        home_page = Page.objects.get(url_path='/home/')

        self.form_page = home_page.add_child(instance=FormPage(
            title="Contact us",
            slug="contact-us",
            to_address="to@email.com",
            from_address="from@email.com",
            subject="The subject",
        ))

        FormField.objects.create(
            page=self.form_page,
            sort_order=1,
            label="Your name",
            field_type='singleline',
            required=True,
        )
        FormField.objects.create(
            page=self.form_page,
            sort_order=2,
            label="Your message",
            field_type='multiline',
            required=True,
        )
        FormField.objects.create(
            page=self.form_page,
            sort_order=2,
            label="Your birthday",
            field_type='date',
            required=True,
        )
        FormField.objects.create(
            page=self.form_page,
            sort_order=2,
            label="Your birthtime :)",
            field_type='datetime',
            required=True,
        )
        FormField.objects.create(
            page=self.form_page,
            sort_order=1,
            label="Your email",
            field_type='email',
            required=True,
        )
        FormField.objects.create(
            page=self.form_page,
            sort_order=2,
            label="Your homepage",
            field_type='url',
            required=True,
        )
        FormField.objects.create(
            page=self.form_page,
            sort_order=2,
            label="Your favourite number",
            field_type='number',
            required=True,
        )
        FormField.objects.create(
            page=self.form_page,
            sort_order=2,
            label="Your favourite Python IDEs",
            field_type='dropdown',
            required=True,
            choices='PyCharm,vim,nano',
        )
        FormField.objects.create(
            page=self.form_page,
            sort_order=2,
            label="Your favourite Python IDE",
            help_text="Choose one",
            field_type='radio',
            required=True,
            choices='PyCharm,vim,nano',
        )
        FormField.objects.create(
            page=self.form_page,
            sort_order=3,
            label="Your choices",
            field_type='checkboxes',
            required=False,
            choices='foo,bar,baz',
        )
        FormField.objects.create(
            page=self.form_page,
            sort_order=3,
            label="I agree to the Terms of Use",
            field_type='checkbox',
            required=True,
        )

        # Create a form builder
        self.fb = FormBuilder(self.form_page.form_fields.all())

    def test_fields(self):
        """
        This tests that all fields were added to the form with the correct types
        """
        form_class = self.fb.get_form_class()

        # All fields are present in form
        field_names = form_class.base_fields.keys()
        self.assertIn('your-name', field_names)
        self.assertIn('your-message', field_names)
        self.assertIn('your-birthday', field_names)
        self.assertIn('your-birthtime', field_names)
        self.assertIn('your-email', field_names)
        self.assertIn('your-homepage', field_names)
        self.assertIn('your-favourite-number', field_names)
        self.assertIn('your-favourite-python-ides', field_names)
        self.assertIn('your-favourite-python-ide', field_names)
        self.assertIn('your-choices', field_names)
        self.assertIn('i-agree-to-the-terms-of-use', field_names)

        # All fields have proper type
        self.assertIsInstance(form_class.base_fields['your-name'], forms.CharField)
        self.assertIsInstance(form_class.base_fields['your-message'], forms.CharField)
        self.assertIsInstance(form_class.base_fields['your-birthday'], forms.DateField)
        self.assertIsInstance(form_class.base_fields['your-birthtime'], forms.DateTimeField)
        self.assertIsInstance(form_class.base_fields['your-email'], forms.EmailField)
        self.assertIsInstance(form_class.base_fields['your-homepage'], forms.URLField)
        self.assertIsInstance(form_class.base_fields['your-favourite-number'], forms.DecimalField)
        self.assertIsInstance(form_class.base_fields['your-favourite-python-ides'], forms.ChoiceField)
        self.assertIsInstance(form_class.base_fields['your-favourite-python-ide'], forms.ChoiceField)
        self.assertIsInstance(form_class.base_fields['your-choices'], forms.MultipleChoiceField)
        self.assertIsInstance(form_class.base_fields['i-agree-to-the-terms-of-use'], forms.BooleanField)

        # Some fields have non-default widgets
        self.assertIsInstance(form_class.base_fields['your-message'].widget, forms.Textarea)
        self.assertIsInstance(form_class.base_fields['your-favourite-python-ide'].widget, forms.RadioSelect)
        self.assertIsInstance(form_class.base_fields['your-choices'].widget, forms.CheckboxSelectMultiple)


class TestFormsIndex(TestCase):
    fixtures = ['test.json']

    def setUp(self):
        self.assertTrue(self.client.login(username='siteeditor', password='password'))
        self.form_page = Page.objects.get(url_path='/home/contact-us/')

    def make_form_pages(self):
        """
        This makes 100 form pages and adds them as children to 'contact-us'
        This is used to test pagination on the forms index
        """
        for i in range(100):
            self.form_page.add_child(instance=FormPage(
                title="Form " + str(i),
                slug='form-' + str(i),
                live=True
            ))

    def test_forms_index(self):
        response = self.client.get(reverse('wagtailforms:index'))

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailforms/index.html')

    def test_forms_index_pagination(self):
        # Create some more form pages to make pagination kick in
        self.make_form_pages()

        # Get page two
        response = self.client.get(reverse('wagtailforms:index'), {'p': 2})

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailforms/index.html')

        # Check that we got the correct page
        self.assertEqual(response.context['form_pages'].number, 2)

    def test_forms_index_pagination_invalid(self):
        # Create some more form pages to make pagination kick in
        self.make_form_pages()

        # Get page two
        response = self.client.get(reverse('wagtailforms:index'), {'p': 'Hello world!'})

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailforms/index.html')

        # Check that it got page one
        self.assertEqual(response.context['form_pages'].number, 1)

    def test_forms_index_pagination_out_of_range(self):
        # Create some more form pages to make pagination kick in
        self.make_form_pages()

        # Get page two
        response = self.client.get(reverse('wagtailforms:index'), {'p': 99999})

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailforms/index.html')

        # Check that it got the last page
        self.assertEqual(response.context['form_pages'].number, response.context['form_pages'].paginator.num_pages)

    def test_cannot_see_forms_without_permission(self):
        # Login with as a user without permission to see forms
        self.assertTrue(self.client.login(username='eventeditor', password='password'))

        response = self.client.get(reverse('wagtailforms:index'))

        # Check that the user cannot see the form page
        self.assertFalse(self.form_page in response.context['form_pages'])

    def test_can_see_forms_with_permission(self):
        response = self.client.get(reverse('wagtailforms:index'))

        # Check that the user can see the form page
        self.assertIn(self.form_page, response.context['form_pages'])


class TestFormsSubmissions(TestCase, WagtailTestUtils):
    def setUp(self):
        # Create a form page
        self.form_page = make_form_page()

        # Add a couple of form submissions
        old_form_submission = FormSubmission.objects.create(
            page=self.form_page,
            form_data=json.dumps({
                'your-email': "old@example.com",
                'your-message': "this is a really old message",
            }),
        )
        old_form_submission.submit_time = '2013-01-01T12:00:00.000Z'
        old_form_submission.save()

        new_form_submission = FormSubmission.objects.create(
            page=self.form_page,
            form_data=json.dumps({
                'your-email': "new@example.com",
                'your-message': "this is a fairly new message",
            }),
        )
        new_form_submission.submit_time = '2014-01-01T12:00:00.000Z'
        new_form_submission.save()

        # Login
        self.login()

    def make_list_submissions(self):
        """
        This makes 100 submissions to test pagination on the forms submissions page
        """
        for i in range(100):
            submission = FormSubmission(
                page=self.form_page,
                form_data=json.dumps({
                    'hello': 'world'
                })
            )
            submission.save()

    def test_list_submissions(self):
        response = self.client.get(reverse('wagtailforms:list_submissions', args=(self.form_page.id, )))

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailforms/index_submissions.html')
        self.assertEqual(len(response.context['data_rows']), 2)

    def test_list_submissions_filtering_date_from(self):
        response = self.client.get(
            reverse('wagtailforms:list_submissions', args=(self.form_page.id, )), {'date_from': '01/01/2014'}
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailforms/index_submissions.html')
        self.assertEqual(len(response.context['data_rows']), 1)

    def test_list_submissions_filtering_date_to(self):
        response = self.client.get(
            reverse('wagtailforms:list_submissions', args=(self.form_page.id, )), {'date_to': '12/31/2013'}
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailforms/index_submissions.html')
        self.assertEqual(len(response.context['data_rows']), 1)

    def test_list_submissions_filtering_range(self):
        response = self.client.get(
            reverse('wagtailforms:list_submissions', args=(self.form_page.id, )),
            {'date_from': '12/31/2013', 'date_to': '01/02/2014'}
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailforms/index_submissions.html')
        self.assertEqual(len(response.context['data_rows']), 1)

    def test_list_submissions_pagination(self):
        self.make_list_submissions()

        response = self.client.get(reverse('wagtailforms:list_submissions', args=(self.form_page.id, )), {'p': 2})

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailforms/index_submissions.html')

        # Check that we got the correct page
        self.assertEqual(response.context['submissions'].number, 2)

    def test_list_submissions_pagination_invalid(self):
        self.make_list_submissions()

        response = self.client.get(
            reverse('wagtailforms:list_submissions', args=(self.form_page.id, )), {'p': 'Hello World!'}
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailforms/index_submissions.html')

        # Check that we got page one
        self.assertEqual(response.context['submissions'].number, 1)

    def test_list_submissions_pagination_out_of_range(self):
        self.make_list_submissions()

        response = self.client.get(reverse('wagtailforms:list_submissions', args=(self.form_page.id, )), {'p': 99999})

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailforms/index_submissions.html')

        # Check that we got the last page
        self.assertEqual(response.context['submissions'].number, response.context['submissions'].paginator.num_pages)

    def test_list_submissions_csv_export(self):
        response = self.client.get(
            reverse('wagtailforms:list_submissions', args=(self.form_page.id,)),
            {'action': 'CSV'}
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        data_lines = response.content.decode().split("\n")

        self.assertEqual(data_lines[0], 'Submission date,Your email,Your message,Your choices\r')
        self.assertEqual(data_lines[1], '2013-01-01 12:00:00+00:00,old@example.com,this is a really old message,None\r')
        self.assertEqual(data_lines[2], '2014-01-01 12:00:00+00:00,new@example.com,this is a fairly new message,None\r')

    def test_list_submissions_csv_export_with_date_from_filtering(self):
        response = self.client.get(
            reverse('wagtailforms:list_submissions', args=(self.form_page.id,)),
            {'action': 'CSV', 'date_from': '01/01/2014'}
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        data_lines = response.content.decode().split("\n")

        self.assertEqual(data_lines[0], 'Submission date,Your email,Your message,Your choices\r')
        self.assertEqual(data_lines[1], '2014-01-01 12:00:00+00:00,new@example.com,this is a fairly new message,None\r')

    def test_list_submissions_csv_export_with_date_to_filtering(self):
        response = self.client.get(
            reverse('wagtailforms:list_submissions', args=(self.form_page.id,)),
            {'action': 'CSV', 'date_to': '12/31/2013'}
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        data_lines = response.content.decode().split("\n")

        self.assertEqual(data_lines[0], 'Submission date,Your email,Your message,Your choices\r')
        self.assertEqual(data_lines[1], '2013-01-01 12:00:00+00:00,old@example.com,this is a really old message,None\r')

    def test_list_submissions_csv_export_with_range_filtering(self):
        response = self.client.get(
            reverse('wagtailforms:list_submissions', args=(self.form_page.id,)),
            {'action': 'CSV', 'date_from': '12/31/2013', 'date_to': '01/02/2014'}
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        data_lines = response.content.decode().split("\n")

        self.assertEqual(data_lines[0], 'Submission date,Your email,Your message,Your choices\r')
        self.assertEqual(data_lines[1], '2014-01-01 12:00:00+00:00,new@example.com,this is a fairly new message,None\r')

    def test_list_submissions_csv_export_with_unicode_in_submission(self):
        unicode_form_submission = FormSubmission.objects.create(
            page=self.form_page,
            form_data=json.dumps({
                'your-email': "unicode@example.com",
                'your-message': 'こんにちは、世界',
            }),
        )
        unicode_form_submission.submit_time = '2014-01-02T12:00:00.000Z'
        unicode_form_submission.save()

        response = self.client.get(
            reverse('wagtailforms:list_submissions', args=(self.form_page.id, )),
            {'date_from': '01/02/2014', 'action': 'CSV'}
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        data_line = response.content.decode('utf-8').split("\n")[1]
        self.assertIn('こんにちは、世界', data_line)

    def test_list_submissions_csv_export_with_unicode_in_field(self):
        FormField.objects.create(
            page=self.form_page,
            sort_order=2,
            label="Выберите самую любимую IDE для разработке на Python",
            help_text="Вы можете выбрать только один вариант",
            field_type='radio',
            required=True,
            choices='PyCharm,vim,nano',
        )
        unicode_form_submission = FormSubmission.objects.create(
            page=self.form_page,
            form_data=json.dumps({
                'your-email': "unicode@example.com",
                'your-message': "We don\'t need unicode here",
                'vyberite-samuiu-liubimuiu-ide-dlia-razrabotke-na-python': "vim",
            }),
        )
        unicode_form_submission.submit_time = '2014-01-02T12:00:00.000Z'
        unicode_form_submission.save()

        response = self.client.get(
            reverse('wagtailforms:list_submissions', args=(self.form_page.id, )),
            {'date_from': '01/02/2014', 'action': 'CSV'}
        )

        # Check response
        self.assertEqual(response.status_code, 200)

        data_lines = response.content.decode('utf-8').split("\n")
        self.assertIn('Выберите самую любимую IDE для разработке на Python', data_lines[0])
        self.assertIn('vim', data_lines[1])


class TestDeleteFormSubmission(TestCase):
    fixtures = ['test.json']

    def setUp(self):
        self.assertTrue(self.client.login(username='siteeditor', password='password'))
        self.form_page = Page.objects.get(url_path='/home/contact-us/')

    def test_delete_submission_show_cofirmation(self):
        response = self.client.get(reverse(
            'wagtailforms:delete_submission',
            args=(self.form_page.id, FormSubmission.objects.first().id)
        ))
        # Check show confirm page when HTTP method is GET
        self.assertTemplateUsed(response, 'wagtailforms/confirm_delete.html')

        # Check that the deletion has not happened with GET request
        self.assertEqual(FormSubmission.objects.count(), 2)

    def test_delete_submission_with_permissions(self):
        response = self.client.post(reverse(
            'wagtailforms:delete_submission',
            args=(self.form_page.id, FormSubmission.objects.first().id)
        ))

        # Check that the submission is gone
        self.assertEqual(FormSubmission.objects.count(), 1)
        # Should be redirected to list of submissions
        self.assertRedirects(response, reverse("wagtailforms:list_submissions", args=(self.form_page.id, )))

    def test_delete_submission_bad_permissions(self):
        self.assertTrue(self.client.login(username="eventeditor", password="password"))

        response = self.client.post(reverse(
            'wagtailforms:delete_submission',
            args=(self.form_page.id, FormSubmission.objects.first().id)
        ))

        # Check that the user recieved a 403 response
        self.assertEqual(response.status_code, 403)

        # Check that the deletion has not happened
        self.assertEqual(FormSubmission.objects.count(), 2)


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
