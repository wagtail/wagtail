from django.test import TestCase

from wagtail.tests.modeladmintest.models import Contributor, Person, Visitor
from wagtail.tests.utils import WagtailTestUtils


class TestExtractPanelDefinitionsFromModelAdmin(TestCase, WagtailTestUtils):
    """tests that edit_handler and panels can be defined on modeladmin"""

    def setUp(self):
        self.login()

    def test_model_edit_handler(self):
        # tests that edit_handler defintion from model is used to create
        # a model instance if edit_handler is set on the model
        response = self.client.post('/admin/modeladmintest/person/create/', {
            'first_name': "John",
            'last_name': "Doe",
            'address': "123 Main St Anytown",
            'phone_number': "+123456789"
        })
        # Should redirect back to index
        self.assertRedirects(response, '/admin/modeladmintest/person/')

        # Check that the person was created
        self.assertEqual(Person.objects.filter(
            first_name="John",
            last_name="Doe",
            phone_number="+123456789"
        ).count(), 1)

        # verify that form fields are returned which have been defined
        # in Person.edit_handler
        response = self.client.get('/admin/modeladmintest/person/create/')
        self.assertIn('first_name', response.content.decode('UTF-8'))
        self.assertIn('last_name', response.content.decode('UTF-8'))
        self.assertIn('phone_number', response.content.decode('UTF-8'))
        self.assertNotIn('address', response.content.decode('UTF-8'))
        self.assertEqual(
            [ii for ii in response.context['form'].fields],
            ['first_name', 'last_name', 'phone_number']
        )

    def test_model_admin_edit_handler(self):
        # tests that edit_handler definition from modeladmin is used to create
        # a model instance if no edit_handler is set on the model
        response = self.client.post('/admin/modeladmintest/visitor/create/', {
            'first_name': "John",
            'last_name': "Doe",
            'address': "123 Main St Anytown",
            'phone_number': "+123456789"
        })
        # Should redirect back to index
        self.assertRedirects(response, '/admin/modeladmintest/visitor/')

        # Check that the person was created
        self.assertEqual(Visitor.objects.filter(
            last_name="Doe",
            phone_number="+123456789",
            address="123 Main St Anytown"
        ).count(), 1)

        # verify that form fields are returned which have been defined
        # in Person.edit_handler
        response = self.client.get('/admin/modeladmintest/visitor/create/')

        self.assertIn('last_name', response.content.decode('UTF-8'))
        self.assertIn('phone_number', response.content.decode('UTF-8'))
        self.assertIn('address', response.content.decode('UTF-8'))
        self.assertNotIn('first_name', response.content.decode('UTF-8'))
        self.assertEqual(
            [ii for ii in response.context['form'].fields],
            ['last_name', 'phone_number', 'address']
        )

    def test_model_admin_panels(self):
        # tests that panel definition from modeladmin is used to create
        # a model instance if no edit_handler is set on the model and modeladmin
        response = self.client.post('/admin/modeladmintest/contributor/create/', {
            'first_name': "John",
            'last_name': "Doe",
            'address': "123 Main St Anytown",
            'phone_number': "+123456789"
        })
        # Should redirect back to index
        self.assertRedirects(response, '/admin/modeladmintest/contributor/')

        # Check that the person was created
        self.assertEqual(Contributor.objects.filter(
            last_name="Doe",
            phone_number="+123456789",
            address="123 Main St Anytown"
        ).count(), 1)

        # verify that form fields are returned which have been defined
        # in Person.edit_handler
        response = self.client.get('/admin/modeladmintest/contributor/create/')

        self.assertIn('last_name', response.content.decode('UTF-8'))
        self.assertIn('phone_number', response.content.decode('UTF-8'))
        self.assertIn('address', response.content.decode('UTF-8'))
        self.assertNotIn('first_name', response.content.decode('UTF-8'))
        self.assertEqual(
            [ii for ii in response.context['form'].fields],
            ['last_name', 'phone_number', 'address']
        )
