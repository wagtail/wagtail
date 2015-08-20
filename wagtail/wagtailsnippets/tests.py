from django.test import TestCase
from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission

from taggit.models import Tag

from wagtail.tests.utils import WagtailTestUtils
from wagtail.tests.testapp.models import Advert, SnippetChooserModel
from wagtail.tests.snippets.models import AlphaSnippet, ZuluSnippet, RegisterDecorator, RegisterFunction
from wagtail.wagtailsnippets.models import register_snippet, SNIPPET_MODELS

from wagtail.wagtailsnippets.views.snippets import (
    get_snippet_edit_handler
)
from wagtail.wagtailcore.models import Page


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


class TestSnippetCreateView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

    def get(self, params={}):
        return self.client.get(reverse('wagtailsnippets:add',
                                       args=('tests', 'advert')),
                               params)

    def post(self, post_data={}):
        return self.client.post(reverse('wagtailsnippets:add',
                               args=('tests', 'advert')),
                               post_data)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailsnippets/snippets/create.html')

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
        self.assertEqual(
            list(snippet.tags.order_by('name')),
            list(Tag.objects.order_by('name').filter(name__in=tags)))


class TestSnippetEditView(TestCase, WagtailTestUtils):
    fixtures = ['test.json']

    def setUp(self):
        self.test_snippet = Advert.objects.get(id=1)
        self.login()

    def get(self, params={}):
        return self.client.get(reverse('wagtailsnippets:edit',
                                       args=('tests', 'advert', self.test_snippet.id)),
                               params)

    def post(self, post_data={}):
        return self.client.post(reverse('wagtailsnippets:edit',
                                        args=('tests', 'advert', self.test_snippet.id)),
                                post_data)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailsnippets/snippets/edit.html')

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
        self.assertEqual(
            list(snippet.tags.order_by('name')),
            list(Tag.objects.order_by('name').filter(name__in=tags)))


class TestSnippetDelete(TestCase, WagtailTestUtils):
    fixtures = ['test.json']

    def setUp(self):
        self.test_snippet = Advert.objects.get(id=1)
        self.login()

    def test_delete_get(self):
        response = self.client.get(reverse('wagtailsnippets:delete', args=('tests', 'advert', self.test_snippet.id, )))
        self.assertEqual(response.status_code, 200)

    def test_delete_post(self):
        post_data = {'foo': 'bar'} # For some reason, this test doesn't work without a bit of POST data
        response = self.client.post(reverse('wagtailsnippets:delete', args=('tests', 'advert', self.test_snippet.id, )), post_data)

        # Should be redirected to explorer page
        self.assertRedirects(response, reverse('wagtailsnippets:list', args=('tests', 'advert')))

        # Check that the page is gone
        self.assertEqual(Advert.objects.filter(text='test_advert').count(), 0)


class TestSnippetChooserPanel(TestCase):
    fixtures = ['test.json']

    def setUp(self):
        model = SnippetChooserModel
        self.advert_text = 'Test advert text'
        test_snippet = model.objects.create(
            advert=Advert.objects.create(text=self.advert_text))

        edit_handler_class = get_snippet_edit_handler(model)
        form_class = edit_handler_class.get_form_class(model)
        form = form_class(instance=test_snippet)
        edit_handler = edit_handler_class(instance=test_snippet, form=form)

        self.snippet_chooser_panel = [
            panel for panel in edit_handler.children
            if getattr(panel, 'field_name', None) == 'advert'][0]

    def test_create_snippet_chooser_panel_class(self):
        self.assertEqual(type(self.snippet_chooser_panel).__name__,
                         '_SnippetChooserPanel')

    def test_render_as_field(self):
        self.assertTrue(self.advert_text in self.snippet_chooser_panel.render_as_field())

    def test_render_js(self):
        self.assertIn('createSnippetChooser("id_advert", "tests/advert");',
                      self.snippet_chooser_panel.render_as_field())


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
        user = get_user_model().objects.create_user(username='addonly', email='addonly@example.com', password='password')
        add_permission = Permission.objects.get(content_type__app_label='tests', codename='add_advert')
        admin_permission = Permission.objects.get(content_type__app_label='wagtailadmin', codename='access_admin')
        user.user_permissions.add(add_permission, admin_permission)
        self.client.login(username='addonly', password='password')

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
        user = get_user_model().objects.create_user(username='changeonly', email='changeonly@example.com', password='password')
        change_permission = Permission.objects.get(content_type__app_label='tests', codename='change_advert')
        admin_permission = Permission.objects.get(content_type__app_label='wagtailadmin', codename='access_admin')
        user.user_permissions.add(change_permission, admin_permission)
        self.client.login(username='changeonly', password='password')

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
        user = get_user_model().objects.create_user(username='deleteonly', email='deleteeonly@example.com', password='password')
        change_permission = Permission.objects.get(content_type__app_label='tests', codename='delete_advert')
        admin_permission = Permission.objects.get(content_type__app_label='wagtailadmin', codename='access_admin')
        user.user_permissions.add(change_permission, admin_permission)
        self.client.login(username='deleteonly', password='password')

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
