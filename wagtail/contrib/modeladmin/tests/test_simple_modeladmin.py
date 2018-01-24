from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core import checks
from django.test import TestCase

import mock

from wagtail.admin.edit_handlers import FieldPanel, TabbedInterface
from wagtail.contrib.modeladmin.options import (
    ModelAdmin, ModelAdminGroup, get_modeladmin_models, modeladmin_register)
from wagtail.images.models import Image
from wagtail.images.tests.utils import get_test_image_file
from wagtail.tests.modeladmintest.models import (
    Author, Book, EventSupplier, PrintMediaCampaign, Publisher,
    SocialMediaCampaign, Token, VenuePage, VenuePageRelatedSeatingSection)
from wagtail.tests.utils import WagtailTestUtils



class TestBookIndexView(TestCase, WagtailTestUtils):
    fixtures = ['modeladmintest_test.json']

    def setUp(self):
        self.login()

        img = Image.objects.create(
            title="LOTR cover",
            file=get_test_image_file(),
        )
        book = Book.objects.get(title="The Lord of the Rings")
        book.cover_image = img
        book.save()

    def get(self, **params):
        return self.client.get('/admin/modeladmintest/book/', params)

    def test_simple(self):
        response = self.get()

        self.assertEqual(response.status_code, 200)

        # There are four books in the test data
        self.assertEqual(response.context['result_count'], 4)

        # User has add permission
        self.assertEqual(response.context['user_can_create'], True)

    def test_tr_attributes(self):
        response = self.get()

        # Charlie & The Chocolate factory should be in the list with the
        # `data-author_yob` and `data-object_pk` attributes added
        self.assertContains(response, 'data-author-yob="1916"')
        self.assertContains(response, 'data-object-pk="3"')

        # There should be two odd rows and two even ones, and 'book' should be
        # added to the `class` attribute for every one.
        self.assertContains(response, 'class="book odd"', count=2)
        self.assertContains(response, 'class="book even"', count=2)

    def test_filter(self):
        # Filter by author 1 (JRR Tolkien)
        response = self.get(author__id__exact=1)

        self.assertEqual(response.status_code, 200)

        # JRR Tolkien has two books in the test data
        self.assertEqual(response.context['result_count'], 2)

        for book in response.context['object_list']:
            self.assertEqual(book.author_id, 1)

    def test_search(self):
        response = self.get(q='of')

        self.assertEqual(response.status_code, 200)

        # There are two books where the title contains 'of'
        self.assertEqual(response.context['result_count'], 2)

    def test_ordering(self):
        response = self.get(o='0.1')

        self.assertEqual(response.status_code, 200)

        # There are four books in the test data
        self.assertEqual(response.context['result_count'], 4)

    def test_paging(self):
        # should be corrected to just the first page, as there aren't enough
        # objects to make up more than one page
        response = self.get(p=9)

        self.assertEqual(response.status_code, 200)

        # There are four books in the test data
        self.assertEqual(response.context['result_count'], 4)

        # Should raise a ValueError that gets caught during initialisation
        response = self.get(p='notaninteger')

        self.assertEqual(response.status_code, 200)

        # There are four books in the test data
        self.assertEqual(response.context['result_count'], 4)


class TestAuthorIndexView(TestCase, WagtailTestUtils):
    fixtures = ['modeladmintest_test.json']

    def setUp(self):
        self.login()

    def get(self, **params):
        return self.client.get('/admin/modeladmintest/author/', params)

    def test_col_extra_class_names(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        test_html = """
            <td class="field-first_book for-author-1">The Lord of the Rings</td>
        """
        self.assertContains(response, test_html, html=True)

    def test_col_extra_attributes(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        test_html = """
            <td class="field-last_book" data-for_author="1">The Hobbit</td>
        """
        self.assertContains(response, test_html, html=True)


class TestCreateView(TestCase, WagtailTestUtils):
    fixtures = ['modeladmintest_test.json']

    def setUp(self):
        self.login()

    def get(self):
        return self.client.get('/admin/modeladmintest/book/create/')

    def post(self, post_data):
        return self.client.post('/admin/modeladmintest/book/create/', post_data)

    def test_simple(self):
        response = self.get()

        self.assertEqual(response.status_code, 200)

    def test_create(self):
        response = self.post({
            'title': "George's Marvellous Medicine",
            'author': 2,
        })
        # Should redirect back to index
        self.assertRedirects(response, '/admin/modeladmintest/book/')

        # Check that the book was created
        self.assertEqual(Book.objects.filter(title="George's Marvellous Medicine").count(), 1)

        response = self.client.get('/admin/modeladmintest/publisher/create/')
        self.assertIn('name', response.content.decode('UTF-8'))
        self.assertNotIn('headquartered_in', response.content.decode('UTF-8'))
        self.assertEqual(
            [ii for ii in response.context['form'].fields],
            ['name']
        )
        self.client.post('/admin/modeladmintest/publisher/create/', {
            'name': 'Sharper Collins'
        })
        publisher = Publisher.objects.get(name='Sharper Collins')
        self.assertEqual(publisher.headquartered_in, None)

    def test_post_invalid(self):
        initial_book_count = Book.objects.count()

        response = self.post({
            'title': '',
            'author': 2,
        })
        final_book_count = Book.objects.count()

        self.assertEqual(response.status_code, 200)
        # Check that the book was not created
        self.assertEqual(initial_book_count, final_book_count)

        # Check that a form error was raised
        self.assertFormError(response, 'form', 'title', "This field is required.")

    def test_exclude_passed_to_extract_panel_definitions(self):
        path_to_form_fields_exclude_property = 'wagtail.contrib.modeladmin.options.ModelAdmin.form_fields_exclude'
        with mock.patch('wagtail.contrib.modeladmin.views.extract_panel_definitions_from_model_class') as m:
            with mock.patch(path_to_form_fields_exclude_property, new_callable=mock.PropertyMock) as mock_form_fields_exclude:
                mock_form_fields_exclude.return_value = ['123']

                self.get()
                mock_form_fields_exclude.assert_called()
                m.assert_called_with(Book, exclude=mock_form_fields_exclude.return_value)


class TestInspectView(TestCase, WagtailTestUtils):
    fixtures = ['modeladmintest_test.json']

    def setUp(self):
        self.login()

        img = Image.objects.create(
            title="LOTR cover",
            file=get_test_image_file(),
        )
        book = Book.objects.get(title="The Lord of the Rings")
        book.cover_image = img
        book.save()

    def get_for_author(self, author_id):
        return self.client.get('/admin/modeladmintest/author/inspect/%d/' % author_id)

    def get_for_book(self, book_id):
        return self.client.get('/admin/modeladmintest/book/inspect/%d/' % book_id)

    def test_author_simple(self):
        response = self.get_for_author(1)
        self.assertEqual(response.status_code, 200)

    def test_author_name_present(self):
        """
        The author name should appear twice. Once in the header, and once
        more in the field listing
        """
        response = self.get_for_author(1)
        self.assertContains(response, 'J. R. R. Tolkien', 2)

    def test_author_dob_not_present(self):
        """
        The date of birth shouldn't appear, because the field wasn't included
        in the `inspect_view_fields` list
        """
        response = self.get_for_author(1)
        self.assertNotContains(response, '1892')

    def test_book_simple(self):
        response = self.get_for_book(1)
        self.assertEqual(response.status_code, 200)

    def test_book_title_present(self):
        """
        The book title should appear once only, in the header, as 'title'
        was added to the `inspect_view_fields_ignore` list
        """
        response = self.get_for_book(1)
        self.assertContains(response, 'The Lord of the Rings', 1)

    def test_book_author_present(self):
        """
        The author name should appear, because 'author' is not in
        `inspect_view_fields_ignore` and should be returned by the
        `get_inspect_view_fields` method.
        """
        response = self.get_for_book(1)
        self.assertContains(response, 'J. R. R. Tolkien', 1)

    def test_non_existent(self):
        response = self.get_for_book(100)
        self.assertEqual(response.status_code, 404)


class TestEditView(TestCase, WagtailTestUtils):
    fixtures = ['modeladmintest_test.json']

    def setUp(self):
        self.login()

    def get(self, book_id):
        return self.client.get('/admin/modeladmintest/book/edit/%d/' % book_id)

    def post(self, book_id, post_data):
        return self.client.post('/admin/modeladmintest/book/edit/%d/' % book_id, post_data)

    def test_simple(self):
        response = self.get(1)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'The Lord of the Rings')

    def test_non_existent(self):
        response = self.get(100)

        self.assertEqual(response.status_code, 404)

    def test_edit(self):
        response = self.post(1, {
            'title': 'The Lady of the Rings',
            'author': 1,
        })

        # Should redirect back to index
        self.assertRedirects(response, '/admin/modeladmintest/book/')

        # Check that the book was updated
        self.assertEqual(Book.objects.get(id=1).title, 'The Lady of the Rings')

    def test_post_invalid(self):
        response = self.post(1, {
            'title': '',
            'author': 1,
        })

        self.assertEqual(response.status_code, 200)

        # Check that the title was not updated
        self.assertEqual(Book.objects.get(id=1).title, 'The Lord of the Rings')

        # Check that a form error was raised
        self.assertFormError(response, 'form', 'title', "This field is required.")

    def test_exclude_passed_to_extract_panel_definitions(self):
        path_to_form_fields_exclude_property = 'wagtail.contrib.modeladmin.options.ModelAdmin.form_fields_exclude'
        with mock.patch('wagtail.contrib.modeladmin.views.extract_panel_definitions_from_model_class') as m:
            with mock.patch(path_to_form_fields_exclude_property, new_callable=mock.PropertyMock) as mock_form_fields_exclude:
                mock_form_fields_exclude.return_value = ['123']

                self.get(1)
                mock_form_fields_exclude.assert_called()
                m.assert_called_with(Book, exclude=mock_form_fields_exclude.return_value)


class TestPageSpecificViews(TestCase, WagtailTestUtils):
    fixtures = ['modeladmintest_test.json']
    expected_status_code = 404

    def setUp(self):
        self.login()

    def test_choose_parent(self):
        response = self.client.get('/admin/modeladmintest/book/choose_parent/')
        self.assertEqual(response.status_code, self.expected_status_code)


class TestConfirmDeleteView(TestCase, WagtailTestUtils):
    fixtures = ['modeladmintest_test.json']

    def setUp(self):
        self.login()

    def get(self, book_id):
        return self.client.get('/admin/modeladmintest/book/delete/%d/' % book_id)

    def post(self, book_id):
        return self.client.post('/admin/modeladmintest/book/delete/%d/' % book_id)

    def test_simple(self):
        response = self.get(1)

        self.assertEqual(response.status_code, 200)

    def test_non_existent(self):
        response = self.get(100)

        self.assertEqual(response.status_code, 404)

    def test_post(self):
        response = self.post(1)

        # User redirected to index
        self.assertRedirects(response, '/admin/modeladmintest/book/')

        # Book deleted
        self.assertFalse(Book.objects.filter(id=1).exists())


class TestDeleteViewWithProtectedRelation(TestCase, WagtailTestUtils):
    fixtures = ['modeladmintest_test.json']

    def setUp(self):
        self.login()

    def get(self, author_id):
        return self.client.get('/admin/modeladmintest/author/delete/%d/' % author_id)

    def post(self, author_id):
        return self.client.post('/admin/modeladmintest/author/delete/%d/' % author_id)

    def test_get_with_dependent_object(self):
        response = self.get(1)

        self.assertEqual(response.status_code, 200)

    def test_get_without_dependent_object(self):
        response = self.get(4)

        self.assertEqual(response.status_code, 200)

    def test_post_with_dependent_object(self):
        response = self.post(1)

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "'J. R. R. Tolkien' is currently referenced by other objects"
        )
        self.assertContains(
            response,
            "<li><b>Book:</b> The Lord of the Rings</li>"
        )

        # Author not deleted
        self.assertTrue(Author.objects.filter(id=1).exists())

    def test_post_without_dependent_object(self):
        response = self.post(4)

        # User redirected to index
        self.assertRedirects(response, '/admin/modeladmintest/author/')

        # Author deleted
        self.assertFalse(Author.objects.filter(id=4).exists())


class TestDeleteViewModelReprPrimary(TestCase, WagtailTestUtils):
    fixtures = ['modeladmintest_test.json']

    def setUp(self):
        self.login()

    def test_delete(self):
        response = self.client.post('/admin/modeladmintest/token/delete/boom/')
        self.assertEqual(response.status_code, 302)


class TestEditorAccess(TestCase):
    fixtures = ['modeladmintest_test.json']
    expected_status_code = 403

    def login(self):
        # Create a user
        user = get_user_model().objects._create_user(username='test2', email='test2@email.com', password='password', is_staff=True, is_superuser=False)
        user.groups.add(Group.objects.get(pk=2))
        # Login
        self.client.login(username='test2', password='password')

        return user

    def setUp(self):
        self.login()

    def test_index_permitted(self):
        response = self.client.get('/admin/modeladmintest/book/')
        self.assertEqual(response.status_code, self.expected_status_code)

    def test_inpspect_permitted(self):
        response = self.client.get('/admin/modeladmintest/book/inspect/2/')
        self.assertEqual(response.status_code, self.expected_status_code)

    def test_create_permitted(self):
        response = self.client.get('/admin/modeladmintest/book/create/')
        self.assertEqual(response.status_code, self.expected_status_code)

    def test_edit_permitted(self):
        response = self.client.get('/admin/modeladmintest/book/edit/2/')
        self.assertEqual(response.status_code, self.expected_status_code)

    def test_delete_get_permitted(self):
        response = self.client.get('/admin/modeladmintest/book/delete/2/')
        self.assertEqual(response.status_code, self.expected_status_code)

    def test_delete_post_permitted(self):
        response = self.client.post('/admin/modeladmintest/book/delete/2/')
        self.assertEqual(response.status_code, self.expected_status_code)


class TestQuoting(TestCase, WagtailTestUtils):
    fixtures = ['modeladmintest_test.json']
    expected_status_code = 200

    def setUp(self):
        self.login()
        self.tok_reg = Token.objects.create(key="RegularName")
        self.tok_irr = Token.objects.create(key="Irregular_Name")

    def test_action_links(self):
        response = self.client.get('/admin/modeladmintest/token/')

        self.assertContains(response, 'href="/admin/modeladmintest/token/edit/RegularName/"')
        self.assertContains(response, 'href="/admin/modeladmintest/token/delete/RegularName/"')
        self.assertContains(response, 'href="/admin/modeladmintest/token/edit/Irregular_5FName/"')
        self.assertContains(response, 'href="/admin/modeladmintest/token/delete/Irregular_5FName/"')

        response = self.client.get('/admin/modeladmintest/token/edit/Irregular_5FName/')
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/admin/modeladmintest/token/delete/Irregular_5FName/')
        self.assertEqual(response.status_code, 200)


class TestModelAdminRegistration(TestCase, WagtailTestUtils):
    """Tests the registration of modeladmin models works as intended."""

    def test_registration_of_model_admin(self):
        modeladmin_models_before = get_modeladmin_models()
        self.assertNotIn(SocialMediaCampaign, modeladmin_models_before)

        class SocialMediaCampaignAdmin(ModelAdmin):
            model = SocialMediaCampaign

        modeladmin_register(SocialMediaCampaignAdmin)

        modeladmin_models_after = get_modeladmin_models()
        self.assertIn(SocialMediaCampaign, modeladmin_models_after)

    def test_registration_of_model_admin_group(self):
        modeladmin_models_before = get_modeladmin_models()
        self.assertNotIn(PrintMediaCampaign, modeladmin_models_before)

        class SocialMediaCampaignAdmin(ModelAdmin):
            model = SocialMediaCampaign

        class PrintMediaCampaignAdmin(ModelAdmin):
            model = PrintMediaCampaign

        class CampaignsAdminGroup(ModelAdminGroup):
            items = (
                SocialMediaCampaignAdmin,
                PrintMediaCampaignAdmin,
            )

        modeladmin_register(CampaignsAdminGroup)

        modeladmin_models_after = get_modeladmin_models()
        self.assertIn(PrintMediaCampaign, modeladmin_models_after)

    def test_model_admin_registered_models(self):
        """Test models within ModelAdmin are registered correctly."""
        modeladmin_models = get_modeladmin_models()
        self.assertIn(Author, modeladmin_models)
        self.assertIn(Book, modeladmin_models)

    def test_model_admin_group_registered_models(self):
        """Test models within a ModelAdminGroup are registered correctly."""
        modeladmin_models = get_modeladmin_models()
        self.assertIn(EventSupplier, modeladmin_models)
        self.assertIn(VenuePage, modeladmin_models)


class TestPanelConfigurationChecksInModelAdmin(TestCase, WagtailTestUtils):

    def test_model_with_single_tabbed_panel_only(self):

        Publisher.content_panels = [FieldPanel('name'), FieldPanel('headquartered_in')]

        warning = checks.Warning(
            "Publisher.content_panels will have no effect on modeladmin editing",
            hint="""Ensure that Publisher uses `panels` instead of `content_panels`
        or set up an `edit_handler` if you want a tabbed editing interface.
        There are no default tabs on non-Page models so there will be no
        Content tab for the content_panels to render in.""",
            obj=Publisher,
            id='wagtailadmin.W002',
        )

        # run checks only with the 'panels' tag
        errors = [e for e in checks.run_checks(tags=['panels']) if e.obj == Publisher]
        self.assertEqual(errors, [warning])

        # clean up for future checks
        del Publisher.content_panels


    def test_model_with_two_tabbed_panels_only(self):

        Publisher.settings_panels = [FieldPanel('name')]
        Publisher.promote_panels = [FieldPanel('headquartered_in')]


        warning_1 = checks.Warning(
            "Publisher.promote_panels will have no effect on modeladmin editing",
            hint="""Ensure that Publisher uses `panels` instead of `promote_panels`
        or set up an `edit_handler` if you want a tabbed editing interface.
        There are no default tabs on non-Page models so there will be no
        Promote tab for the promote_panels to render in.""",
            obj=Publisher,
            id='wagtailadmin.W002',
        )

        warning_2 = checks.Warning(
            "Publisher.settings_panels will have no effect on modeladmin editing",
            hint="""Ensure that Publisher uses `panels` instead of `settings_panels`
        or set up an `edit_handler` if you want a tabbed editing interface.
        There are no default tabs on non-Page models so there will be no
        Settings tab for the settings_panels to render in.""",
            obj=Publisher,
            id='wagtailadmin.W002',
        )

        # run checks only with the 'panels' tag
        errors = [e for e in checks.run_checks(tags=['panels']) if e.obj == Publisher]
        self.assertEqual(errors, [warning_1, warning_2])

        # clean up for future checks
        del Publisher.settings_panels
        del Publisher.promote_panels


    def test_model_with_single_tabbed_panel_and_edit_handler(self):

        Publisher.content_panels = [FieldPanel('name'), FieldPanel('headquartered_in')]
        Publisher.edit_handler = TabbedInterface(Publisher.content_panels)

        # run checks only with the 'panels' tag
        errors = [e for e in checks.run_checks(tags=['panels']) if e.obj == Publisher]
        # no errors should occur
        self.assertEqual(errors, [])

        del Publisher.content_panels
        del Publisher.edit_handler


class TestPanelConfigurationChecksInModelAdminGroup(TestCase, WagtailTestUtils):

    def test_model_with_single_tabbed_panel_only(self):

        EventSupplier.content_panels = [FieldPanel('name'), FieldPanel('website')]

        warning = checks.Warning(
            "EventSupplier.content_panels will have no effect on modeladmin editing",
            hint="""Ensure that EventSupplier uses `panels` instead of `content_panels`
        or set up an `edit_handler` if you want a tabbed editing interface.
        There are no default tabs on non-Page models so there will be no
        Content tab for the content_panels to render in.""",
            obj=EventSupplier,
            id='wagtailadmin.W002',
        )

        # run checks only with the 'panels' tag
        errors = [e for e in checks.run_checks(tags=['panels']) if e.obj == EventSupplier]
        self.assertEqual(errors, [warning])

        # clean up for future checks
        del EventSupplier.content_panels


    def test_inline_panel_related_model(self):
        """Check that a modeladmin model's inlinepanel related model is checked."""

        VenuePageRelatedSeatingSection.content_panels = [
            FieldPanel('name'), FieldPanel('seats')]

        warning = checks.Warning(
            "VenuePageRelatedSeatingSection.content_panels will have no effect on InlinePanel model editing",
            hint="""Ensure that VenuePageRelatedSeatingSection uses `panels` instead of `content_panels`.
        There are no tabs on non-Page model editing within InlinePanels.
        """,
            obj=VenuePageRelatedSeatingSection,
            id='wagtailadmin.W002',
        )

        # run checks only with the 'panels' tag
        errors = [e for e in checks.run_checks(tags=['panels']) if e.obj == VenuePageRelatedSeatingSection]
        self.assertIn(warning, errors)

        # clean up for future checks
        del VenuePageRelatedSeatingSection.content_panels


    def test_model_with_two_tabbed_panels_only(self):

        EventSupplier.settings_panels = [FieldPanel('name'), FieldPanel('email')]
        EventSupplier.promote_panels = [FieldPanel('area')]


        warning_1 = checks.Warning(
            "EventSupplier.promote_panels will have no effect on modeladmin editing",
            hint="""Ensure that EventSupplier uses `panels` instead of `promote_panels`
        or set up an `edit_handler` if you want a tabbed editing interface.
        There are no default tabs on non-Page models so there will be no
        Promote tab for the promote_panels to render in.""",
            obj=EventSupplier,
            id='wagtailadmin.W002',
        )

        warning_2 = checks.Warning(
            "EventSupplier.settings_panels will have no effect on modeladmin editing",
            hint="""Ensure that EventSupplier uses `panels` instead of `settings_panels`
        or set up an `edit_handler` if you want a tabbed editing interface.
        There are no default tabs on non-Page models so there will be no
        Settings tab for the settings_panels to render in.""",
            obj=EventSupplier,
            id='wagtailadmin.W002',
        )

        # run checks only with the 'panels' tag
        errors = [e for e in checks.run_checks(tags=['panels']) if e.obj == EventSupplier]
        self.assertEqual(errors, [warning_1, warning_2])

        # clean up for future checks
        del EventSupplier.settings_panels
        del EventSupplier.promote_panels


    def test_model_with_single_tabbed_panel_and_edit_handler(self):

        EventSupplier.content_panels = [FieldPanel('name'), FieldPanel('email')]
        EventSupplier.edit_handler = TabbedInterface(EventSupplier.content_panels)

        # run checks only with the 'panels' tag
        errors = [e for e in checks.run_checks(tags=['panels']) if e.obj == EventSupplier]
        # no errors should occur
        self.assertEqual(errors, [])

        del EventSupplier.content_panels
        del EventSupplier.edit_handler
