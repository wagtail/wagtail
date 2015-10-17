from django.test import TestCase
from django.core.urlresolvers import reverse

from wagtail.tests.utils import WagtailTestUtils
from wagtail.wagtailsearch.models import Query
from wagtail.contrib.wagtailsearchpromotions.models import SearchPromotion
from wagtail.contrib.wagtailsearchpromotions.templatetags.wagtailsearchpromotions_tags import get_search_promotions


class TestSearchPromotions(TestCase):
    def test_search_pick_create(self):
        # Create a search pick to the root page
        SearchPromotion.objects.create(
            query=Query.get("root page"),
            page_id=1,
            sort_order=0,
            description="First search promotion",
        )

        # Check
        self.assertEqual(Query.get("root page").editors_picks.count(), 1)
        self.assertEqual(Query.get("root page").editors_picks.first().page_id, 1)

    def test_search_pick_ordering(self):
        # Add 3 search picks in a different order to their sort_order values
        # They should be ordered by their sort order values and not their insertion order
        SearchPromotion.objects.create(
            query=Query.get("root page"),
            page_id=1,
            sort_order=0,
            description="First search pick",
        )
        SearchPromotion.objects.create(
            query=Query.get("root page"),
            page_id=1,
            sort_order=2,
            description="Last search pick",
        )
        SearchPromotion.objects.create(
            query=Query.get("root page"),
            page_id=1,
            sort_order=1,
            description="Middle search pick",
        )

        # Check
        self.assertEqual(Query.get("root page").editors_picks.count(), 3)
        self.assertEqual(Query.get("root page").editors_picks.first().description, "First search pick")
        self.assertEqual(Query.get("root page").editors_picks.last().description, "Last search pick")


class TestGetSearchPromotionsTemplateTag(TestCase):
    def test_get_search_promotions_template_tag(self):
        # Create a search pick to the root page
        pick = SearchPromotion.objects.create(
            query=Query.get("root page"),
            page_id=1,
            sort_order=0,
            description="First search pick",
        )

        # Create another search pick against a different query
        SearchPromotion.objects.create(
            query=Query.get("root page again"),
            page_id=1,
            sort_order=0,
            description="Second search pick",
        )

        # Check
        search_picks = list(get_search_promotions("root page"))
        self.assertEqual(search_picks, [pick])

    def test_get_search_promotions_with_none_query_string(self):
        search_picks = list(get_search_promotions(None))
        self.assertEqual(search_picks, [])


class TestSearchPromotionsIndexView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

    def test_simple(self):
        response = self.client.get(reverse('wagtailsearchpromotions:index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailsearchpromotions/index.html')

    def test_search(self):
        response = self.client.get(reverse('wagtailsearchpromotions:index'), {'q': "Hello"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['query_string'], "Hello")

    def make_search_picks(self):
        for i in range(50):
            SearchPromotion.objects.create(
                query=Query.get("query " + str(i)),
                page_id=1,
                sort_order=0,
                description="First search pick",
            )

    def test_pagination(self):
        self.make_search_picks()

        response = self.client.get(reverse('wagtailsearchpromotions:index'), {'p': 2})

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailsearchpromotions/index.html')

        # Check that we got the correct page
        self.assertEqual(response.context['queries'].number, 2)

    def test_pagination_invalid(self):
        self.make_search_picks()

        response = self.client.get(reverse('wagtailsearchpromotions:index'), {'p': 'Hello World!'})

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailsearchpromotions/index.html')

        # Check that we got page one
        self.assertEqual(response.context['queries'].number, 1)

    def test_pagination_out_of_range(self):
        self.make_search_picks()

        response = self.client.get(reverse('wagtailsearchpromotions:index'), {'p': 99999})

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailsearchpromotions/index.html')

        # Check that we got the last page
        self.assertEqual(response.context['queries'].number, response.context['queries'].paginator.num_pages)


class TestSearchPromotionsAddView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

    def test_simple(self):
        response = self.client.get(reverse('wagtailsearchpromotions:add'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailsearchpromotions/add.html')

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
        response = self.client.post(reverse('wagtailsearchpromotions:add'), post_data)

        # User should be redirected back to the index
        self.assertRedirects(response, reverse('wagtailsearchpromotions:index'))

        # Check that the search pick was created
        self.assertTrue(Query.get('test').editors_picks.filter(page_id=1).exists())

    def test_post_without_recommendations(self):
        # Submit
        post_data = {
            'query_string': "test",
            'editors_picks-TOTAL_FORMS': 0,
            'editors_picks-INITIAL_FORMS': 0,
            'editors_picks-MAX_NUM_FORMS': 1000,
        }
        response = self.client.post(reverse('wagtailsearchpromotions:add'), post_data)

        # User should be given an error
        self.assertEqual(response.status_code, 200)
        self.assertFormsetError(
            response, 'searchpicks_formset', None, None,
            "Please specify at least one recommendation for this search term."
        )


class TestSearchPromotionsEditView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

        # Create an search pick to edit
        self.query = Query.get("Hello")
        self.search_pick = self.query.editors_picks.create(page_id=1, description="Root page")
        self.search_pick_2 = self.query.editors_picks.create(page_id=2, description="Homepage")

    def test_simple(self):
        response = self.client.get(reverse('wagtailsearchpromotions:edit', args=(self.query.id, )))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailsearchpromotions/edit.html')

    def test_post(self):
        # Submit
        post_data = {
            'query_string': "Hello",
            'editors_picks-TOTAL_FORMS': 2,
            'editors_picks-INITIAL_FORMS': 2,
            'editors_picks-MAX_NUM_FORMS': 1000,
            'editors_picks-0-id': self.search_pick.id,
            'editors_picks-0-DELETE': '',
            'editors_picks-0-ORDER': 0,
            'editors_picks-0-page': 1,
            'editors_picks-0-description': "Description has changed",  # Change
            'editors_picks-1-id': self.search_pick_2.id,
            'editors_picks-1-DELETE': '',
            'editors_picks-1-ORDER': 1,
            'editors_picks-1-page': 2,
            'editors_picks-1-description': "Homepage",
        }
        response = self.client.post(reverse('wagtailsearchpromotions:edit', args=(self.query.id, )), post_data)

        # User should be redirected back to the index
        self.assertRedirects(response, reverse('wagtailsearchpromotions:index'))

        # Check that the search pick description was edited
        self.assertEqual(SearchPromotion.objects.get(id=self.search_pick.id).description, "Description has changed")

    def test_post_reorder(self):
        # Check order before reordering
        self.assertEqual(Query.get("Hello").editors_picks.all()[0], self.search_pick)
        self.assertEqual(Query.get("Hello").editors_picks.all()[1], self.search_pick_2)

        # Submit
        post_data = {
            'query_string': "Hello",
            'editors_picks-TOTAL_FORMS': 2,
            'editors_picks-INITIAL_FORMS': 2,
            'editors_picks-MAX_NUM_FORMS': 1000,
            'editors_picks-0-id': self.search_pick.id,
            'editors_picks-0-DELETE': '',
            'editors_picks-0-ORDER': 1,  # Change
            'editors_picks-0-page': 1,
            'editors_picks-0-description': "Root page",
            'editors_picks-1-id': self.search_pick_2.id,
            'editors_picks-1-DELETE': '',
            'editors_picks-1-ORDER': 0,  # Change
            'editors_picks-1-page': 2,
            'editors_picks-1-description': "Homepage",
        }
        response = self.client.post(reverse('wagtailsearchpromotions:edit', args=(self.query.id, )), post_data)

        # User should be redirected back to the index
        self.assertRedirects(response, reverse('wagtailsearchpromotions:index'))

        # Check that the ordering has been saved correctly
        self.assertEqual(SearchPromotion.objects.get(id=self.search_pick.id).sort_order, 1)
        self.assertEqual(SearchPromotion.objects.get(id=self.search_pick_2.id).sort_order, 0)

        # Check that the recommendations were reordered
        self.assertEqual(Query.get("Hello").editors_picks.all()[0], self.search_pick_2)
        self.assertEqual(Query.get("Hello").editors_picks.all()[1], self.search_pick)

    def test_post_delete_recommendation(self):
        # Submit
        post_data = {
            'query_string': "Hello",
            'editors_picks-TOTAL_FORMS': 2,
            'editors_picks-INITIAL_FORMS': 2,
            'editors_picks-MAX_NUM_FORMS': 1000,
            'editors_picks-0-id': self.search_pick.id,
            'editors_picks-0-DELETE': '',
            'editors_picks-0-ORDER': 0,
            'editors_picks-0-page': 1,
            'editors_picks-0-description': "Root page",
            'editors_picks-1-id': self.search_pick_2.id,
            'editors_picks-1-DELETE': 1,
            'editors_picks-1-ORDER': 1,
            'editors_picks-1-page': 2,
            'editors_picks-1-description': "Homepage",
        }
        response = self.client.post(reverse('wagtailsearchpromotions:edit', args=(self.query.id, )), post_data)

        # User should be redirected back to the index
        self.assertRedirects(response, reverse('wagtailsearchpromotions:index'))

        # Check that the recommendation was deleted
        self.assertFalse(SearchPromotion.objects.filter(id=self.search_pick_2.id).exists())

        # The other recommendation should still exist
        self.assertTrue(SearchPromotion.objects.filter(id=self.search_pick.id).exists())

    def test_post_without_recommendations(self):
        # Submit
        post_data = {
            'query_string': "Hello",
            'editors_picks-TOTAL_FORMS': 2,
            'editors_picks-INITIAL_FORMS': 2,
            'editors_picks-MAX_NUM_FORMS': 1000,
            'editors_picks-0-id': self.search_pick.id,
            'editors_picks-0-DELETE': 1,
            'editors_picks-0-ORDER': 0,
            'editors_picks-0-page': 1,
            'editors_picks-0-description': "Description has changed",  # Change
            'editors_picks-1-id': self.search_pick_2.id,
            'editors_picks-1-DELETE': 1,
            'editors_picks-1-ORDER': 1,
            'editors_picks-1-page': 2,
            'editors_picks-1-description': "Homepage",
        }
        response = self.client.post(reverse('wagtailsearchpromotions:edit', args=(self.query.id, )), post_data)

        # User should be given an error
        self.assertEqual(response.status_code, 200)
        self.assertFormsetError(
            response, 'searchpicks_formset', None, None,
            "Please specify at least one recommendation for this search term."
        )


class TestSearchPromotionsDeleteView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

        # Create an search pick to delete
        self.query = Query.get("Hello")
        self.search_pick = self.query.editors_picks.create(page_id=1, description="Root page")
        self.search_pick_2 = self.query.editors_picks.create(page_id=2, description="Homepage")

    def test_simple(self):
        response = self.client.get(reverse('wagtailsearchpromotions:delete', args=(self.query.id, )))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailsearchpromotions/confirm_delete.html')

    def test_post(self):
        # Submit
        post_data = {
            'foo': 'bar',
        }
        response = self.client.post(reverse('wagtailsearchpromotions:delete', args=(self.query.id, )), post_data)

        # User should be redirected back to the index
        self.assertRedirects(response, reverse('wagtailsearchpromotions:index'))

        # Check that both recommendations were deleted
        self.assertFalse(SearchPromotion.objects.filter(id=self.search_pick_2.id).exists())

        # The other recommendation should still exist
        self.assertFalse(SearchPromotion.objects.filter(id=self.search_pick.id).exists())
