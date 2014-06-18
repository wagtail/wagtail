from django.test import TestCase
from django.core.urlresolvers import reverse
from wagtail.tests.utils import unittest, WagtailTestUtils
from wagtail.wagtailsearch import models


class TestEditorsPicks(TestCase):
    def test_editors_pick_create(self):
        # Create an editors pick to the root page
        models.EditorsPick.objects.create(
            query=models.Query.get("root page"),
            page_id=1,
            sort_order=0,
            description="First editors pick",
        )

        # Check
        self.assertEqual(models.Query.get("root page").editors_picks.count(), 1)
        self.assertEqual(models.Query.get("root page").editors_picks.first().page_id, 1)

    def test_editors_pick_ordering(self):
        # Add 3 editors picks in a different order to their sort_order values
        # They should be ordered by their sort order values and not their insertion order
        models.EditorsPick.objects.create(
            query=models.Query.get("root page"),
            page_id=1,
            sort_order=0,
            description="First editors pick",
        )
        models.EditorsPick.objects.create(
            query=models.Query.get("root page"),
            page_id=1,
            sort_order=2,
            description="Last editors pick",
        )
        models.EditorsPick.objects.create(
            query=models.Query.get("root page"),
            page_id=1,
            sort_order=1,
            description="Middle editors pick",
        )

        # Check
        self.assertEqual(models.Query.get("root page").editors_picks.count(), 3)
        self.assertEqual(models.Query.get("root page").editors_picks.first().description, "First editors pick")
        self.assertEqual(models.Query.get("root page").editors_picks.last().description, "Last editors pick")


class TestEditorsPicksIndexView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

    def get(self, params={}):
        return self.client.get('/admin/search/editorspicks/', params)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailsearch/editorspicks/index.html')

    def test_search(self):
        response = self.get({'q': "Hello"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['query_string'], "Hello")

    def test_pagination(self):
        pages = ['0', '1', '-1', '9999', 'Not a page']
        for page in pages:
            response = self.get({'p': page})
            self.assertEqual(response.status_code, 200)

    def make_editors_picks(self):
        for i in range(50):
            models.EditorsPick.objects.create(
                query=models.Query.get("query " + str(i)),
                page_id=1,
                sort_order=0,
                description="First editors pick",
            )

    def test_pagination(self):
        self.make_editors_picks()

        response = self.client.get(reverse('wagtailsearch_editorspicks_index'), {'p': 2})

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailsearch/editorspicks/index.html')

        # Check that we got the correct page
        self.assertEqual(response.context['queries'].number, 2)

    def test_pagination_invalid(self):
        self.make_editors_picks()

        response = self.client.get(reverse('wagtailsearch_editorspicks_index'), {'p': 'Hello World!'})

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailsearch/editorspicks/index.html')

        # Check that we got page one
        self.assertEqual(response.context['queries'].number, 1)

    def test_pagination_out_of_range(self):
        self.make_editors_picks()

        response = self.client.get(reverse('wagtailsearch_editorspicks_index'), {'p': 99999})

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailsearch/editorspicks/index.html')

        # Check that we got the last page
        self.assertEqual(response.context['queries'].number, response.context['queries'].paginator.num_pages)


class TestEditorsPicksAddView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

    def get(self, params={}):
        return self.client.get('/admin/search/editorspicks/add/', params)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailsearch/editorspicks/add.html')

    # TODO: Test posting


class TestEditorsPicksEditView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

        # Create an editors pick to edit
        self.query = models.Query.get("Hello")
        self.query.editors_picks.create(page_id=1, description="Root page")

    def get(self, params={}):
        return self.client.get('/admin/search/editorspicks/' + str(self.query.id) + '/', params)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailsearch/editorspicks/edit.html')

    # TODO: Test posting


class TestEditorsPicksDeleteView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

        # Create an editors pick to delete
        self.query = models.Query.get("Hello")
        self.query.editors_picks.create(page_id=1, description="Root page")

    def get(self, params={}):
        return self.client.get('/admin/search/editorspicks/' + str(self.query.id) + '/delete/', params)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailsearch/editorspicks/confirm_delete.html')

    # TODO: Test posting
