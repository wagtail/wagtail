# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

from django.test import TestCase
from django.core import mail
from django import forms
from django import template
from django.core.urlresolvers import reverse

from wagtail.wagtailcore.models import Page
from wagtail.wagtailcore.blocks import CharBlock, ListBlock, StreamBlock, StructBlock, StructValue
from wagtail.wagtailforms.blocks import AbstractField, FormFieldBlock
from wagtail.wagtailforms.models import FormSubmission, FakeManager
from wagtail.wagtailforms.forms import FormBuilder, FormFieldFinder
from wagtail.tests.testapp.models import FormPage, FormField, StreamFormPage
from wagtail.tests.utils import WagtailTestUtils


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
        self.form_page = make_form_page()

        # Create a form builder
        self.fb = FormBuilder(self.form_page.form_fields.all())

    def test_fields(self):
        """
        This tests that all fields were added to the form with the correct types
        """
        form_class = self.fb.get_form_class()

        self.assertIn('your-email', form_class.base_fields.keys())
        self.assertIn('your-message', form_class.base_fields.keys())

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
        self.client.login(username='eventeditor', password='password')

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

    def test_list_submissions_filtering(self):
        response = self.client.get(
            reverse('wagtailforms:list_submissions', args=(self.form_page.id, )), {'date_from': '01/01/2014'}
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
            reverse('wagtailforms:list_submissions', args=(self.form_page.id, )),
            {'date_from': '01/01/2014', 'action': 'CSV'}
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        data_line = response.content.decode().split("\n")[1]
        self.assertIn('new@example.com', data_line)

    def test_list_submissions_csv_export_with_unicode(self):
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


class TestDeleteFormSubmission(TestCase):
    fixtures = ['test.json']

    def setUp(self):
        self.client.login(username='siteeditor', password='password')
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
        self.form_page = make_form_page()
        self.client.login(username="eventeditor", password="password")

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
        self.client.login(username='siteeditor', password='password')
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


class TestFakeManager(TestCase):
    def test_init_with_wrong_type(self):
        with self.assertRaises(ValueError):
            FakeManager(None)

        class TestClass(object):
            pass

        with self.assertRaises(ValueError):
            FakeManager(TestClass())

    def test_init_with_page(self):
        root_page = Page.objects.get(id=1)

        # try a page that does not have a specific class that inherits from AbstractForm
        with self.assertRaises(ValueError):
            FakeManager(root_page)

        page = StreamFormPage()
        FakeManager(page)
        # TODO: find a way to test when we have a Page object that has a Page.specific of AbstractForm

    def test_all(self):
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
        manager = FakeManager(page)
        records = manager.all()
        self.assertEqual(len(records), 1)


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


class TestStreamFieldFormFull(TestCase):

    def setUp(self):
        home_page = Page.objects.get(url_path='/home/')
        self.page = home_page.add_child(instance=StreamFormPage(body='''[
            {
                "type": "p",
                "value": "Please provide your name."
            }, {
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
        ]''', thanks='''[
            {
                "type": "p",
                "value": "Thanks for providing your name."
            }
        ]''', slug='stream-form', title='Stream Form Test'))
        super(TestStreamFieldFormFull, self).setUp()

    def tearDown(self):
        self.page.delete()
        super(TestStreamFieldFormFull, self).tearDown()

    def test_form_rendering(self):
        response = self.client.get('/stream-form/')

        self.assertContains(response, '<input')
        self.assertContains(response, 'name="name"')
        self.assertContains(response, 'Please provide your name.')
        self.assertTemplateUsed(response, 'tests/stream_form_page.html')
        self.assertTemplateNotUsed(response, 'tests/stream_form_page_landing.html')

    def test_valid_form_post(self):
        response = self.client.post('/stream-form/', {'name': 'Joe'})

        self.assertContains(response, 'Thanks for providing your name.')
        self.assertTemplateNotUsed(response, 'tests/stream_form_page.html')
        self.assertTemplateUsed(response, 'tests/stream_form_page_landing.html')

    def test_invalid_form_post(self):
        response = self.client.post('/stream-form/', {'name': ''})

        self.assertContains(response, 'This field is required.')
        self.assertTemplateUsed(response, 'tests/stream_form_page.html')
        self.assertTemplateNotUsed(response, 'tests/stream_form_page_landing.html')
