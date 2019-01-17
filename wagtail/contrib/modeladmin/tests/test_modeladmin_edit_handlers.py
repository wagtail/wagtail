import mock
from django.test import TestCase

from wagtail.tests.utils import WagtailTestUtils


class TestExtractPanelDefinitionsFromModelAdmin(TestCase, WagtailTestUtils):
    """tests that edit_handler and panels can be defined on modeladmin"""

    def setUp(self):
        self.login()

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
        # loads the 'create' view and verifies
        # that modelformview edit_handler is called
        self.client.get('/admin/modeladmintest/person/create/')
        mock_modelformview_get_edit_handler.assert_called()

    @mock.patch('wagtail.contrib.modeladmin.options.ModelAdmin.get_edit_handler')
    def test_model_admin_edit_handler_called(self, mock_modeladmin_get_edit_handler):
        # loads the 'create' view and verifies
        # that modeladmin edit_handler is called
        self.client.get('/admin/modeladmintest/person/create/')
        mock_modeladmin_get_edit_handler.assert_called()

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
