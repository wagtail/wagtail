from django.test import TestCase
from django.core import mail
from django import forms

from wagtail.wagtailcore.models import Page
from wagtail.wagtailforms.models import FormSubmission
from wagtail.wagtailforms.forms import FormBuilder


class TestFormSubmission(TestCase):
    fixtures = ['test.json']

    def test_get_form(self):
        response = self.client.get('/contact-us/')

        # Check response
        self.assertContains(response, """<label for="id_your-email">Your email</label>""")
        self.assertTemplateUsed(response, 'tests/form_page.html')
        self.assertTemplateNotUsed(response, 'tests/form_page_landing.html')

    def test_post_invalid_form(self):
        response = self.client.post('/contact-us/', {
            'your-email': 'bob', 'your-message': 'hello world'
        })

        # Check response
        self.assertContains(response, "Enter a valid email address.")
        self.assertTemplateUsed(response, 'tests/form_page.html')
        self.assertTemplateNotUsed(response, 'tests/form_page_landing.html')

    def test_post_valid_form(self):
        response = self.client.post('/contact-us/', {
            'your-email': 'bob@example.com', 'your-message': 'hello world'
        })

        # Check response
        self.assertEqual(response.status_code, 302)

        # Check that an email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "The subject")
        self.assertTrue("Your message: hello world" in mail.outbox[0].body)
        self.assertEqual(mail.outbox[0].to, ['to@email.com'])
        self.assertEqual(mail.outbox[0].from_email, 'from@email.com')

        # Check that form submission was saved correctly
        form_page = Page.objects.get(url_path='/home/contact-us/')
        self.assertTrue(FormSubmission.objects.filter(page=form_page, form_data__contains='hello world').exists())

    def test_get_landing_page(self):
        response = self.client.get('/contact-us/done/')

        # Check response
        self.assertContains(response, "Thank you for your feedback.")
        self.assertTemplateNotUsed(response, 'tests/form_page.html')
        self.assertTemplateUsed(response, 'tests/form_page_landing.html')


class TestFormBuilder(TestCase):
    fixtures = ['test.json']

    def setUp(self):
        self.form_page = Page.objects.get(url_path='/home/contact-us/').specific
        self.fb = FormBuilder(self.form_page.form_fields.all())

    def test_fields(self):
        """
        This tests that all fields were added to the form with the correct types
        """
        form_class = self.fb.get_form_class()
        
        self.assertTrue('your-email' in form_class.base_fields.keys())
        self.assertTrue('your-message' in form_class.base_fields.keys())

        self.assertIsInstance(form_class.base_fields['your-email'], forms.EmailField)
        self.assertIsInstance(form_class.base_fields['your-message'], forms.CharField)


class TestFormsBackend(TestCase):
    fixtures = ['test.json']

    def setUp(self):
        self.client.login(username='siteeditor', password='password')
        self.form_page = Page.objects.get(url_path='/home/contact-us/')

    def test_cannot_see_forms_without_permission(self):
        # Login with as a user without permission to see forms
        self.client.login(username='eventeditor', password='password')

        response = self.client.get('/admin/forms/')

        # Check that the user cannot see the form page
        self.assertFalse(self.form_page in response.context['form_pages'])

    def test_can_see_forms_with_permission(self):
        response = self.client.get('/admin/forms/')

        # Check that the user can see the form page
        self.assertTrue(self.form_page in response.context['form_pages'])

    def test_list_submissions(self):
        response = self.client.get('/admin/forms/submissions/%d/' % self.form_page.id)

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['data_rows']), 2)

    def test_list_submissions_filtered(self):
        response = self.client.get('/admin/forms/submissions/%d/?date_from=01%%2F01%%2F2014' % self.form_page.id)

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['data_rows']), 1)

    def test_list_submissions_csv_export(self):
        response = self.client.get('/admin/forms/submissions/%d/?date_from=01%%2F01%%2F2014&action=CSV' % self.form_page.id)

        # Check response
        self.assertEqual(response.status_code, 200)
        data_line = response.content.split("\n")[1]
        self.assertTrue('new@example.com' in data_line)
