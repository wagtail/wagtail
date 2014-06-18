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

    def test_simple(self):
        response = self.client.get(reverse('wagtailsearch_editorspicks_index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailsearch/editorspicks/index.html')

    def test_search(self):
        response = self.client.get(reverse('wagtailsearch_editorspicks_index'), {'q': "Hello"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['query_string'], "Hello")

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

    def test_simple(self):
        response = self.client.get(reverse('wagtailsearch_editorspicks_add'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailsearch/editorspicks/add.html')

    def test_post(self):
        # Submit
        post_data = {
            'query_string': "test",
            'editors_picks-TOTAL_FORMS': 1,
            'editors_picks-INITIAL_FORMS': 0,
            'editors_picks-MAX_NUM_FORMS': 1000,
            'editors_picks-0-DELETE': '',
            'editors_picks-0-ORDER': 0,
            'editors_picks-0-page': 1,
            'editors_picks-0-description': "Hello",
        }
        response = self.client.post(reverse('wagtailsearch_editorspicks_add'), post_data)

        # User should be redirected back to the index
        self.assertRedirects(response, reverse('wagtailsearch_editorspicks_index'))

        # Check that the editors pick was created
        self.assertTrue(models.Query.get('test').editors_picks.filter(page_id=1).exists())

    def test_post_without_recommendations(self):
        # Submit
        post_data = {
            'query_string': "test",
            'editors_picks-TOTAL_FORMS': 0,
            'editors_picks-INITIAL_FORMS': 0,
            'editors_picks-MAX_NUM_FORMS': 1000,
        }
        response = self.client.post(reverse('wagtailsearch_editorspicks_add'), post_data)

        # User should be given an error
        self.assertEqual(response.status_code, 200)
        self.assertFormsetError(response, 'editors_pick_formset', None, None, "Please specify at least one recommendation for this search term.")


class TestEditorsPicksEditView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

        # Create an editors pick to edit
        self.query = models.Query.get("Hello")
        self.editors_pick = self.query.editors_picks.create(page_id=1, description="Root page")
        self.editors_pick_2 = self.query.editors_picks.create(page_id=2, description="Homepage")

    def test_simple(self):
        response = self.client.get(reverse('wagtailsearch_editorspicks_edit', args=(self.query.id, )))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailsearch/editorspicks/edit.html')

    def test_post(self):
        # Submit
        post_data = {
            'query_string': "Hello",
            'editors_picks-TOTAL_FORMS': 2,
            'editors_picks-INITIAL_FORMS': 2,
            'editors_picks-MAX_NUM_FORMS': 1000,
            'editors_picks-0-id': self.editors_pick.id,
            'editors_picks-0-DELETE': '',
            'editors_picks-0-ORDER': 0,
            'editors_picks-0-page': 1,
            'editors_picks-0-description': "Description has changed", # Change
            'editors_picks-1-id': self.editors_pick_2.id,
            'editors_picks-1-DELETE': '',
            'editors_picks-1-ORDER': 1,
            'editors_picks-1-page': 2,
            'editors_picks-1-description': "Homepage",
        }
        response = self.client.post(reverse('wagtailsearch_editorspicks_edit', args=(self.query.id, )), post_data)

        # User should be redirected back to the index
        self.assertRedirects(response, reverse('wagtailsearch_editorspicks_index'))

        # Check that the editors pick description was edited
        self.assertEqual(models.EditorsPick.objects.get(id=self.editors_pick.id).description, "Description has changed")

    def test_post_reorder(self):
        # Check order before reordering
        self.assertEqual(models.Query.get("Hello").editors_picks.all()[0], self.editors_pick)
        self.assertEqual(models.Query.get("Hello").editors_picks.all()[1], self.editors_pick_2)

        # Submit
        post_data = {
            'query_string': "Hello",
            'editors_picks-TOTAL_FORMS': 2,
            'editors_picks-INITIAL_FORMS': 2,
            'editors_picks-MAX_NUM_FORMS': 1000,
            'editors_picks-0-id': self.editors_pick.id,
            'editors_picks-0-DELETE': '',
            'editors_picks-0-ORDER': 1, # Change
            'editors_picks-0-page': 1,
            'editors_picks-0-description': "Root page",
            'editors_picks-1-id': self.editors_pick_2.id,
            'editors_picks-1-DELETE': '',
            'editors_picks-1-ORDER': 0, # Change
            'editors_picks-1-page': 2,
            'editors_picks-1-description': "Homepage",
        }
        response = self.client.post(reverse('wagtailsearch_editorspicks_edit', args=(self.query.id, )), post_data)

        # User should be redirected back to the index
        self.assertRedirects(response, reverse('wagtailsearch_editorspicks_index'))

        # Check that the recommendations were reordered
        self.assertEqual(models.Query.get("Hello").editors_picks.all()[0], self.editors_pick_2)
        self.assertEqual(models.Query.get("Hello").editors_picks.all()[1], self.editors_pick)

    def test_post_delete_recommendation(self):
        # Submit
        post_data = {
            'query_string': "Hello",
            'editors_picks-TOTAL_FORMS': 2,
            'editors_picks-INITIAL_FORMS': 2,
            'editors_picks-MAX_NUM_FORMS': 1000,
            'editors_picks-0-id': self.editors_pick.id,
            'editors_picks-0-DELETE': '',
            'editors_picks-0-ORDER': 0,
            'editors_picks-0-page': 1,
            'editors_picks-0-description': "Root page",
            'editors_picks-1-id': self.editors_pick_2.id,
            'editors_picks-1-DELETE': 1,
            'editors_picks-1-ORDER': 1,
            'editors_picks-1-page': 2,
            'editors_picks-1-description': "Homepage",
        }
        response = self.client.post(reverse('wagtailsearch_editorspicks_edit', args=(self.query.id, )), post_data)

        # User should be redirected back to the index
        self.assertRedirects(response, reverse('wagtailsearch_editorspicks_index'))

        # Check that the recommendation was deleted
        self.assertFalse(models.EditorsPick.objects.filter(id=self.editors_pick_2.id).exists())

        # The other recommendation should still exist
        self.assertTrue(models.EditorsPick.objects.filter(id=self.editors_pick.id).exists())

    def test_post_without_recommendations(self):
        # Submit
        post_data = {
            'query_string': "Hello",
            'editors_picks-TOTAL_FORMS': 2,
            'editors_picks-INITIAL_FORMS': 2,
            'editors_picks-MAX_NUM_FORMS': 1000,
            'editors_picks-0-id': self.editors_pick.id,
            'editors_picks-0-DELETE': 1,
            'editors_picks-0-ORDER': 0,
            'editors_picks-0-page': 1,
            'editors_picks-0-description': "Description has changed", # Change
            'editors_picks-1-id': self.editors_pick_2.id,
            'editors_picks-1-DELETE': 1,
            'editors_picks-1-ORDER': 1,
            'editors_picks-1-page': 2,
            'editors_picks-1-description': "Homepage",
        }
        response = self.client.post(reverse('wagtailsearch_editorspicks_edit', args=(self.query.id, )), post_data)

        # User should be given an error
        self.assertEqual(response.status_code, 200)
        self.assertFormsetError(response, 'editors_pick_formset', None, None, "Please specify at least one recommendation for this search term.")


class TestEditorsPicksDeleteView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

        # Create an editors pick to delete
        self.query = models.Query.get("Hello")
        self.editors_pick = self.query.editors_picks.create(page_id=1, description="Root page")
        self.editors_pick_2 = self.query.editors_picks.create(page_id=2, description="Homepage")

    def test_simple(self):
        response = self.client.get(reverse('wagtailsearch_editorspicks_delete', args=(self.query.id, )))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailsearch/editorspicks/confirm_delete.html')

    def test_post(self):
        # Submit
        post_data = {
            'foo': 'bar',
        }
        response = self.client.post(reverse('wagtailsearch_editorspicks_delete', args=(self.query.id, )), post_data)

        # User should be redirected back to the index
        self.assertRedirects(response, reverse('wagtailsearch_editorspicks_index'))

        # Check that both recommendations were deleted
        self.assertFalse(models.EditorsPick.objects.filter(id=self.editors_pick_2.id).exists())

        # The other recommendation should still exist
        self.assertFalse(models.EditorsPick.objects.filter(id=self.editors_pick.id).exists())
