from django import forms
from django.test import TestCase

from wagtail.contrib.forms.forms import FormBuilder
from wagtail.contrib.forms.utils import get_field_clean_name
from wagtail.models import Page
from wagtail.test.testapp.models import (
    ExtendedFormField,
    FormField,
    FormPage,
    FormPageWithCustomFormBuilder,
)


class TestFormBuilder(TestCase):
    def setUp(self):
        # Create a form page
        home_page = Page.objects.get(url_path="/home/")

        self.form_page = home_page.add_child(
            instance=FormPage(
                title="Contact us",
                slug="contact-us",
                to_address="to@email.com",
                from_address="from@email.com",
                subject="The subject",
            )
        )

        FormField.objects.create(
            page=self.form_page,
            sort_order=1,
            label="Your name",
            field_type="singleline",
            required=True,
        )
        FormField.objects.create(
            page=self.form_page,
            sort_order=2,
            label="Your message",
            field_type="multiline",
            required=True,
        )
        FormField.objects.create(
            page=self.form_page,
            sort_order=2,
            label="Your birthday",
            field_type="date",
            required=True,
        )
        FormField.objects.create(
            page=self.form_page,
            sort_order=2,
            label="Your birthtime :)",
            field_type="datetime",
            required=True,
        )
        FormField.objects.create(
            page=self.form_page,
            sort_order=1,
            label="Your email",
            field_type="email",
            required=True,
        )
        FormField.objects.create(
            page=self.form_page,
            sort_order=2,
            label="Your homepage",
            field_type="url",
            required=True,
        )
        FormField.objects.create(
            page=self.form_page,
            sort_order=2,
            label="Your favourite number",
            field_type="number",
            required=True,
        )
        FormField.objects.create(
            page=self.form_page,
            sort_order=2,
            label="Your favourite text editors",
            field_type="multiselect",
            required=True,
            choices="vim,nano,emacs",
        )
        FormField.objects.create(
            page=self.form_page,
            sort_order=2,
            label="Your favourite Python IDEs",
            field_type="dropdown",
            required=True,
            choices="PyCharm,vim,nano",
        )
        FormField.objects.create(
            page=self.form_page,
            sort_order=2,
            label="Ὕour favourite Ρython ÏÐÈ",  # unicode example
            help_text="Choose one",
            field_type="radio",
            required=True,
            choices="PyCharm,vim,nano",
        )
        FormField.objects.create(
            page=self.form_page,
            sort_order=3,
            label="Your choices",
            field_type="checkboxes",
            required=False,
            choices="foo,bar,baz",
        )
        FormField.objects.create(
            page=self.form_page,
            sort_order=3,
            label="I agree to the Terms of Use",
            field_type="checkbox",
            required=True,
        )
        FormField.objects.create(
            page=self.form_page,
            sort_order=1,
            label="A Hidden Field",
            field_type="hidden",
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
        self.assertIn("your_name", field_names)
        self.assertIn("your_message", field_names)
        self.assertIn("your_birthday", field_names)
        self.assertIn("your_birthtime", field_names)
        self.assertIn("your_email", field_names)
        self.assertIn("your_homepage", field_names)
        self.assertIn("your_favourite_number", field_names)
        self.assertIn("your_favourite_text_editors", field_names)
        self.assertIn("your_favourite_python_ides", field_names)
        self.assertIn("u03a5our_favourite_u03a1ython_ixd0e", field_names)
        self.assertIn("your_choices", field_names)
        self.assertIn("i_agree_to_the_terms_of_use", field_names)
        self.assertIn("a_hidden_field", field_names)

        # All fields have proper type
        self.assertIsInstance(form_class.base_fields["your_name"], forms.CharField)
        self.assertIsInstance(form_class.base_fields["your_message"], forms.CharField)
        self.assertIsInstance(form_class.base_fields["your_birthday"], forms.DateField)
        self.assertIsInstance(
            form_class.base_fields["your_birthtime"], forms.DateTimeField
        )
        self.assertIsInstance(form_class.base_fields["your_email"], forms.EmailField)
        self.assertIsInstance(form_class.base_fields["your_homepage"], forms.URLField)
        self.assertIsInstance(
            form_class.base_fields["your_favourite_number"], forms.DecimalField
        )
        self.assertIsInstance(
            form_class.base_fields["your_favourite_text_editors"],
            forms.MultipleChoiceField,
        )
        self.assertIsInstance(
            form_class.base_fields["your_favourite_python_ides"], forms.ChoiceField
        )
        self.assertIsInstance(
            form_class.base_fields["u03a5our_favourite_u03a1ython_ixd0e"],
            forms.ChoiceField,
        )
        self.assertIsInstance(
            form_class.base_fields["your_choices"], forms.MultipleChoiceField
        )
        self.assertIsInstance(
            form_class.base_fields["i_agree_to_the_terms_of_use"], forms.BooleanField
        )
        self.assertIsInstance(form_class.base_fields["a_hidden_field"], forms.CharField)

        # Some fields have non-default widgets
        self.assertIsInstance(
            form_class.base_fields["your_message"].widget, forms.Textarea
        )
        self.assertIsInstance(
            form_class.base_fields["u03a5our_favourite_u03a1ython_ixd0e"].widget,
            forms.RadioSelect,
        )
        self.assertIsInstance(
            form_class.base_fields["your_choices"].widget, forms.CheckboxSelectMultiple
        )
        self.assertIsInstance(
            form_class.base_fields["a_hidden_field"].widget, forms.HiddenInput
        )

    def test_unsaved_fields_in_form_builder_formfields(self):
        """Ensure unsaved FormField instances are added to FormBuilder.formfields dict
        with a clean_name as the key.
        """
        unsaved_field_1 = FormField(
            page=self.form_page,
            sort_order=14,
            label="Unsaved field 1",
            field_type="singleline",
            required=True,
        )
        self.form_page.form_fields.add(unsaved_field_1)

        unsaved_field_2 = FormField(
            page=self.form_page,
            sort_order=15,
            label="Unsaved field 2",
            field_type="singleline",
            required=True,
        )
        self.form_page.form_fields.add(unsaved_field_2)

        fb = FormBuilder(self.form_page.get_form_fields())
        self.assertIn(get_field_clean_name(unsaved_field_1.label), fb.formfields)
        self.assertIn(get_field_clean_name(unsaved_field_2.label), fb.formfields)

    def test_newline_value_separation_in_choices_and_default_value_fields(self):
        """Ensure that the new line present between input choices or values gets formatted into choices or value list
        respectively as an alternative to commas.
        """
        multiselect_field = FormField.objects.create(
            page=self.form_page,
            sort_order=2,
            label="Your favorite colours",
            field_type="multiselect",
            required=True,
            choices="red\r\nblue\r\ngreen",
        )
        self.form_page.form_fields.add(multiselect_field)

        dropdown_field = FormField.objects.create(
            page=self.form_page,
            sort_order=2,
            label="Pick your next destination",
            field_type="dropdown",
            required=True,
            choices="hawaii\r\nparis\r\nabuja",
        )
        self.form_page.form_fields.add(dropdown_field)

        checkboxes_field = FormField.objects.create(
            page=self.form_page,
            sort_order=3,
            label="Do you possess these attributes",
            field_type="checkboxes",
            required=False,
            choices="good, kind and gentle.\r\nstrong, bold and brave.",
        )
        self.form_page.form_fields.add(checkboxes_field)

        radio_field = FormField.objects.create(
            page=self.form_page,
            sort_order=2,
            label="Your favorite animal",
            help_text="Choose one",
            field_type="radio",
            required=True,
            choices="cat\r\ndog\r\nbird",
        )
        self.form_page.form_fields.add(radio_field)

        checkboxes_field_with_default_value = FormField.objects.create(
            page=self.form_page,
            sort_order=3,
            label="Choose the correct answer",
            field_type="checkboxes",
            required=False,
            choices="a\r\nb\r\nc",
            default_value="a\r\nc",
        )
        self.form_page.form_fields.add(checkboxes_field_with_default_value)

        fb = FormBuilder(self.form_page.get_form_fields())
        form_class = fb.get_form_class()

        self.assertEqual(
            [("red", "red"), ("blue", "blue"), ("green", "green")],
            form_class.base_fields["your_favorite_colours"].choices,
        )
        self.assertEqual(
            [("cat", "cat"), ("dog", "dog"), ("bird", "bird")],
            form_class.base_fields["your_favorite_animal"].choices,
        )
        self.assertEqual(
            [
                ("good, kind and gentle.", "good, kind and gentle."),
                ("strong, bold and brave.", "strong, bold and brave."),
            ],
            form_class.base_fields["do_you_possess_these_attributes"].choices,
        )
        self.assertEqual(
            [("hawaii", "hawaii"), ("paris", "paris"), ("abuja", "abuja")],
            form_class.base_fields["pick_your_next_destination"].choices,
        )
        self.assertEqual(
            ["a", "c"],
            form_class.base_fields["choose_the_correct_answer"].initial,
        )


class TestCustomFormBuilder(TestCase):
    def setUp(self):
        # Create a form page
        home_page = Page.objects.get(url_path="/home/")

        self.form_page = home_page.add_child(
            instance=FormPageWithCustomFormBuilder(
                title="IT Support Request",
                slug="it-support-request",
                to_address="it@jenkins.com",
                from_address="support@jenkins.com",
                subject="Support Request Submitted",
            )
        )
        ExtendedFormField.objects.create(
            page=self.form_page,
            sort_order=1,
            label="Name",
            field_type="singleline",
            required=True,
        )

    def test_using_custom_form_builder(self):
        """Tests that charfield max_length is 120 characters."""
        form_class = self.form_page.get_form_class()
        form = form_class()
        # check name field exists
        self.assertIsInstance(form.base_fields["name"], forms.CharField)
        # check max_length is set
        self.assertEqual(form.base_fields["name"].max_length, 120)

    def test_adding_custom_field(self):
        """Tests that we can add the ipaddress field, which is an extended choice."""
        ExtendedFormField.objects.create(
            page=self.form_page,
            sort_order=1,
            label="Device IP Address",
            field_type="ipaddress",
            required=True,
        )
        form_class = self.form_page.get_form_class()
        form = form_class()
        # check ip address field used
        self.assertIsInstance(
            form.base_fields["device_ip_address"], forms.GenericIPAddressField
        )

    def test_unsaved_fields_in_form_builder_formfields_with_clean_name_override(self):
        """
        Ensure unsaved FormField instances are added to FormBuilder.formfields dict
        with a clean_name that uses the `get_field_clean_name` method that can be overridden.
        """

        unsaved_field_1 = ExtendedFormField(
            page=self.form_page,
            sort_order=14,
            label="Unsaved field 1",
            field_type="number",
            required=True,
        )
        self.form_page.form_fields.add(unsaved_field_1)

        unsaved_field_2 = ExtendedFormField(
            page=self.form_page,
            sort_order=15,
            label="duplicate (suffix removed)",
            field_type="singleline",
            required=True,
        )
        self.form_page.form_fields.add(unsaved_field_2)

        form_class = self.form_page.get_form_class()
        form = form_class()

        # See ExtendedFormField get_field_clean_name method
        self.assertIn("number_field--unsaved_field_1", form.base_fields)
        self.assertIn("test duplicate", form.base_fields)
