import json

from django.contrib.admin.utils import quote
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser, Permission
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, TestCase
from django.test.utils import override_settings
from django.urls import reverse
from taggit.models import Tag

from wagtail.admin.forms import WagtailAdminModelForm
from wagtail.core.models import Page
from wagtail.snippets.blocks import SnippetChooserBlock
from wagtail.snippets.edit_handlers import SnippetChooserPanel
from wagtail.snippets.models import SNIPPET_MODELS, register_snippet
from wagtail.snippets.views.snippets import get_snippet_edit_handler
from wagtail.tests.snippets.forms import FancySnippetForm
from wagtail.tests.snippets.models import (
    AlphaSnippet, FancySnippet, FileUploadSnippet, RegisterDecorator, RegisterFunction,
    SearchableSnippet, StandardSnippet, StandardSnippetWithCustomPrimaryKey, ZuluSnippet)
from wagtail.tests.testapp.models import (
    Advert, AdvertWithCustomPrimaryKey, AdvertWithTabbedInterface, SnippetChooserModel,
    SnippetChooserModelWithCustomPrimaryKey)
from wagtail.tests.utils import WagtailTestUtils


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

    def test_ordering(self):
        """
        Listing should be ordered by PK if no ordering has been set on the model
        """
        for i in range(10, 0, -1):
            Advert.objects.create(pk=i, text="advert %d" % i)
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['items'][0].text, "advert 1")

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


class TestModelOrdering(TestCase, WagtailTestUtils):
    def setUp(self):
        for i in range(1, 10):
            AdvertWithTabbedInterface.objects.create(text="advert %d" % i)
        AdvertWithTabbedInterface.objects.create(text="aaaadvert")
        self.login()

    def test_listing_respects_model_ordering(self):
        response = self.client.get(
            reverse('wagtailsnippets:list', args=('tests', 'advertwithtabbedinterface'))
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['items'][0].text, "aaaadvert")

    def test_chooser_respects_model_ordering(self):
        response = self.client.get(
            reverse('wagtailsnippets:choose', args=('tests', 'advertwithtabbedinterface'))
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['items'][0].text, "aaaadvert")


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
        self.assertNotContains(response, '<a href="#tab-advert" class="active">Advert</a>', html=True)
        self.assertNotContains(response, '<a href="#tab-other" class="">Other</a>', html=True)

    def test_snippet_with_tabbed_interface(self):
        response = self.client.get(reverse('wagtailsnippets:add',
                                           args=('tests', 'advertwithtabbedinterface')))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailsnippets/snippets/create.html')
        self.assertContains(response, '<ul class="tab-nav merged">')
        self.assertContains(response, '<a href="#tab-advert" class="active">Advert</a>', html=True)
        self.assertContains(response, '<a href="#tab-other" class="">Other</a>', html=True)

    def test_create_invalid(self):
        response = self.post(post_data={'foo': 'bar'})
        self.assertContains(response, "The snippet could not be created due to errors.")
        self.assertContains(response, """<p class="error-message"><span>This field is required.</span></p>""",
                            count=1, html=True)
        self.assertContains(response, "This field is required", count=1)

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
        args = (snippet._meta.app_label, snippet._meta.model_name, quote(snippet.pk))
        return self.client.get(reverse('wagtailsnippets:edit', args=args), params)

    def post(self, post_data={}):
        snippet = self.test_snippet
        args = (snippet._meta.app_label, snippet._meta.model_name, quote(snippet.pk))
        return self.client.post(reverse('wagtailsnippets:edit', args=args), post_data)

    def setUp(self):
        self.login()


class TestSnippetEditView(BaseTestSnippetEditView):
    fixtures = ['test.json']

    def setUp(self):
        super().setUp()
        self.test_snippet = Advert.objects.get(pk=1)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailsnippets/snippets/edit.html')
        self.assertNotContains(response, '<ul class="tab-nav merged">')
        self.assertNotContains(response, '<a href="#advert" class="active">Advert</a>', html=True)
        self.assertNotContains(response, '<a href="#other" class="">Other</a>', html=True)

    def test_non_existant_model(self):
        response = self.client.get(reverse('wagtailsnippets:edit', args=('tests', 'foo', quote(self.test_snippet.pk))))
        self.assertEqual(response.status_code, 404)

    def test_nonexistant_id(self):
        response = self.client.get(reverse('wagtailsnippets:edit', args=('tests', 'advert', 999999)))
        self.assertEqual(response.status_code, 404)

    def test_edit_invalid(self):
        response = self.post(post_data={'foo': 'bar'})
        self.assertContains(response, "The snippet could not be saved due to errors.")
        self.assertContains(response, """<p class="error-message"><span>This field is required.</span></p>""",
                            count=1, html=True)
        self.assertContains(response, "This field is required", count=1)

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
        super().setUp()
        self.test_snippet = AdvertWithTabbedInterface.objects.create(
            text="test_advert",
            url="http://www.example.com",
            something_else="Model with tabbed interface")

    def test_snippet_with_tabbed_interface(self):
        response = self.get()

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailsnippets/snippets/edit.html')
        self.assertContains(response, '<ul class="tab-nav merged">')
        self.assertContains(response, '<a href="#tab-advert" class="active">Advert</a>', html=True)
        self.assertContains(response, '<a href="#tab-other" class="">Other</a>', html=True)


class TestEditFileUploadSnippet(BaseTestSnippetEditView):

    def setUp(self):
        super().setUp()
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
        self.test_snippet = Advert.objects.get(pk=1)
        self.login()

    def test_delete_get(self):
        response = self.client.get(reverse('wagtailsnippets:delete', args=('tests', 'advert', quote(self.test_snippet.pk), )))
        self.assertEqual(response.status_code, 200)

    def test_delete_post(self):
        response = self.client.post(
            reverse('wagtailsnippets:delete', args=('tests', 'advert', quote(self.test_snippet.pk), ))
        )

        # Should be redirected to explorer page
        self.assertRedirects(response, reverse('wagtailsnippets:list', args=('tests', 'advert')))

        # Check that the page is gone
        self.assertEqual(Advert.objects.filter(text='test_advert').count(), 0)

    @override_settings(WAGTAIL_USAGE_COUNT_ENABLED=True)
    def test_usage_link(self):
        response = self.client.get(reverse('wagtailsnippets:delete', args=('tests', 'advert', quote(self.test_snippet.pk), )))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailsnippets/snippets/confirm_delete.html')
        self.assertContains(response, 'Used 2 times')
        self.assertContains(response, self.test_snippet.usage_url())


class TestSnippetDeleteMultipleWithOne(TestCase, WagtailTestUtils):
    # test deletion of one snippet using the delete-multiple URL
    # behaviour should mimic the TestSnippetDelete but with different URl structure
    fixtures = ['test.json']

    def setUp(self):
        self.snippet = Advert.objects.get(id=1)
        self.login()

    def test_delete_get(self):
        url = reverse('wagtailsnippets:delete-multiple', args=('tests', 'advert'))
        url += '?id=%s' % (self.snippet.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_delete_post(self):
        url = reverse('wagtailsnippets:delete-multiple', args=('tests', 'advert'))
        url += '?id=%s' % (self.snippet.id)
        response = self.client.post(url)

        # Should be redirected to explorer page
        self.assertRedirects(response, reverse('wagtailsnippets:list', args=('tests', 'advert')))

        # Check that the page is gone
        self.assertEqual(Advert.objects.filter(text='test_advert').count(), 0)


class TestSnippetDeleteMultipleWithThree(TestCase, WagtailTestUtils):
    # test deletion of three snippets using the delete-multiple URL
    fixtures = ['test.json']

    def setUp(self):
        # first advert is in the fixtures
        Advert.objects.create(text="Boreas").save()
        Advert.objects.create(text="Cloud 9").save()
        self.snippets = Advert.objects.all()
        self.login()

    def test_delete_get(self):
        # tests that the URL is available on get
        url = reverse('wagtailsnippets:delete-multiple', args=('tests', 'advert'))
        url += '?id=%s' % ('&id='.join(['%s' % snippet.id for snippet in self.snippets]))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_delete_post(self):
        # tests that the URL is available on post and deletes snippets
        url = reverse('wagtailsnippets:delete-multiple', args=('tests', 'advert'))
        url += '?id=%s' % ('&id='.join(['%s' % snippet.id for snippet in self.snippets]))
        response = self.client.post(url)

        # Should be redirected to explorer page
        self.assertRedirects(response, reverse('wagtailsnippets:list', args=('tests', 'advert')))

        # Check that the page is gone
        self.assertEqual(Advert.objects.filter(text='test_advert').count(), 0)


class TestSnippetChooserPanel(TestCase, WagtailTestUtils):
    fixtures = ['test.json']

    def setUp(self):
        self.request = RequestFactory().get('/')
        user = AnonymousUser()  # technically, Anonymous users cannot access the admin
        self.request.user = user

        model = SnippetChooserModel
        self.advert_text = 'Test advert text'
        test_snippet = model.objects.create(
            advert=Advert.objects.create(text=self.advert_text))

        self.edit_handler = get_snippet_edit_handler(model)
        self.form_class = self.edit_handler.get_form_class()
        form = self.form_class(instance=test_snippet)
        edit_handler = self.edit_handler.bind_to_instance(instance=test_snippet,
                                                          form=form,
                                                          request=self.request)

        self.snippet_chooser_panel = [
            panel for panel in edit_handler.children
            if getattr(panel, 'field_name', None) == 'advert'][0]

    def test_create_snippet_chooser_panel_class(self):
        self.assertIsInstance(self.snippet_chooser_panel, SnippetChooserPanel)

    def test_render_as_field(self):
        field_html = self.snippet_chooser_panel.render_as_field()
        self.assertIn(self.advert_text, field_html)
        self.assertIn("Choose advert", field_html)
        self.assertIn("Choose another advert", field_html)

    def test_render_as_empty_field(self):
        test_snippet = SnippetChooserModel()
        form = self.form_class(instance=test_snippet)
        edit_handler = self.edit_handler.bind_to_instance(instance=test_snippet,
                                                          form=form,
                                                          request=self.request)

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

    def test_target_model_autodetected(self):
        result = SnippetChooserPanel(
            'advert'
        ).bind_to_model(SnippetChooserModel).target_model
        self.assertEqual(result, Advert)


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
        advert = Advert.objects.get(pk=1)
        self.assertEqual(advert.get_usage().count(), 2)


class TestUsedBy(TestCase):
    fixtures = ['test.json']

    @override_settings(WAGTAIL_USAGE_COUNT_ENABLED=True)
    def test_snippet_used_by(self):
        advert = Advert.objects.get(pk=1)
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

    def test_ordering(self):
        """
        Listing should be ordered by PK if no ordering has been set on the model
        """
        Advert.objects.all().delete()
        for i in range(10, 0, -1):
            Advert.objects.create(pk=i, text="advert %d" % i)
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['items'][0].text, "advert 1")

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
        response_json = json.loads(response.content.decode())
        self.assertEqual(response_json['step'], 'chosen')

    def test_choose_a_non_existing_page(self):

        response = self.get(999999)
        self.assertEqual(response.status_code, 404)


class TestAddOnlyPermissions(TestCase, WagtailTestUtils):
    fixtures = ['test.json']

    def setUp(self):
        self.test_snippet = Advert.objects.get(pk=1)

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
                                   args=('tests', 'advert', quote(self.test_snippet.pk))))
        # permission should be denied
        self.assertRedirects(response, reverse('wagtailadmin_home'))

    def test_get_delete(self):
        response = self.client.get(reverse('wagtailsnippets:delete', args=('tests', 'advert', quote(self.test_snippet.pk), )))
        # permission should be denied
        self.assertRedirects(response, reverse('wagtailadmin_home'))

    def test_get_delete_mulitple(self):
        url = reverse('wagtailsnippets:delete-multiple', args=('tests', 'advert'))
        url += '?id=%s' % self.test_snippet.id
        response = self.client.get(url)
        # permission should be denied
        self.assertRedirects(response, reverse('wagtailadmin_home'))


class TestEditOnlyPermissions(TestCase, WagtailTestUtils):
    fixtures = ['test.json']

    def setUp(self):
        self.test_snippet = Advert.objects.get(pk=1)

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
                                   args=('tests', 'advert', quote(self.test_snippet.pk))))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailsnippets/snippets/edit.html')

    def test_get_delete(self):
        response = self.client.get(reverse('wagtailsnippets:delete', args=('tests', 'advert', quote(self.test_snippet.pk), )))
        # permission should be denied
        self.assertRedirects(response, reverse('wagtailadmin_home'))

    def test_get_delete_mulitple(self):
        url = reverse('wagtailsnippets:delete-multiple', args=('tests', 'advert'))
        url += '?id=%s' % self.test_snippet.id
        response = self.client.get(url)
        # permission should be denied
        self.assertRedirects(response, reverse('wagtailadmin_home'))


class TestDeleteOnlyPermissions(TestCase, WagtailTestUtils):
    fixtures = ['test.json']

    def setUp(self):
        self.test_snippet = Advert.objects.get(pk=1)

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
                                   args=('tests', 'advert', quote(self.test_snippet.pk))))
        # permission should be denied
        self.assertRedirects(response, reverse('wagtailadmin_home'))

    def test_get_delete(self):
        response = self.client.get(reverse('wagtailsnippets:delete', args=('tests', 'advert', quote(self.test_snippet.pk), )))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailsnippets/snippets/confirm_delete.html')

    def test_get_delete_mulitple(self):
        url = reverse('wagtailsnippets:delete-multiple', args=('tests', 'advert'))
        url += '?id=%s' % self.test_snippet.id
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailsnippets/snippets/confirm_delete.html')


class TestSnippetEditHandlers(TestCase, WagtailTestUtils):
    def test_standard_edit_handler(self):
        edit_handler = get_snippet_edit_handler(StandardSnippet)
        form_class = edit_handler.get_form_class()
        self.assertTrue(issubclass(form_class, WagtailAdminModelForm))
        self.assertFalse(issubclass(form_class, FancySnippetForm))

    def test_fancy_edit_handler(self):
        edit_handler = get_snippet_edit_handler(FancySnippet)
        form_class = edit_handler.get_form_class()
        self.assertTrue(issubclass(form_class, WagtailAdminModelForm))
        self.assertTrue(issubclass(form_class, FancySnippetForm))


class TestInlinePanelMedia(TestCase, WagtailTestUtils):
    """
    Test that form media required by InlinePanels is correctly pulled in to the edit page
    """
    def test_inline_panel_media(self):
        self.login()

        response = self.client.get(reverse('wagtailsnippets:add', args=('snippetstests', 'multisectionrichtextsnippet')))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'wagtailadmin/js/draftail.js')


class TestSnippetChooserBlock(TestCase):
    fixtures = ['test.json']

    def test_serialize(self):
        """The value of a SnippetChooserBlock (a snippet instance) should serialize to an ID"""
        block = SnippetChooserBlock(Advert)
        test_advert = Advert.objects.get(text='test_advert')

        self.assertEqual(block.get_prep_value(test_advert), test_advert.id)

        # None should serialize to None
        self.assertEqual(block.get_prep_value(None), None)

    def test_deserialize(self):
        """The serialized value of a SnippetChooserBlock (an ID) should deserialize to a snippet instance"""
        block = SnippetChooserBlock(Advert)
        test_advert = Advert.objects.get(text='test_advert')

        self.assertEqual(block.to_python(test_advert.id), test_advert)

        # None should deserialize to None
        self.assertEqual(block.to_python(None), None)

    def test_reference_model_by_string(self):
        block = SnippetChooserBlock('tests.Advert')
        test_advert = Advert.objects.get(text='test_advert')
        self.assertEqual(block.to_python(test_advert.id), test_advert)

    def test_form_render(self):
        block = SnippetChooserBlock(Advert, help_text="pick an advert, any advert")

        empty_form_html = block.render_form(None, 'advert')
        self.assertInHTML('<input id="advert" name="advert" placeholder="" type="hidden" />', empty_form_html)
        self.assertIn('createSnippetChooser("advert", "tests/advert");', empty_form_html)

        test_advert = Advert.objects.get(text='test_advert')
        test_advert_form_html = block.render_form(test_advert, 'advert')
        expected_html = '<input id="advert" name="advert" placeholder="" type="hidden" value="%d" />' % test_advert.id
        self.assertInHTML(expected_html, test_advert_form_html)
        self.assertIn("pick an advert, any advert", test_advert_form_html)

    def test_form_response(self):
        block = SnippetChooserBlock(Advert)
        test_advert = Advert.objects.get(text='test_advert')

        value = block.value_from_datadict({'advert': str(test_advert.id)}, {}, 'advert')
        self.assertEqual(value, test_advert)

        empty_value = block.value_from_datadict({'advert': ''}, {}, 'advert')
        self.assertEqual(empty_value, None)

    def test_clean(self):
        required_block = SnippetChooserBlock(Advert)
        nonrequired_block = SnippetChooserBlock(Advert, required=False)
        test_advert = Advert.objects.get(text='test_advert')

        self.assertEqual(required_block.clean(test_advert), test_advert)
        with self.assertRaises(ValidationError):
            required_block.clean(None)

        self.assertEqual(nonrequired_block.clean(test_advert), test_advert)
        self.assertEqual(nonrequired_block.clean(None), None)


class TestSnippetListViewWithCustomPrimaryKey(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

        # Create some instances of the searchable snippet for testing
        self.snippet_a = StandardSnippetWithCustomPrimaryKey.objects.create(snippet_id="snippet/01", text="Hello")
        self.snippet_b = StandardSnippetWithCustomPrimaryKey.objects.create(snippet_id="snippet/02", text="Hello")
        self.snippet_c = StandardSnippetWithCustomPrimaryKey.objects.create(snippet_id="snippet/03", text="Hello")

    def get(self, params={}):
        return self.client.get(reverse('wagtailsnippets:list',
                                       args=('snippetstests', 'standardsnippetwithcustomprimarykey')),
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


class TestSnippetViewWithCustomPrimaryKey(TestCase, WagtailTestUtils):
    fixtures = ['test.json']

    def setUp(self):
        super(TestSnippetViewWithCustomPrimaryKey, self).setUp()
        self.login()
        self.snippet_a = StandardSnippetWithCustomPrimaryKey.objects.create(snippet_id="snippet/01", text="Hello")

    def get(self, snippet, params={}):
        args = (snippet._meta.app_label, snippet._meta.model_name, quote(snippet.pk))
        return self.client.get(reverse('wagtailsnippets:edit', args=args), params)

    def post(self, snippet, post_data={}):
        args = (snippet._meta.app_label, snippet._meta.model_name, quote(snippet.pk))
        return self.client.post(reverse('wagtailsnippets:edit', args=args), post_data)

    def create(self, snippet, post_data={}, model=Advert):
        args = (snippet._meta.app_label, snippet._meta.model_name)
        return self.client.post(reverse('wagtailsnippets:add', args=args), post_data)

    def test_show_edit_view(self):
        response = self.get(self.snippet_a)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailsnippets/snippets/edit.html')

    def test_edit_invalid(self):
        response = self.post(self.snippet_a, post_data={'foo': 'bar'})
        self.assertContains(response, "The snippet could not be saved due to errors.")
        self.assertContains(response, "This field is required.")

    def test_edit(self):
        response = self.post(self.snippet_a, post_data={'text': 'Edited snippet',
                             'snippet_id': 'snippet_id_edited'})
        self.assertRedirects(response, reverse('wagtailsnippets:list', args=('snippetstests', 'standardsnippetwithcustomprimarykey')))

        snippets = StandardSnippetWithCustomPrimaryKey.objects.all()
        self.assertEqual(snippets.count(), 2)
        self.assertEqual(snippets.last().snippet_id, 'snippet_id_edited')

    def test_create(self):
        response = self.create(self.snippet_a, post_data={'text': 'test snippet',
                               'snippet_id': 'snippet/02'})
        self.assertRedirects(response, reverse('wagtailsnippets:list', args=('snippetstests', 'standardsnippetwithcustomprimarykey')))

        snippets = StandardSnippetWithCustomPrimaryKey.objects.all()
        self.assertEqual(snippets.count(), 2)
        self.assertEqual(snippets.last().text, 'test snippet')

    def test_get_delete(self):
        response = self.client.get(reverse('wagtailsnippets:delete', args=('snippetstests', 'standardsnippetwithcustomprimarykey', quote(self.snippet_a.pk), )))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailsnippets/snippets/confirm_delete.html')

    @override_settings(WAGTAIL_USAGE_COUNT_ENABLED=True)
    def test_usage_link(self):
        response = self.client.get(reverse('wagtailsnippets:delete', args=('snippetstests', 'standardsnippetwithcustomprimarykey', quote(self.snippet_a.pk), )))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailsnippets/snippets/confirm_delete.html')
        self.assertContains(response, 'Used 0 times')
        self.assertContains(response, self.snippet_a.usage_url())


class TestSnippetChooserBlockWithCustomPrimaryKey(TestCase):
    fixtures = ['test.json']

    def test_serialize(self):
        """The value of a SnippetChooserBlock (a snippet instance) should serialize to an ID"""
        block = SnippetChooserBlock(AdvertWithCustomPrimaryKey)
        test_advert = AdvertWithCustomPrimaryKey.objects.get(pk='advert/01')

        self.assertEqual(block.get_prep_value(test_advert), test_advert.pk)

        # None should serialize to None
        self.assertEqual(block.get_prep_value(None), None)

    def test_deserialize(self):
        """The serialized value of a SnippetChooserBlock (an ID) should deserialize to a snippet instance"""
        block = SnippetChooserBlock(AdvertWithCustomPrimaryKey)
        test_advert = AdvertWithCustomPrimaryKey.objects.get(pk='advert/01')

        self.assertEqual(block.to_python(test_advert.pk), test_advert)

        # None should deserialize to None
        self.assertEqual(block.to_python(None), None)

    def test_form_render(self):
        block = SnippetChooserBlock(AdvertWithCustomPrimaryKey, help_text="pick an advert, any advert")

        empty_form_html = block.render_form(None, 'advertwithcustomprimarykey')
        self.assertInHTML('<input id="advertwithcustomprimarykey" name="advertwithcustomprimarykey" placeholder="" type="hidden" />', empty_form_html)
        self.assertIn('createSnippetChooser("advertwithcustomprimarykey", "tests/advertwithcustomprimarykey");', empty_form_html)

        test_advert = AdvertWithCustomPrimaryKey.objects.get(pk='advert/01')
        test_advert_form_html = block.render_form(test_advert, 'advertwithcustomprimarykey')
        expected_html = '<input id="advertwithcustomprimarykey" name="advertwithcustomprimarykey" placeholder="" type="hidden" value="%s" />' % test_advert.pk
        self.assertInHTML(expected_html, test_advert_form_html)
        self.assertIn("pick an advert, any advert", test_advert_form_html)

    def test_form_response(self):
        block = SnippetChooserBlock(AdvertWithCustomPrimaryKey)
        test_advert = AdvertWithCustomPrimaryKey.objects.get(pk='advert/01')

        value = block.value_from_datadict({'advertwithcustomprimarykey': str(test_advert.pk)}, {}, 'advertwithcustomprimarykey')
        self.assertEqual(value, test_advert)

        empty_value = block.value_from_datadict({'advertwithcustomprimarykey': ''}, {}, 'advertwithcustomprimarykey')
        self.assertEqual(empty_value, None)

    def test_clean(self):
        required_block = SnippetChooserBlock(AdvertWithCustomPrimaryKey)
        nonrequired_block = SnippetChooserBlock(AdvertWithCustomPrimaryKey, required=False)
        test_advert = AdvertWithCustomPrimaryKey.objects.get(pk='advert/01')

        self.assertEqual(required_block.clean(test_advert), test_advert)
        with self.assertRaises(ValidationError):
            required_block.clean(None)

        self.assertEqual(nonrequired_block.clean(test_advert), test_advert)
        self.assertEqual(nonrequired_block.clean(None), None)


class TestSnippetChooserPanelWithCustomPrimaryKey(TestCase, WagtailTestUtils):
    fixtures = ['test.json']

    def setUp(self):
        self.request = RequestFactory().get('/')
        user = AnonymousUser()  # technically, Anonymous users cannot access the admin
        self.request.user = user

        model = SnippetChooserModelWithCustomPrimaryKey
        self.advert_text = 'Test advert text'
        test_snippet = model.objects.create(
            advertwithcustomprimarykey=AdvertWithCustomPrimaryKey.objects.create(
                advert_id="advert/02",
                text=self.advert_text
            )
        )

        self.edit_handler = get_snippet_edit_handler(model)
        self.form_class = self.edit_handler.get_form_class()
        form = self.form_class(instance=test_snippet)
        edit_handler = self.edit_handler.bind_to_instance(instance=test_snippet,
                                                          form=form,
                                                          request=self.request)

        self.snippet_chooser_panel = [
            panel for panel in edit_handler.children
            if getattr(panel, 'field_name', None) == 'advertwithcustomprimarykey'][0]

    def test_create_snippet_chooser_panel_class(self):
        self.assertIsInstance(self.snippet_chooser_panel, SnippetChooserPanel)

    def test_render_as_field(self):
        field_html = self.snippet_chooser_panel.render_as_field()
        self.assertIn(self.advert_text, field_html)
        self.assertIn("Choose advert with custom primary key", field_html)
        self.assertIn("Choose another advert with custom primary key", field_html)

    def test_render_as_empty_field(self):
        test_snippet = SnippetChooserModelWithCustomPrimaryKey()
        form = self.form_class(instance=test_snippet)
        edit_handler = self.edit_handler.bind_to_instance(instance=test_snippet,
                                                          form=form,
                                                          request=self.request)

        snippet_chooser_panel = [
            panel for panel in edit_handler.children
            if getattr(panel, 'field_name', None) == 'advertwithcustomprimarykey'
        ][0]

        field_html = snippet_chooser_panel.render_as_field()
        self.assertIn("Choose advert with custom primary key", field_html)
        self.assertIn("Choose another advert with custom primary key", field_html)

    def test_render_js(self):
        self.assertIn('createSnippetChooser("id_advertwithcustomprimarykey", "tests/advertwithcustomprimarykey");',
                      self.snippet_chooser_panel.render_as_field())

    def test_target_model_autodetected(self):
        result = SnippetChooserPanel(
            'advertwithcustomprimarykey'
        ).bind_to_model(SnippetChooserModelWithCustomPrimaryKey).target_model
        self.assertEqual(result, AdvertWithCustomPrimaryKey)


class TestSnippetChooseWithCustomPrimaryKey(TestCase, WagtailTestUtils):
    fixtures = ['test.json']

    def setUp(self):
        self.login()

    def get(self, params=None):
        return self.client.get(reverse('wagtailsnippets:choose',
                                       args=('tests', 'advertwithcustomprimarykey')),
                               params or {})

    def test_simple(self):
        response = self.get()
        self.assertTemplateUsed(response, 'wagtailsnippets/chooser/choose.html')

    def test_ordering(self):
        """
        Listing should be ordered by PK if no ordering has been set on the model
        """
        AdvertWithCustomPrimaryKey.objects.all().delete()
        for i in range(10, 0, -1):
            AdvertWithCustomPrimaryKey.objects.create(pk=i, text="advert %d" % i)
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['items'][0].text, "advert 1")


class TestSnippetChosenWithCustomPrimaryKey(TestCase, WagtailTestUtils):
    fixtures = ['test.json']

    def setUp(self):
        self.login()

    def get(self, pk, params=None):
        return self.client.get(reverse('wagtailsnippets:chosen',
                                       args=('tests', 'advertwithcustomprimarykey', quote(pk))),
                               params or {})

    def test_choose_a_page(self):
        response = self.get(pk=AdvertWithCustomPrimaryKey.objects.all()[0].pk)
        response_json = json.loads(response.content.decode())
        self.assertEqual(response_json['step'], 'chosen')
