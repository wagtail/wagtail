from __future__ import absolute_import, unicode_literals

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.exceptions import ImproperlyConfigured
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.utils import override_settings
from taggit.models import Tag

from wagtail.tests.snippets.forms import FancySnippetForm
from wagtail.tests.snippets.models import (
    AlphaSnippet, FancySnippet, FileUploadSnippet, RegisterDecorator, RegisterFunction,
    SearchableSnippet, StandardSnippet, ZuluSnippet)
from wagtail.tests.testapp.models import Advert, AdvertWithTabbedInterface, SnippetChooserModel
from wagtail.tests.utils import WagtailTestUtils
from wagtail.wagtailadmin.forms import WagtailAdminModelForm
from wagtail.wagtailcore.models import Page
from wagtail.wagtailsnippets.edit_handlers import SnippetChooserPanel
from wagtail.wagtailsnippets.models import SNIPPET_MODELS, register_snippet
from wagtail.wagtailsnippets.views.snippets import get_snippet_edit_handler


class TestSnippetIndexView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

    def get(self, params={}):
        return self.client.get(reverse('wagtailsnippets:index'), params)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailsnippets/snippets/index.html')

    def test_displays_snippet(self):
        self.assertContains(self.get(), "Adverts")


class TestSnippetListView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

    def get(self, params={}):
        return self.client.get(reverse('wagtailsnippets:list',
                                       args=('tests', 'advert')),
                               params)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailsnippets/snippets/type_index.html')

    def test_simple_pagination(self):

        pages = ['0', '1', '-1', '9999', 'Not a page']
        for page in pages:
            response = self.get({'p': page})
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'wagtailsnippets/snippets/type_index.html')

    def test_displays_add_button(self):
        self.assertContains(self.get(), "Add advert")

    def test_not_searchable(self):
        self.assertFalse(self.get().context['is_searchable'])


class TestSnippetListViewWithSearchableSnippet(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

        # Create some instances of the searchable snippet for testing
        self.snippet_a = SearchableSnippet.objects.create(text="Hello")
        self.snippet_b = SearchableSnippet.objects.create(text="World")
        self.snippet_c = SearchableSnippet.objects.create(text="Hello World")

    def get(self, params={}):
        return self.client.get(reverse('wagtailsnippets:list',
                                       args=('snippetstests', 'searchablesnippet')),
                               params)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailsnippets/snippets/type_index.html')

        # All snippets should be in items
        items = list(response.context['items'].object_list)
        self.assertIn(self.snippet_a, items)
        self.assertIn(self.snippet_b, items)
        self.assertIn(self.snippet_c, items)

    def test_is_searchable(self):
        self.assertTrue(self.get().context['is_searchable'])

    def test_search_hello(self):
        response = self.get({'q': "Hello"})

        # Just snippets with "Hello" should be in items
        items = list(response.context['items'].object_list)
        self.assertIn(self.snippet_a, items)
        self.assertNotIn(self.snippet_b, items)
        self.assertIn(self.snippet_c, items)

    def test_search_world(self):
        response = self.get({'q': "World"})

        # Just snippets with "World" should be in items
        items = list(response.context['items'].object_list)
        self.assertNotIn(self.snippet_a, items)
        self.assertIn(self.snippet_b, items)
        self.assertIn(self.snippet_c, items)


class TestSnippetCreateView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

    def get(self, params={}, model=Advert):
        args = (model._meta.app_label, model._meta.model_name)
        return self.client.get(reverse('wagtailsnippets:add', args=args), params)

    def post(self, post_data={}, model=Advert):
        args = (model._meta.app_label, model._meta.model_name)
        return self.client.post(reverse('wagtailsnippets:add', args=args), post_data)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailsnippets/snippets/create.html')
        self.assertNotContains(response, '<ul class="tab-nav merged">')
        self.assertNotContains(response, '<a href="#advert" class="active">Advert</a>', html=True)
        self.assertNotContains(response, '<a href="#other" class="">Other</a>', html=True)

    def test_snippet_with_tabbed_interface(self):
        response = self.client.get(reverse('wagtailsnippets:add',
                                           args=('tests', 'advertwithtabbedinterface')))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailsnippets/snippets/create.html')
        self.assertContains(response, '<ul class="tab-nav merged">')
        self.assertContains(response, '<a href="#advert" class="active">Advert</a>', html=True)
        self.assertContains(response, '<a href="#other" class="">Other</a>', html=True)

    def test_create_invalid(self):
        response = self.post(post_data={'foo': 'bar'})
        self.assertContains(response, "The snippet could not be created due to errors.")
        self.assertContains(response, "This field is required.")

    def test_create(self):
        response = self.post(post_data={'text': 'test_advert',
                                        'url': 'http://www.example.com/'})
        self.assertRedirects(response, reverse('wagtailsnippets:list', args=('tests', 'advert')))

        snippets = Advert.objects.filter(text='test_advert')
        self.assertEqual(snippets.count(), 1)
        self.assertEqual(snippets.first().url, 'http://www.example.com/')

    def test_create_with_tags(self):
        tags = ['hello', 'world']
        response = self.post(post_data={'text': 'test_advert',
                                        'url': 'http://example.com/',
                                        'tags': ', '.join(tags)})

        self.assertRedirects(response, reverse('wagtailsnippets:list',
                                               args=('tests', 'advert')))

        snippet = Advert.objects.get(text='test_advert')

        expected_tags = list(Tag.objects.order_by('name').filter(name__in=tags))
        self.assertEqual(len(expected_tags), 2)
        self.assertEqual(
            list(snippet.tags.order_by('name')),
            expected_tags)

    def test_create_file_upload_multipart(self):
        response = self.get(model=FileUploadSnippet)
        self.assertContains(response, 'enctype="multipart/form-data"')

        response = self.post(model=FileUploadSnippet, post_data={
            'file': SimpleUploadedFile('test.txt', b"Uploaded file")})
        self.assertRedirects(response, reverse('wagtailsnippets:list',
                                               args=('snippetstests', 'fileuploadsnippet')))
        snippet = FileUploadSnippet.objects.get()
        self.assertEqual(snippet.file.read(), b"Uploaded file")


class BaseTestSnippetEditView(TestCase, WagtailTestUtils):

    def get(self, params={}):
        snippet = self.test_snippet
        args = (snippet._meta.app_label, snippet._meta.model_name, snippet.id)
        return self.client.get(reverse('wagtailsnippets:edit', args=args), params)

    def post(self, post_data={}):
        snippet = self.test_snippet
        args = (snippet._meta.app_label, snippet._meta.model_name, snippet.id)
        return self.client.post(reverse('wagtailsnippets:edit', args=args), post_data)

    def setUp(self):
        self.login()


class TestSnippetEditView(BaseTestSnippetEditView):
    fixtures = ['test.json']

    def setUp(self):
        super(TestSnippetEditView, self).setUp()
        self.test_snippet = Advert.objects.get(id=1)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailsnippets/snippets/edit.html')
        self.assertNotContains(response, '<ul class="tab-nav merged">')
        self.assertNotContains(response, '<a href="#advert" class="active">Advert</a>', html=True)
        self.assertNotContains(response, '<a href="#other" class="">Other</a>', html=True)

    def test_non_existant_model(self):
        response = self.client.get(reverse('wagtailsnippets:edit', args=('tests', 'foo', self.test_snippet.id)))
        self.assertEqual(response.status_code, 404)

    def test_nonexistant_id(self):
        response = self.client.get(reverse('wagtailsnippets:edit', args=('tests', 'advert', 999999)))
        self.assertEqual(response.status_code, 404)

    def test_edit_invalid(self):
        response = self.post(post_data={'foo': 'bar'})
        self.assertContains(response, "The snippet could not be saved due to errors.")
        self.assertContains(response, "This field is required.")

    def test_edit(self):
        response = self.post(post_data={'text': 'edited_test_advert',
                                        'url': 'http://www.example.com/edited'})
        self.assertRedirects(response, reverse('wagtailsnippets:list', args=('tests', 'advert')))

        snippets = Advert.objects.filter(text='edited_test_advert')
        self.assertEqual(snippets.count(), 1)
        self.assertEqual(snippets.first().url, 'http://www.example.com/edited')

    def test_edit_with_tags(self):
        tags = ['hello', 'world']
        response = self.post(post_data={'text': 'edited_test_advert',
                                        'url': 'http://www.example.com/edited',
                                        'tags': ', '.join(tags)})

        self.assertRedirects(response, reverse('wagtailsnippets:list',
                                               args=('tests', 'advert')))

        snippet = Advert.objects.get(text='edited_test_advert')

        expected_tags = list(Tag.objects.order_by('name').filter(name__in=tags))
        self.assertEqual(len(expected_tags), 2)
        self.assertEqual(
            list(snippet.tags.order_by('name')),
            expected_tags)


class TestEditTabbedSnippet(BaseTestSnippetEditView):

    def setUp(self):
        super(TestEditTabbedSnippet, self).setUp()
        self.test_snippet = AdvertWithTabbedInterface.objects.create(
            text="test_advert",
            url="http://www.example.com",
            something_else="Model with tabbed interface")

    def test_snippet_with_tabbed_interface(self):
        response = self.get()

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailsnippets/snippets/edit.html')
        self.assertContains(response, '<ul class="tab-nav merged">')
        self.assertContains(response, '<a href="#advert" class="active">Advert</a>', html=True)
        self.assertContains(response, '<a href="#other" class="">Other</a>', html=True)


class TestEditFileUploadSnippet(BaseTestSnippetEditView):

    def setUp(self):
        super(TestEditFileUploadSnippet, self).setUp()
        self.test_snippet = FileUploadSnippet.objects.create(
            file=ContentFile(b"Simple text document", 'test.txt'))

    def test_edit_file_upload_multipart(self):
        response = self.get()
        self.assertContains(response, 'enctype="multipart/form-data"')

        response = self.post(post_data={
            'file': SimpleUploadedFile('replacement.txt', b"Replacement document")})
        self.assertRedirects(response, reverse('wagtailsnippets:list',
                                               args=('snippetstests', 'fileuploadsnippet')))
        snippet = FileUploadSnippet.objects.get()
        self.assertEqual(snippet.file.read(), b"Replacement document")


class TestSnippetDelete(TestCase, WagtailTestUtils):
    fixtures = ['test.json']

    def setUp(self):
        self.test_snippet = Advert.objects.get(id=1)
        self.login()

    def test_delete_get(self):
        response = self.client.get(reverse('wagtailsnippets:delete', args=('tests', 'advert', self.test_snippet.id, )))
        self.assertEqual(response.status_code, 200)

    def test_delete_post(self):
        response = self.client.post(
            reverse('wagtailsnippets:delete', args=('tests', 'advert', self.test_snippet.id, ))
        )

        # Should be redirected to explorer page
        self.assertRedirects(response, reverse('wagtailsnippets:list', args=('tests', 'advert')))

        # Check that the page is gone
        self.assertEqual(Advert.objects.filter(text='test_advert').count(), 0)


class TestSnippetChooserPanel(TestCase, WagtailTestUtils):
    fixtures = ['test.json']

    def setUp(self):
        model = SnippetChooserModel
        self.advert_text = 'Test advert text'
        test_snippet = model.objects.create(
            advert=Advert.objects.create(text=self.advert_text))

        self.edit_handler_class = get_snippet_edit_handler(model)
        self.form_class = self.edit_handler_class.get_form_class(model)
        form = self.form_class(instance=test_snippet)
        edit_handler = self.edit_handler_class(instance=test_snippet, form=form)

        self.snippet_chooser_panel = [
            panel for panel in edit_handler.children
            if getattr(panel, 'field_name', None) == 'advert'][0]

    def test_create_snippet_chooser_panel_class(self):
        self.assertEqual(type(self.snippet_chooser_panel).__name__,
                         '_SnippetChooserPanel')

    def test_render_as_field(self):
        field_html = self.snippet_chooser_panel.render_as_field()
        self.assertIn(self.advert_text, field_html)
        self.assertIn("Choose advert", field_html)
        self.assertIn("Choose another advert", field_html)

    def test_render_as_empty_field(self):
        test_snippet = SnippetChooserModel()
        form = self.form_class(instance=test_snippet)
        edit_handler = self.edit_handler_class(instance=test_snippet, form=form)

        snippet_chooser_panel = [
            panel for panel in edit_handler.children
            if getattr(panel, 'field_name', None) == 'advert'
        ][0]

        field_html = snippet_chooser_panel.render_as_field()
        self.assertIn("Choose advert", field_html)
        self.assertIn("Choose another advert", field_html)

    def test_render_js(self):
        self.assertIn('createSnippetChooser("id_advert", "tests/advert");',
                      self.snippet_chooser_panel.render_as_field())

    def test_target_model_from_string(self):
        # RemovedInWagtail16Warning: snippet_type argument
        with self.ignore_deprecation_warnings():
            result = SnippetChooserPanel(
                'advert',
                'tests.advert'
            ).bind_to_model(SnippetChooserModel).target_model()
            self.assertIs(result, Advert)

    def test_target_model_from_model(self):
        # RemovedInWagtail16Warning: snippet_type argument
        with self.ignore_deprecation_warnings():
            result = SnippetChooserPanel(
                'advert',
                Advert
            ).bind_to_model(SnippetChooserModel).target_model()
            self.assertIs(result, Advert)

    def test_target_model_autodetected(self):
        result = SnippetChooserPanel(
            'advert'
        ).bind_to_model(SnippetChooserModel).target_model()
        self.assertEqual(result, Advert)

    def test_target_model_malformed_type(self):
        # RemovedInWagtail16Warning: snippet_type argument
        with self.ignore_deprecation_warnings():
            result = SnippetChooserPanel(
                'advert',
                'snowman'
            ).bind_to_model(SnippetChooserModel)
            self.assertRaises(ImproperlyConfigured,
                              result.target_model)

    def test_target_model_nonexistent_type(self):
        # RemovedInWagtail16Warning: snippet_type argument
        with self.ignore_deprecation_warnings():
            result = SnippetChooserPanel(
                'advert',
                'snowman.lorry'
            ).bind_to_model(SnippetChooserModel)
            self.assertRaises(ImproperlyConfigured,
                              result.target_model)


class TestSnippetRegistering(TestCase):
    def test_register_function(self):
        self.assertIn(RegisterFunction, SNIPPET_MODELS)

    def test_register_decorator(self):
        # Misbehaving decorators often return None
        self.assertIsNotNone(RegisterDecorator)
        self.assertIn(RegisterDecorator, SNIPPET_MODELS)


class TestSnippetOrdering(TestCase):
    def setUp(self):
        register_snippet(ZuluSnippet)
        register_snippet(AlphaSnippet)

    def test_snippets_ordering(self):
        # Ensure AlphaSnippet is before ZuluSnippet
        # Cannot check first and last position as other snippets
        # may get registered elsewhere during test
        self.assertLess(SNIPPET_MODELS.index(AlphaSnippet),
                        SNIPPET_MODELS.index(ZuluSnippet))


class TestUsageCount(TestCase):
    fixtures = ['test.json']

    @override_settings(WAGTAIL_USAGE_COUNT_ENABLED=True)
    def test_snippet_usage_count(self):
        advert = Advert.objects.get(id=1)
        self.assertEqual(advert.get_usage().count(), 2)


class TestUsedBy(TestCase):
    fixtures = ['test.json']

    @override_settings(WAGTAIL_USAGE_COUNT_ENABLED=True)
    def test_snippet_used_by(self):
        advert = Advert.objects.get(id=1)
        self.assertEqual(type(advert.get_usage()[0]), Page)


class TestSnippetChoose(TestCase, WagtailTestUtils):
    fixtures = ['test.json']

    def setUp(self):
        self.login()

    def get(self, params=None):
        return self.client.get(reverse('wagtailsnippets:choose',
                                       args=('tests', 'advert')),
                               params or {})

    def test_simple(self):
        response = self.get()
        self.assertTemplateUsed(response, 'wagtailsnippets/chooser/choose.html')

    def test_simple_pagination(self):

        pages = ['0', '1', '-1', '9999', 'Not a page']
        for page in pages:
            response = self.get({'p': page})
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'wagtailsnippets/chooser/choose.html')

    def test_not_searchable(self):
        self.assertFalse(self.get().context['is_searchable'])


class TestSnippetChooseWithSearchableSnippet(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

        # Create some instances of the searchable snippet for testing
        self.snippet_a = SearchableSnippet.objects.create(text="Hello")
        self.snippet_b = SearchableSnippet.objects.create(text="World")
        self.snippet_c = SearchableSnippet.objects.create(text="Hello World")

    def get(self, params=None):
        return self.client.get(reverse('wagtailsnippets:choose',
                                       args=('snippetstests', 'searchablesnippet')),
                               params or {})

    def test_simple(self):
        response = self.get()
        self.assertTemplateUsed(response, 'wagtailsnippets/chooser/choose.html')

        # All snippets should be in items
        items = list(response.context['items'].object_list)
        self.assertIn(self.snippet_a, items)
        self.assertIn(self.snippet_b, items)
        self.assertIn(self.snippet_c, items)

    def test_is_searchable(self):
        self.assertTrue(self.get().context['is_searchable'])

    def test_search_hello(self):
        response = self.get({'q': "Hello"})

        # Just snippets with "Hello" should be in items
        items = list(response.context['items'].object_list)
        self.assertIn(self.snippet_a, items)
        self.assertNotIn(self.snippet_b, items)
        self.assertIn(self.snippet_c, items)

    def test_search_world(self):
        response = self.get({'q': "World"})

        # Just snippets with "World" should be in items
        items = list(response.context['items'].object_list)
        self.assertNotIn(self.snippet_a, items)
        self.assertIn(self.snippet_b, items)
        self.assertIn(self.snippet_c, items)


class TestSnippetChosen(TestCase, WagtailTestUtils):
    fixtures = ['test.json']

    def setUp(self):
        self.login()

    def get(self, pk, params=None):
        return self.client.get(reverse('wagtailsnippets:chosen',
                                       args=('tests', 'advert', pk)),
                               params or {})

    def test_choose_a_page(self):
        response = self.get(pk=Advert.objects.all()[0].pk)
        self.assertTemplateUsed(response, 'wagtailsnippets/chooser/chosen.js')

    def test_choose_a_non_existing_page(self):

        response = self.get(999999)
        self.assertEqual(response.status_code, 404)


class TestAddOnlyPermissions(TestCase, WagtailTestUtils):
    fixtures = ['test.json']

    def setUp(self):
        self.test_snippet = Advert.objects.get(id=1)

        # Create a user with add_advert permission but not change_advert
        user = get_user_model().objects.create_user(
            username='addonly',
            email='addonly@example.com',
            password='password'
        )
        add_permission = Permission.objects.get(content_type__app_label='tests', codename='add_advert')
        admin_permission = Permission.objects.get(content_type__app_label='wagtailadmin', codename='access_admin')
        user.user_permissions.add(add_permission, admin_permission)
        self.assertTrue(self.client.login(username='addonly', password='password'))

    def test_get_index(self):
        response = self.client.get(reverse('wagtailsnippets:list',
                                   args=('tests', 'advert')))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailsnippets/snippets/type_index.html')

        # user should get an "Add advert" button
        self.assertContains(response, "Add advert")

    def test_get_add(self):
        response = self.client.get(reverse('wagtailsnippets:add',
                                   args=('tests', 'advert')))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailsnippets/snippets/create.html')

    def test_get_edit(self):
        response = self.client.get(reverse('wagtailsnippets:edit',
                                   args=('tests', 'advert', self.test_snippet.id)))
        # permission should be denied
        self.assertRedirects(response, reverse('wagtailadmin_home'))

    def test_get_delete(self):
        response = self.client.get(reverse('wagtailsnippets:delete', args=('tests', 'advert', self.test_snippet.id, )))
        # permission should be denied
        self.assertRedirects(response, reverse('wagtailadmin_home'))


class TestEditOnlyPermissions(TestCase, WagtailTestUtils):
    fixtures = ['test.json']

    def setUp(self):
        self.test_snippet = Advert.objects.get(id=1)

        # Create a user with change_advert permission but not add_advert
        user = get_user_model().objects.create_user(
            username='changeonly',
            email='changeonly@example.com',
            password='password'
        )
        change_permission = Permission.objects.get(content_type__app_label='tests', codename='change_advert')
        admin_permission = Permission.objects.get(content_type__app_label='wagtailadmin', codename='access_admin')
        user.user_permissions.add(change_permission, admin_permission)
        self.assertTrue(self.client.login(username='changeonly', password='password'))

    def test_get_index(self):
        response = self.client.get(reverse('wagtailsnippets:list',
                                   args=('tests', 'advert')))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailsnippets/snippets/type_index.html')

        # user should not get an "Add advert" button
        self.assertNotContains(response, "Add advert")

    def test_get_add(self):
        response = self.client.get(reverse('wagtailsnippets:add',
                                   args=('tests', 'advert')))
        # permission should be denied
        self.assertRedirects(response, reverse('wagtailadmin_home'))

    def test_get_edit(self):
        response = self.client.get(reverse('wagtailsnippets:edit',
                                   args=('tests', 'advert', self.test_snippet.id)))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailsnippets/snippets/edit.html')

    def test_get_delete(self):
        response = self.client.get(reverse('wagtailsnippets:delete', args=('tests', 'advert', self.test_snippet.id, )))
        # permission should be denied
        self.assertRedirects(response, reverse('wagtailadmin_home'))


class TestDeleteOnlyPermissions(TestCase, WagtailTestUtils):
    fixtures = ['test.json']

    def setUp(self):
        self.test_snippet = Advert.objects.get(id=1)

        # Create a user with delete_advert permission
        user = get_user_model().objects.create_user(
            username='deleteonly',
            email='deleteeonly@example.com',
            password='password'
        )
        change_permission = Permission.objects.get(content_type__app_label='tests', codename='delete_advert')
        admin_permission = Permission.objects.get(content_type__app_label='wagtailadmin', codename='access_admin')
        user.user_permissions.add(change_permission, admin_permission)
        self.assertTrue(self.client.login(username='deleteonly', password='password'))

    def test_get_index(self):
        response = self.client.get(reverse('wagtailsnippets:list',
                                   args=('tests', 'advert')))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailsnippets/snippets/type_index.html')

        # user should not get an "Add advert" button
        self.assertNotContains(response, "Add advert")

    def test_get_add(self):
        response = self.client.get(reverse('wagtailsnippets:add',
                                   args=('tests', 'advert')))
        # permission should be denied
        self.assertRedirects(response, reverse('wagtailadmin_home'))

    def test_get_edit(self):
        response = self.client.get(reverse('wagtailsnippets:edit',
                                   args=('tests', 'advert', self.test_snippet.id)))
        # permission should be denied
        self.assertRedirects(response, reverse('wagtailadmin_home'))

    def test_get_delete(self):
        response = self.client.get(reverse('wagtailsnippets:delete', args=('tests', 'advert', self.test_snippet.id, )))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailsnippets/snippets/confirm_delete.html')


class TestSnippetEditHandlers(TestCase, WagtailTestUtils):
    def test_standard_edit_handler(self):
        edit_handler_class = get_snippet_edit_handler(StandardSnippet)
        form_class = edit_handler_class.get_form_class(StandardSnippet)
        self.assertTrue(issubclass(form_class, WagtailAdminModelForm))
        self.assertFalse(issubclass(form_class, FancySnippetForm))

    def test_fancy_edit_handler(self):
        edit_handler_class = get_snippet_edit_handler(FancySnippet)
        form_class = edit_handler_class.get_form_class(FancySnippet)
        self.assertTrue(issubclass(form_class, WagtailAdminModelForm))
        self.assertTrue(issubclass(form_class, FancySnippetForm))
