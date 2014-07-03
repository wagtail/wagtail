from django.test import TestCase
from django.core.urlresolvers import reverse

from wagtail.tests.utils import WagtailTestUtils
from wagtail.tests.models import Advert, AlphaSnippet, ZuluSnippet
from wagtail.wagtailsnippets.models import register_snippet, SNIPPET_MODELS

from wagtail.wagtailsnippets.views.snippets import (
    get_snippet_edit_handler
)
from wagtail.wagtailsnippets.edit_handlers import SnippetChooserPanel


class TestSnippetIndexView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

    def get(self, params={}):
        return self.client.get(reverse('wagtailsnippets_index'), params)

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
        return self.client.get(reverse('wagtailsnippets_list',
                                       args=('tests', 'advert')),
                               params)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailsnippets/snippets/type_index.html')

    def test_displays_add_button(self):
        self.assertContains(self.get(), "Add advert")


class TestSnippetCreateView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

    def get(self, params={}):
        return self.client.get(reverse('wagtailsnippets_create',
                                       args=('tests', 'advert')),
                               params)

    def post(self, post_data={}):
        return self.client.post(reverse('wagtailsnippets_create',
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
        self.assertRedirects(response, reverse('wagtailsnippets_list', args=('tests', 'advert')))

        snippets = Advert.objects.filter(text='test_advert')
        self.assertEqual(snippets.count(), 1)
        self.assertEqual(snippets.first().url, 'http://www.example.com/')


class TestSnippetEditView(TestCase, WagtailTestUtils):
    fixtures = ['wagtail/tests/fixtures/test.json']

    def setUp(self):
        self.test_snippet = Advert.objects.get(id=1)
        self.login()

    def get(self, params={}):
        return self.client.get(reverse('wagtailsnippets_edit',
                                       args=('tests', 'advert', self.test_snippet.id)),
                               params)

    def post(self, post_data={}):
        return self.client.post(reverse('wagtailsnippets_edit',
                                        args=('tests', 'advert', self.test_snippet.id)),
                                post_data)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailsnippets/snippets/edit.html')

    def test_non_existant_model(self):
        response = self.client.get(reverse('wagtailsnippets_edit',
                                            args=('tests', 'foo', self.test_snippet.id)))
        self.assertEqual(response.status_code, 404)

    def test_nonexistant_id(self):
        response = self.client.get(reverse('wagtailsnippets_edit',
                                            args=('tests', 'advert', 999999)))
        self.assertEqual(response.status_code, 404)

    def test_edit_invalid(self):
        response = self.post(post_data={'foo': 'bar'})
        self.assertContains(response, "The snippet could not be saved due to errors.")
        self.assertContains(response, "This field is required.")

    def test_edit(self):
        response = self.post(post_data={'text': 'edited_test_advert',
                                        'url': 'http://www.example.com/edited'})
        self.assertRedirects(response, reverse('wagtailsnippets_list', args=('tests', 'advert')))

        snippets = Advert.objects.filter(text='edited_test_advert')
        self.assertEqual(snippets.count(), 1)
        self.assertEqual(snippets.first().url, 'http://www.example.com/edited')


class TestSnippetDelete(TestCase, WagtailTestUtils):
    fixtures = ['wagtail/tests/fixtures/test.json']

    def setUp(self):
        self.test_snippet = Advert.objects.get(id=1)
        self.login()

    def test_delete_get(self):
        response = self.client.get(reverse('wagtailsnippets_delete', args=('tests', 'advert', self.test_snippet.id, )))
        self.assertEqual(response.status_code, 200)

    def test_delete_post(self):
        post_data = {'foo': 'bar'} # For some reason, this test doesn't work without a bit of POST data
        response = self.client.post(reverse('wagtailsnippets_delete', args=('tests', 'advert', self.test_snippet.id, )), post_data)

        # Should be redirected to explorer page
        self.assertRedirects(response, reverse('wagtailsnippets_list', args=('tests', 'advert')))

        # Check that the page is gone
        self.assertEqual(Advert.objects.filter(text='test_advert').count(), 0)


class TestSnippetChooserPanel(TestCase):
    fixtures = ['wagtail/tests/fixtures/test.json']

    def setUp(self):
        content_type = Advert
        test_snippet = Advert.objects.get(id=1)

        edit_handler_class = get_snippet_edit_handler(Advert)
        form_class = edit_handler_class.get_form_class(Advert)
        form = form_class(instance=test_snippet)

        self.snippet_chooser_panel_class = SnippetChooserPanel('text', content_type)
        self.snippet_chooser_panel = self.snippet_chooser_panel_class(instance=test_snippet,
                                                                      form=form)

    def test_create_snippet_chooser_panel_class(self):
        self.assertEqual(self.snippet_chooser_panel_class.__name__, '_SnippetChooserPanel')

    def test_render_as_field(self):
        self.assertTrue('test_advert' in self.snippet_chooser_panel.render_as_field())

    def test_render_js(self):
        self.assertTrue("createSnippetChooser(fixPrefix('id_text'), 'tests/advert');"
                        in self.snippet_chooser_panel.render_js())


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
