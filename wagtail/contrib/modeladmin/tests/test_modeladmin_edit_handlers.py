from unittest import mock

from django.test import RequestFactory, TestCase

from wagtail.contrib.modeladmin.views import CreateView
from wagtail.tests.modeladmintest.models import Person
from wagtail.tests.modeladmintest.wagtail_hooks import PersonAdmin
from wagtail.tests.utils import WagtailTestUtils


class TestExtractPanelDefinitionsFromModelAdmin(TestCase, WagtailTestUtils):
    """tests that edit_handler and panels can be defined on modeladmin"""

    def setUp(self):
        self.factory = RequestFactory()
        self.user = self.create_test_user()
        self.login(user=self.user)

    def test_model_edit_handler(self):
        # loads the 'create' view and verifies that form fields are returned
        # which have been defined via model Person.edit_handler
        response = self.client.get('/admin/modeladmintest/person/create/')
        self.assertEqual(
            [field_name for field_name in response.context['form'].fields],
            ['first_name', 'last_name', 'phone_number']
        )

    @mock.patch('wagtail.contrib.modeladmin.views.ModelFormView.get_edit_handler')
    def test_model_form_view_edit_handler_called(self, mock_modelformview_get_edit_handler):
        """loads the ``create`` view and verifies that modelformview edit_handler is called"""
        self.client.get('/admin/modeladmintest/person/create/')
        self.assertGreater(len(mock_modelformview_get_edit_handler.call_args_list), 0)

    @mock.patch('wagtail.contrib.modeladmin.options.ModelAdmin.get_edit_handler')
    def test_model_admin_edit_handler_called(self, mock_modeladmin_get_edit_handler):
        """loads the ``create`` view and verifies that modeladmin edit_handler is called"""
        # constructing the request in order to be able to assert it
        request = self.factory.get('/admin/modeladmintest/person/create/')
        request.user = self.user
        view = CreateView.as_view(model_admin=PersonAdmin())
        view(request)

        edit_handler_call = mock_modeladmin_get_edit_handler.call_args_list[0]
        call_args, call_kwargs = edit_handler_call
        # not using CreateView.get_instance since
        # CreateView.get_instance always returns a new instance
        self.assertEqual(type(call_kwargs['instance']), Person)
        self.assertEqual(call_kwargs['request'], request)

    def test_model_panels(self):
        # loads the 'create' view and verifies that form fields are returned
        # which have been defined via model Friend.panels
        response = self.client.get('/admin/modeladmintest/friend/create/')
        self.assertEqual(
            [field_name for field_name in response.context['form'].fields],
            ['first_name', 'phone_number']
        )

    def test_model_admin_edit_handler(self):
        # loads the 'create' view and verifies that form fields are returned
        # which have been defined via model VisitorAdmin.edit_handler
        response = self.client.get('/admin/modeladmintest/visitor/create/')
        self.assertEqual(
            [field_name for field_name in response.context['form'].fields],
            ['last_name', 'phone_number', 'address']
        )

    @mock.patch('wagtail.contrib.modeladmin.views.ModelFormView.get_edit_handler')
    def test_model_admin_edit_handler_form_view_edit_handler_called(self, mock_modelformview_get_edit_handler):
        # loads the 'create' view and verifies
        # that modelformview edit_handler is called
        self.client.get('/admin/modeladmintest/visitor/create/')
        mock_modelformview_get_edit_handler.assert_called()

    @mock.patch('wagtail.contrib.modeladmin.options.ModelAdmin.get_edit_handler')
    def test_model_admin_edit_handler_edit_handler_called(self, mock_modeladmin_get_edit_handler):
        # loads the 'create' view and verifies
        # that modeladmin edit_handler is called
        self.client.get('/admin/modeladmintest/visitor/create/')
        mock_modeladmin_get_edit_handler.assert_called()

    def test_model_admin_panels(self):
        # loads the 'create' view and verifies that form fields are returned
        # which have been defined via model ContributorAdmin.panels
        response = self.client.get('/admin/modeladmintest/contributor/create/')
        self.assertEqual(
            [field_name for field_name in response.context['form'].fields],
            ['last_name', 'phone_number', 'address']
        )

    @mock.patch('wagtail.contrib.modeladmin.views.ModelFormView.get_edit_handler')
    def test_model_admin_panels_form_view_edit_handler_called(self, mock_modelformview_get_edit_handler):
        # loads the 'create' view and verifies
        # that modelformview edit_handler is called
        self.client.get('/admin/modeladmintest/contributor/create/')
        mock_modelformview_get_edit_handler.assert_called()

    @mock.patch('wagtail.contrib.modeladmin.options.ModelAdmin.get_edit_handler')
    def test_model_admin_panels_admin_edit_handler_called(self, mock_modeladmin_get_edit_handler):
        # loads the 'create' view and verifies
        # that modeladmin edit_handler is called
        self.client.get('/admin/modeladmintest/contributor/create/')
        mock_modeladmin_get_edit_handler.assert_called()
