# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django import forms
from django import template
from django.test import TestCase

from wagtail.tests.testapp.models import FormField, FormPage, StreamFormPage
from wagtail.wagtailcore.blocks import CharBlock, ListBlock, StreamBlock, StructBlock, StructValue
from wagtail.wagtailcore.models import Page
from wagtail.wagtailforms.blocks import AbstractField, FormFieldBlock
from wagtail.wagtailforms.forms import FormBuilder, FormFieldFinder
from wagtail.wagtailforms.models import FakeManager


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


class TestAbstractField(TestCase):

    def test_init(self):
        # create without parameters
        AbstractField()

        # create with parameters
        b = AbstractField(
            label='My Field',
            field_type='singlelinetext',
            required=True,
            choices='one,two,three',
            default_value='singlelinetext',
            help_text='This is a helpful tip.')

        self.assertEqual(b.label, 'My Field')
        self.assertEqual(b.field_type, 'singlelinetext')
        self.assertEqual(b.required, True)
        self.assertEqual(b.choices, 'one,two,three')
        self.assertEqual(b.default_value, 'singlelinetext')
        self.assertEqual(b.help_text, 'This is a helpful tip.')

        # create with unexpected parameter
        b = AbstractField(
            label='My Field',
            field_type='singlelinetext',
            required=True,
            choices='one,two,three',
            default_value='singlelinetext',
            help_text='This is a helpful tip.',
            unexpected='Not added to the object.')

        self.assertFalse(hasattr(b, 'unexpected'))

    def test_clean_name(self):
        field = AbstractField(label='Your Email:')
        self.assertEqual(field.clean_name, 'your-email')


class TestFormFieldBlock(TestCase):
    def test_init(self):
        block = FormFieldBlock()
        self.assertEqual(list(block.child_blocks.keys()), ['label', 'field_type', 'required', 'choices', 'default_value', 'help_text'])

    def test_render(self):
        block = FormFieldBlock()
        html = block.render(block.to_python({'label': 'My Field', 'field_type': 'singleline', 'required': True, 'choices': '', 'default_value': '', 'help_text': 'A tip.'}))

        self.assertIn('<dt>label</dt>', html)
        self.assertIn('<dt>field_type</dt>', html)
        self.assertIn('<dt>required</dt>', html)
        self.assertIn('<dt>choices</dt>', html)
        self.assertIn('<dt>default_value</dt>', html)
        self.assertIn('<dt>help_text</dt>', html)
        self.assertIn('<dd>My Field</dd>', html)
        self.assertIn('<dd>singleline</dd>', html)
        self.assertIn('<dd>A tip.</dd>', html)

    def test_clean_name(self):
        block = FormFieldBlock()
        value = StructValue(block)
        value.update({'label': 'My Field', 'field_type': 'singleline', 'required': True, 'choices': '', 'default_value': '', 'help_text': 'A tip.'})
        name = block.clean_name(value)
        self.assertEqual(name, 'my-field')


class TestFormFieldFinder(TestCase):
    def test_simple_case(self):
        # create a StreamBlock and pass a value in to to_python
        class TestBlock(StreamBlock):
            field = FormFieldBlock(icon='placeholder')
            p = CharBlock()

        value = TestBlock().to_python([{
            'type': 'field',
            'value': {
                "required": True,
                "default_value": "",
                "field_type": "singleline",
                "label": "Name",
                "choices": "",
                "help_text": ""
            }
        }, {
            'type': 'p',
            'value': 'A test',
        }, {
            'type': 'field',
            'value': {
                "required": False,
                "default_value": "",
                "field_type": "multiline",
                "label": "Description",
                "choices": "",
                "help_text": ""
            }
        }])

        finder = FormFieldFinder()

        fields = finder.find_form_fields(TestBlock(), value)

        self.assertEqual(len(fields), 2)
        self.assertEqual(fields[0].label, 'Name')
        self.assertEqual(fields[1].label, 'Description')

    def test_nested_form_fields(self):
        class TestStructBlock(StructBlock):
            title = CharBlock()
            description = CharBlock()
            field = FormFieldBlock()


        class TestBlock(StreamBlock):
            field = FormFieldBlock(icon='placeholder')
            p = CharBlock()
            special = TestStructBlock()
            list = ListBlock(FormFieldBlock(label='Field'))
            stream = StreamBlock([('field', FormFieldBlock()), ('p', CharBlock())])

        value = TestBlock().to_python([{
            'type': 'field',
            'value': {
                "required": True,
                "default_value": "",
                "field_type": "singleline",
                "label": "Name",
                "choices": "",
                "help_text": ""
            }
        }, {
            'type': 'p',
            'value': 'A test',
        }, {
            'type': 'field',
            'value': {
                "required": False,
                "default_value": "",
                "field_type": "multiline",
                "label": "Description",
                "choices": "",
                "help_text": ""
            }
        }, {
            'type': 'special',
            'value': {
                'title': 'A Test Special',
                'description': 'A longer description of the test special.',
                'field': {
                    "required": True,
                    "default_value": "",
                    "field_type": "singleline",
                    "label": "Book Name",
                    "choices": "",
                    "help_text": ""
                }
            }
        }, {
            'type': 'list',
            'value': [
                {
                    "required": True,
                    "default_value": "",
                    "field_type": "singleline",
                    "label": "Field Four",
                    "choices": "",
                    "help_text": ""
                }, {
                    "required": True,
                    "default_value": "",
                    "field_type": "singleline",
                    "label": "Field Five",
                    "choices": "",
                    "help_text": ""
                }
            ]
        }, {
            'type': 'stream',
            'value': [
                {
                    'type': 'p',
                    'value': 'A test paragraph'
                },
                {
                    'type': 'field',
                    'value': {
                        "required": True,
                        "default_value": "",
                        "field_type": "singleline",
                        "label": "Field Six",
                        "choices": "",
                        "help_text": ""
                    }
                }
            ]
        }])

        finder = FormFieldFinder()

        fields = finder.find_form_fields(TestBlock(), value)

        self.assertEqual(len(fields), 6)
        self.assertEqual(fields[0].label, 'Name')
        self.assertEqual(fields[1].label, 'Description')
        self.assertEqual(fields[2].label, 'Book Name')
        self.assertEqual(fields[3].label, 'Field Four')
        self.assertEqual(fields[4].label, 'Field Five')
        self.assertEqual(fields[5].label, 'Field Six')


class TestStreamFieldAbstractFormMixin(TestCase):

    def test_get_form_field_finder(self):
        page = StreamFormPage()
        self.assertIsInstance(page.get_form_field_finder(), page.form_field_finder)

    def test_find_streamfield_form_fields(self):
        page = StreamFormPage(body='''[
            {
                "type": "field",
                "value": {
                    "required": true,
                    "default_value": "",
                    "field_type": "singleline",
                    "label": "Name",
                    "choices": "",
                    "help_text": ""
                }
            }
        ]''')
        fields = page.find_streamfield_form_fields()
        self.assertEqual(len(fields), 1)

    def test_form_fields(self):
        page = StreamFormPage()
        self.assertIsInstance(page.form_fields, FakeManager)


class TestGetFormFieldTemplateTag(TestCase):
    def test_simple(self):
        class TestForm(forms.Form):
            name = forms.CharField(max_length=100)

        class Field(object):
            def __init__(self, block, value):
                self.block = block
                self.value = value

        tmpl_str = '''{% load wagtailforms_tags %} {% get_form_field field form as form_field %}{{ form_field }}'''
        tmpl = template.Template(tmpl_str)
        html = tmpl.render(template.Context({'form': TestForm(), 'field': Field(value={'label': 'Name'}, block=FormFieldBlock())}))

        self.assertIn('name="name"', html)
        self.assertIn('<input', html)
        self.assertIn('type="text"', html)
