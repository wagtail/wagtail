from django.test import TestCase

from wagtail.wagtailcore.models import Page
from wagtail.wagtailforms.models import FormSubmission

class TestFormSubmission(TestCase):
    fixtures = ['test.json']

    def test_get_form(self):
        response = self.client.get('/contact-us/')
        self.assertContains(response, "Your email")
        self.assertNotContains(response, "Thank you for your feedback")

    def test_post_invalid_form(self):
        response = self.client.post('/contact-us/', {
            'your-email': 'bob', 'your-message': 'hello world'
        })
        self.assertNotContains(response, "Thank you for your feedback")
        self.assertContains(response, "Enter a valid email address.")

    def test_post_valid_form(self):
        response = self.client.post('/contact-us/', {
            'your-email': 'bob@example.com', 'your-message': 'hello world'
        })
        self.assertNotContains(response, "Your email")
        self.assertContains(response, "Thank you for your feedback")

        form_page = Page.objects.get(url_path='/home/contact-us/')

        self.assertTrue(FormSubmission.objects.filter(page=form_page, form_data__contains='hello world').exists())
