# -*- coding: utf-8 -*-
from django import forms
from django.test import TestCase

from wagtail.contrib.forms.forms import FormBuilder
from wagtail.core.models import Page
from wagtail.tests.testapp.models import (
    ExtendedFormField, FormField, FormPage, FormPageWithCustomFormBuilder)


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
            label="Your favourite text editors",
            field_type='multiselect',
            required=True,
            choices='vim,nano,emacs',
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
        FormField.objects.create(
            page=self.form_page,
            sort_order=1,
            label="A Hidden Field",
            field_type='hidden',
            required=False,
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
        self.assertIn('your-name', field_names)
        self.assertIn('your-message', field_names)
        self.assertIn('your-birthday', field_names)
        self.assertIn('your-birthtime', field_names)
        self.assertIn('your-email', field_names)
        self.assertIn('your-homepage', field_names)
        self.assertIn('your-favourite-number', field_names)
        self.assertIn('your-favourite-text-editors', field_names)
        self.assertIn('your-favourite-python-ides', field_names)
        self.assertIn('your-favourite-python-ide', field_names)
        self.assertIn('your-choices', field_names)
        self.assertIn('i-agree-to-the-terms-of-use', field_names)
        self.assertIn('a-hidden-field', field_names)

        # All fields have proper type
        self.assertIsInstance(form_class.base_fields['your-name'], forms.CharField)
        self.assertIsInstance(form_class.base_fields['your-message'], forms.CharField)
        self.assertIsInstance(form_class.base_fields['your-birthday'], forms.DateField)
        self.assertIsInstance(form_class.base_fields['your-birthtime'], forms.DateTimeField)
        self.assertIsInstance(form_class.base_fields['your-email'], forms.EmailField)
        self.assertIsInstance(form_class.base_fields['your-homepage'], forms.URLField)
        self.assertIsInstance(form_class.base_fields['your-favourite-number'], forms.DecimalField)
        self.assertIsInstance(form_class.base_fields['your-favourite-text-editors'], forms.MultipleChoiceField)
        self.assertIsInstance(form_class.base_fields['your-favourite-python-ides'], forms.ChoiceField)
        self.assertIsInstance(form_class.base_fields['your-favourite-python-ide'], forms.ChoiceField)
        self.assertIsInstance(form_class.base_fields['your-choices'], forms.MultipleChoiceField)
        self.assertIsInstance(form_class.base_fields['i-agree-to-the-terms-of-use'], forms.BooleanField)
        self.assertIsInstance(form_class.base_fields['a-hidden-field'], forms.CharField)

        # Some fields have non-default widgets
        self.assertIsInstance(form_class.base_fields['your-message'].widget, forms.Textarea)
        self.assertIsInstance(form_class.base_fields['your-favourite-python-ide'].widget, forms.RadioSelect)
        self.assertIsInstance(form_class.base_fields['your-choices'].widget, forms.CheckboxSelectMultiple)
        self.assertIsInstance(form_class.base_fields['a-hidden-field'].widget, forms.HiddenInput)


class TestCustomFormBuilder(TestCase):
    def setUp(self):
        # Create a form page
        home_page = Page.objects.get(url_path='/home/')

        self.form_page = home_page.add_child(
            instance=FormPageWithCustomFormBuilder(
                title='IT Support Request',
                slug='it-support-request',
                to_address='it@jenkins.com',
                from_address='support@jenkins.com',
                subject='Support Request Submitted',
            )
        )
        ExtendedFormField.objects.create(
            page=self.form_page,
            sort_order=1,
            label='Name',
            field_type='singleline',
            required=True,
        )

    def test_using_custom_form_builder(self):
        """Tests that charfield max_length is 120 characters."""
        form_class = self.form_page.get_form_class()
        form = form_class()
        # check name field exists
        self.assertIsInstance(form.base_fields['name'], forms.CharField)
        # check max_length is set
        self.assertEqual(form.base_fields['name'].max_length, 120)

    def test_adding_custom_field(self):
        """Tests that we can add the ipaddress field, which is an extended choice."""
        ExtendedFormField.objects.create(
            page=self.form_page,
            sort_order=1,
            label='Device IP Address',
            field_type='ipaddress',
            required=True,
        )
        form_class = self.form_page.get_form_class()
        form = form_class()
        # check ip address field used
        self.assertIsInstance(
            form.base_fields['device-ip-address'], forms.GenericIPAddressField)
