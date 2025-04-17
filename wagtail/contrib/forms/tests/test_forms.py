import itertools

from django import forms
from django.test import TestCase

from wagtail.contrib.forms.forms import FormBuilder
from wagtail.contrib.forms.utils import get_field_clean_name
from wagtail.models import Page
from wagtail.test.testapp.models import (
    ExtendedFormField,
    FormBuilderWithCustomWidget,
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

    def test_newline_value_separation_in_choices(self):
        """
        Ensure that choices can be separated either by newlines or by commas.
        """
        field_types = ["multiselect", "dropdown", "checkboxes", "radio"]
        testdata = [
            ("red\ngreen\nblue", ["red", "green", "blue"]),
            ("red\rgreen\rblue", ["red", "green", "blue"]),
            ("red\r\ngreen\r\nblue", ["red", "green", "blue"]),
            ("red\r\ngreen\nblue", ["red", "green", "blue"]),
            ("red\ngreen\nblue\n", ["red", "green", "blue"]),
            ("\nred\ngreen\nblue", ["red", "green", "blue"]),
            ("red,\ngreen \n blue", ["red", "green", "blue"]),
            ("red  ,\ngreen \n blue", ["red", "green", "blue"]),
            ("  red  \ngreen\nblue", ["red", "green", "blue"]),
            ("red\n,green\nblue", ["red", ",green", "blue"]),
            ("red\ngreen, blue\nyellow", ["red", "green, blue", "yellow"]),
        ]
        for field_type, (choices, expected) in itertools.product(field_types, testdata):
            field = FormField(field_type=field_type, choices=choices, label="test")
            builder = FormBuilder([field])
            form_field = builder.formfields["test"]
            with self.subTest(field_type=field_type, choices=choices):
                self.assertEqual(
                    [choice for choice, _ in form_field.choices],
                    expected,
                )

    def test_newline_value_separation_in_default_value(self):
        """
        Ensure that default values can be separated by newlines.
        """
        for choices, default_value, expected in [
            ("a\nb\nc", "a", ["a"]),
            ("a\nb\nc", "a\nc", ["a", "c"]),
            ("a\rb\rc", "a\rc", ["a", "c"]),
            ("a\r\nb\r\nc", "a\r\nc", ["a", "c"]),
            ("a\nb\nc", "a\r\nc", ["a", "c"]),
            ("a\nb\rc", "a\r\nc", ["a", "c"]),
            ("a\nb\nc", "a\nd", ["a", "d"]),
        ]:
            field = FormField(
                label="test",
                field_type="checkboxes",
                choices=choices,
                default_value=default_value,
            )
            builder = FormBuilder([field])
            form_field = builder.formfields["test"]
            with self.subTest(choices=choices, default_value=default_value):
                self.assertEqual(form_field.initial, expected)

    def test_custom_widget(self):
        """
        All builtin field types should be able to receive a custom widget
        """
        self.form_page.form_builder = FormBuilderWithCustomWidget
        form = self.form_page.get_form(auto_id=None)
        for fieldname, expected_render in [
            (
                "your_name",
                '<input type="text" name="your_name" maxlength="255" class="custom">',
            ),
            ("your_message", '<input type="text" name="your_message" class="custom">'),
            (
                "your_birthday",
                '<input type="text" name="your_birthday" class="custom">',
            ),
            (
                "your_birthtime",
                '<input type="text" name="your_birthtime" class="custom">',
            ),
            (
                "your_email",
                '<input type="text" name="your_email" maxlength="320" class="custom">',
            ),
            (
                "your_homepage",
                '<input type="text" name="your_homepage" class="custom">',
            ),
            (
                "your_favourite_number",
                '<input type="text" name="your_favourite_number" class="custom">',
            ),
            (
                "your_favourite_text_editors",
                '<input type="text" name="your_favourite_text_editors" class="custom">',
            ),
            (
                "your_favourite_python_ides",
                '<input type="text" name="your_favourite_python_ides" class="custom">',
            ),
            (
                "u03a5our_favourite_u03a1ython_ixd0e",
                '<input type="text" name="u03a5our_favourite_u03a1ython_ixd0e" class="custom">',
            ),
            (
                "your_choices",
                '<input type="text" name="your_choices" value="[\'\']" class="custom">',
            ),
            (
                "i_agree_to_the_terms_of_use",
                '<input type="text" name="i_agree_to_the_terms_of_use" class="custom">',
            ),
            (
                "a_hidden_field",
                '<input type="text" name="a_hidden_field" class="custom">',
            ),
        ]:
            with self.subTest(field=fieldname):
                form.fields[fieldname].required = False  # makes testing easier
                self.assertHTMLEqual(form[fieldname].as_widget(), expected_render)


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
