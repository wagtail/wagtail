import json

from django.test import TestCase
from django.core import mail
from django import forms
from django.core.urlresolvers import reverse

from wagtail.wagtailcore.models import Page
from wagtail.wagtailforms.models import FormSubmission
from wagtail.wagtailforms.forms import FormBuilder
from wagtail.tests.models import FormPage


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
        self.assertContains(response, "Thank you for your feedback.")
        self.assertTemplateNotUsed(response, 'tests/form_page.html')
        self.assertTemplateUsed(response, 'tests/form_page_landing.html')

        # Check that an email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "The subject")
        self.assertTrue("Your message: hello world" in mail.outbox[0].body)
        self.assertEqual(mail.outbox[0].to, ['to@email.com'])
        self.assertEqual(mail.outbox[0].from_email, 'from@email.com')

        # Check that form submission was saved correctly
        form_page = Page.objects.get(url_path='/home/contact-us/')
        self.assertTrue(FormSubmission.objects.filter(page=form_page, form_data__contains='hello world').exists())


class TestPageModes(TestCase):
    fixtures = ['test.json']

    def setUp(self):
        self.form_page = Page.objects.get(url_path='/home/contact-us/').specific

    def test_form(self):
        response = self.form_page.serve_preview(self.form_page.dummy_request(), 'form')

        # Check response
        self.assertContains(response, """<label for="id_your-email">Your email</label>""")
        self.assertTemplateUsed(response, 'tests/form_page.html')
        self.assertTemplateNotUsed(response, 'tests/form_page_landing.html')

    def test_landing(self):
        response = self.form_page.serve_preview(self.form_page.dummy_request(), 'landing')

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


class TestFormsIndex(TestCase):
    fixtures = ['test.json']

    def setUp(self):
        self.client.login(username='siteeditor', password='password')
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
        response = self.client.get(reverse('wagtailforms_index'))

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailforms/index.html')

    def test_forms_index_pagination(self):
        # Create some more form pages to make pagination kick in
        self.make_form_pages()

        # Get page two
        response = self.client.get(reverse('wagtailforms_index'), {'p': 2})

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailforms/index.html')

        # Check that we got the correct page
        self.assertEqual(response.context['form_pages'].number, 2)

    def test_forms_index_pagination_invalid(self):
        # Create some more form pages to make pagination kick in
        self.make_form_pages()

        # Get page two
        response = self.client.get(reverse('wagtailforms_index'), {'p': 'Hello world!'})

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailforms/index.html')

        # Check that it got page one
        self.assertEqual(response.context['form_pages'].number, 1)

    def test_forms_index_pagination_out_of_range(self):
        # Create some more form pages to make pagination kick in
        self.make_form_pages()

        # Get page two
        response = self.client.get(reverse('wagtailforms_index'), {'p': 99999})

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailforms/index.html')

        # Check that it got the last page
        self.assertEqual(response.context['form_pages'].number, response.context['form_pages'].paginator.num_pages)

    def test_cannot_see_forms_without_permission(self):
        # Login with as a user without permission to see forms
        self.client.login(username='eventeditor', password='password')

        response = self.client.get(reverse('wagtailforms_index'))

        # Check that the user cannot see the form page
        self.assertFalse(self.form_page in response.context['form_pages'])

    def test_can_see_forms_with_permission(self):
        response = self.client.get(reverse('wagtailforms_index'))

        # Check that the user can see the form page
        self.assertTrue(self.form_page in response.context['form_pages'])


class TestFormsSubmissions(TestCase):
    fixtures = ['test.json']

    def setUp(self):
        self.client.login(username='siteeditor', password='password')
        self.form_page = Page.objects.get(url_path='/home/contact-us/')

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
        response = self.client.get(reverse('wagtailforms_list_submissions', args=(self.form_page.id, )))

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailforms/index_submissions.html')
        self.assertEqual(len(response.context['data_rows']), 2)

    def test_list_submissions_filtering(self):
        response = self.client.get(reverse('wagtailforms_list_submissions', args=(self.form_page.id, )), {'date_from': '01/01/2014'})

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailforms/index_submissions.html')
        self.assertEqual(len(response.context['data_rows']), 1)

    def test_list_submissions_pagination(self):
        self.make_list_submissions()

        response = self.client.get(reverse('wagtailforms_list_submissions', args=(self.form_page.id, )), {'p': 2})

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailforms/index_submissions.html')

        # Check that we got the correct page
        self.assertEqual(response.context['submissions'].number, 2)

    def test_list_submissions_pagination_invalid(self):
        self.make_list_submissions()

        response = self.client.get(reverse('wagtailforms_list_submissions', args=(self.form_page.id, )), {'p': 'Hello World!'})

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailforms/index_submissions.html')

        # Check that we got page one
        self.assertEqual(response.context['submissions'].number, 1)

    def test_list_submissions_pagination_out_of_range(self):
        self.make_list_submissions()

        response = self.client.get(reverse('wagtailforms_list_submissions', args=(self.form_page.id, )), {'p': 99999})

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailforms/index_submissions.html')

        # Check that we got the last page
        self.assertEqual(response.context['submissions'].number, response.context['submissions'].paginator.num_pages)

    def test_list_submissions_csv_export(self):
        response = self.client.get(reverse('wagtailforms_list_submissions', args=(self.form_page.id, )), {'date_from': '01/01/2014', 'action': 'CSV'})

        # Check response
        self.assertEqual(response.status_code, 200)
        data_line = response.content.decode().split("\n")[1]
        self.assertTrue('new@example.com' in data_line)
