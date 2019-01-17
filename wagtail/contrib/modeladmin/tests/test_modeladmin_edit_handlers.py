from unittest import mock

from django.test import RequestFactory, TestCase

from wagtail.admin.edit_handlers import FieldPanel, ObjectList, TabbedInterface
from wagtail.contrib.modeladmin.options import ModelAdmin
from wagtail.contrib.modeladmin.views import CreateView
from wagtail.tests.modeladmintest.models import Person
from wagtail.tests.modeladmintest.wagtail_hooks import PersonAdmin
from wagtail.tests.utils import WagtailTestUtils


class PersonAdminWithPanels(ModelAdmin):
    model = Person

    panels = [
        FieldPanel('last_name'),
        FieldPanel('phone_number'),
        FieldPanel('address'),
    ]


class PersonAdminWithEditHandler(ModelAdmin):
    model = Person

    edit_handler = TabbedInterface([
        ObjectList(
            [
                FieldPanel('phone_number'),
                FieldPanel('address'),
            ]
        ),
    ])


class TestExtractPanelDefinitionsFromModelAdmin(TestCase, WagtailTestUtils):
    """tests that edit_handler and panels can be defined on modeladmin"""

    def setUp(self):
        self.factory = RequestFactory()
        self.user = self.create_test_user()
        self.login(user=self.user)

    def test_model_edit_handler(self):
        """loads the 'create' view and verifies that form fields are returned
        which have been defined via model Person.edit_handler"""
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
        """loads the 'create' view and verifies that form fields are returned
        which have been defined via model Friend.panels"""
        response = self.client.get('/admin/modeladmintest/friend/create/')
        self.assertEqual(
            [field_name for field_name in response.context['form'].fields],
            ['first_name', 'phone_number']
        )

    def test_model_admin_panels_preferred_over_model_panels(self):
        """verifies that model admin panels are preferred over model panels"""
        # first, call the view with our default PersonAdmin which has no
        # panels defined. That verifies that the panels defined on the model
        # are used
        request = self.factory.get('/admin/modeladmintest/person/create/')
        request.user = self.user
        view = CreateView.as_view(model_admin=PersonAdmin())
        response = view(request)
        self.assertEqual(
            [field_name for field_name in response.context_data['form'].fields],
            ['first_name', 'last_name', 'phone_number']
        )

        # now call the same view with another model_admin that has panels
        # defined. here we verify that panels defined on PersonAdminWithPanels
        # are used and therefore are preferred over the ones on the
        # Person model
        request = self.factory.get('/admin/modeladmintest/person/create/')
        request.user = self.user
        view = CreateView.as_view(model_admin=PersonAdminWithPanels())
        response = view(request)
        self.assertEqual(
            [field_name for field_name in response.context_data['form'].fields],
            ['last_name', 'phone_number', 'address']
        )

    def test_model_admin_edit_handler_preferred_over_model_panels(self):
        """verifies that model admin panels are preferred over model panels"""
        # first, call the view with our default PersonAdmin which has no
        # panels defined. That verifies that the panels defined on the model
        # are used
        request = self.factory.get('/admin/modeladmintest/person/create/')
        request.user = self.user
        view = CreateView.as_view(model_admin=PersonAdmin())
        response = view(request)
        self.assertEqual(
            [field_name for field_name in response.context_data['form'].fields],
            ['first_name', 'last_name', 'phone_number']
        )

        # now call the same view with another model_admin that has panels
        # defined. here we verify that panels defined on PersonAdminWithEditHandler
        # are used and therefore are preferred over the ones on the
        # Person model
        request = self.factory.get('/admin/modeladmintest/person/create/')
        request.user = self.user
        view = CreateView.as_view(model_admin=PersonAdminWithEditHandler())
        response = view(request)
        self.assertEqual(
            [field_name for field_name in response.context_data['form'].fields],
            ['phone_number', 'address']
        )

    def test_model_admin_edit_handler(self):
        """loads the 'create' view and verifies that form fields are returned
        which have been defined via model VisitorAdmin.edit_handler"""
        response = self.client.get('/admin/modeladmintest/visitor/create/')
        self.assertEqual(
            [field_name for field_name in response.context['form'].fields],
            ['last_name', 'phone_number', 'address']
        )

    def test_model_admin_panels(self):
        """loads the 'create' view and verifies that form fields are returned
        which have been defined via model ContributorAdmin.panels"""
        response = self.client.get('/admin/modeladmintest/contributor/create/')
        self.assertEqual(
            [field_name for field_name in response.context['form'].fields],
            ['last_name', 'phone_number', 'address']
        )
