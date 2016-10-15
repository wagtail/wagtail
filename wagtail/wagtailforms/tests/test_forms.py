# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django import forms
from django.test import TestCase

from wagtail.tests.testapp.models import FormField, FormPage
from wagtail.wagtailcore.models import Page
from wagtail.wagtailforms.forms import FormBuilder


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
        self.fb = FormBuilder(self.form_page.get_form_fields())

    def test_fields(self):
        """
        This tests that all fields were added to the form with the correct types
        """
        form_class = self.fb.get_form_class()

        # All fields are present in form
        field_names = form_class.base_fields.keys()
        self.assertIn('your_name', field_names)
        self.assertIn('your_message', field_names)
        self.assertIn('your_birthday', field_names)
        self.assertIn('your_birthtime', field_names)
        self.assertIn('your_email', field_names)
        self.assertIn('your_homepage', field_names)
        self.assertIn('your_favourite_number', field_names)
        self.assertIn('your_favourite_python_ides', field_names)
        self.assertIn('your_favourite_python_ide', field_names)
        self.assertIn('your_choices', field_names)
        self.assertIn('i_agree_to_the_terms_of_use', field_names)

        # All fields have proper type
        self.assertIsInstance(form_class.base_fields['your_name'], forms.CharField)
        self.assertIsInstance(form_class.base_fields['your_message'], forms.CharField)
        self.assertIsInstance(form_class.base_fields['your_birthday'], forms.DateField)
        self.assertIsInstance(form_class.base_fields['your_birthtime'], forms.DateTimeField)
        self.assertIsInstance(form_class.base_fields['your_email'], forms.EmailField)
        self.assertIsInstance(form_class.base_fields['your_homepage'], forms.URLField)
        self.assertIsInstance(form_class.base_fields['your_favourite_number'], forms.DecimalField)
        self.assertIsInstance(form_class.base_fields['your_favourite_python_ides'], forms.ChoiceField)
        self.assertIsInstance(form_class.base_fields['your_favourite_python_ide'], forms.ChoiceField)
        self.assertIsInstance(form_class.base_fields['your_choices'], forms.MultipleChoiceField)
        self.assertIsInstance(form_class.base_fields['i_agree_to_the_terms_of_use'], forms.BooleanField)

        # Some fields have non-default widgets
        self.assertIsInstance(form_class.base_fields['your_message'].widget, forms.Textarea)
        self.assertIsInstance(form_class.base_fields['your_favourite_python_ide'].widget, forms.RadioSelect)
        self.assertIsInstance(form_class.base_fields['your_choices'].widget, forms.CheckboxSelectMultiple)
