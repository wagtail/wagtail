from datetime import date, datetime, timedelta
from io import StringIO

from django.core import management
from django.test import TestCase
from django.urls import reverse

from wagtail.admin.admin_url_finder import AdminURLFinder
from wagtail.contrib.search_promotions.models import (
    Query,
    QueryDailyHits,
    SearchPromotion,
)
from wagtail.contrib.search_promotions.templatetags.wagtailsearchpromotions_tags import (
    get_search_promotions,
)
from wagtail.test.utils import WagtailTestUtils


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
        self.assertEqual(
            Query.get("root page").editors_picks.first().description,
            "First search pick",
        )
        self.assertEqual(
            Query.get("root page").editors_picks.last().description, "Last search pick"
        )


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


class TestSearchPromotionsIndexView(WagtailTestUtils, TestCase):
    def setUp(self):
        self.login()

    def test_simple(self):
        response = self.client.get(reverse("wagtailsearchpromotions:index"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailsearchpromotions/index.html")

    def test_search(self):
        response = self.client.get(
            reverse("wagtailsearchpromotions:index"), {"q": "Hello"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["query_string"], "Hello")

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

        response = self.client.get(reverse("wagtailsearchpromotions:index"), {"p": 2})

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailsearchpromotions/index.html")

        # Check that we got the correct page
        self.assertEqual(response.context["queries"].number, 2)

    def test_pagination_invalid(self):
        self.make_search_picks()

        response = self.client.get(
            reverse("wagtailsearchpromotions:index"), {"p": "Hello World!"}
        )

        # Check response
        self.assertEqual(response.status_code, 404)

    def test_pagination_out_of_range(self):
        self.make_search_picks()

        response = self.client.get(
            reverse("wagtailsearchpromotions:index"), {"p": 99999}
        )

        # Check response
        self.assertEqual(response.status_code, 404)

    def test_results_are_ordered_alphabetically(self):
        self.make_search_picks()
        SearchPromotion.objects.create(
            query=Query.get("aaargh snake"),
            page_id=1,
            sort_order=0,
            description="ooh, it's a snake",
        )

        response = self.client.get(reverse("wagtailsearchpromotions:index"))

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailsearchpromotions/index.html")

        # "aargh snake" should be the first result alphabetically
        self.assertEqual(response.context["queries"][0].query_string, "aaargh snake")

    def test_results_ordering(self):
        self.make_search_picks()
        url = reverse("wagtailsearchpromotions:index")
        SearchPromotion.objects.create(
            query=Query.get("zyzzyvas"),
            page_id=1,
            sort_order=0,
            description="no definition found, this is a valid scrabble word though",
        )

        SearchPromotion.objects.create(
            query=Query.get("aardwolf"),
            page_id=1,
            sort_order=22,
            description="Striped hyena of southeast Africa that feeds chiefly on insects",
        )

        popularQuery = Query.get("optimal")
        for i in range(50):
            popularQuery.add_hit()
        SearchPromotion.objects.create(
            query=popularQuery,
            page_id=1,
            sort_order=15,
            description="An oddly popular search term?",
        )

        popularQuery = Query.get("suboptimal")
        for i in range(25):
            popularQuery.add_hit()
        SearchPromotion.objects.create(
            query=popularQuery,
            page_id=1,
            sort_order=15,
            description="Not as popular",
        )

        # ordered by querystring (reversed)
        response = self.client.get(url + "?ordering=-query_string")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["queries"][0].query_string, "zyzzyvas")

        # last page, still ordered by query string (reversed)
        response = self.client.get(url + "?ordering=-query_string&p=3")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["queries"][-1].query_string, "aardwolf")

        # ordered by querystring (not reversed)
        response = self.client.get(url + "?ordering=query_string")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["queries"][0].query_string, "aardwolf")

        # ordered by sum of daily hits (reversed)
        response = self.client.get(url + "?ordering=-views")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["queries"][0].query_string, "optimal")
        self.assertEqual(response.context["queries"][1].query_string, "suboptimal")

        # ordered by sum of daily hits, last page (not reversed)
        response = self.client.get(url + "?ordering=views&p=3")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["queries"][-1].query_string, "optimal")
        self.assertEqual(response.context["queries"][-2].query_string, "suboptimal")


class TestSearchPromotionsAddView(WagtailTestUtils, TestCase):
    def setUp(self):
        self.login()

    def test_simple(self):
        response = self.client.get(reverse("wagtailsearchpromotions:add"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailsearchpromotions/add.html")

    def test_post(self):
        # Submit
        post_data = {
            "query_string": "test",
            "editors_picks-TOTAL_FORMS": 1,
            "editors_picks-INITIAL_FORMS": 0,
            "editors_picks-MAX_NUM_FORMS": 1000,
            "editors_picks-0-DELETE": "",
            "editors_picks-0-ORDER": 0,
            "editors_picks-0-page": 1,
            "editors_picks-0-description": "Hello",
        }
        response = self.client.post(reverse("wagtailsearchpromotions:add"), post_data)

        # User should be redirected back to the index
        self.assertRedirects(response, reverse("wagtailsearchpromotions:index"))

        # Check that the search pick was created
        self.assertTrue(Query.get("test").editors_picks.filter(page_id=1).exists())

    def test_post_without_recommendations(self):
        # Submit
        post_data = {
            "query_string": "test",
            "editors_picks-TOTAL_FORMS": 0,
            "editors_picks-INITIAL_FORMS": 0,
            "editors_picks-MAX_NUM_FORMS": 1000,
        }
        response = self.client.post(reverse("wagtailsearchpromotions:add"), post_data)

        # User should be given an error
        self.assertEqual(response.status_code, 200)
        self.assertFormsetError(
            response,
            "searchpicks_formset",
            None,
            None,
            "Please specify at least one recommendation for this search term.",
        )


class TestSearchPromotionsEditView(WagtailTestUtils, TestCase):
    def setUp(self):
        self.user = self.login()

        # Create an search pick to edit
        self.query = Query.get("Hello")
        self.search_pick = self.query.editors_picks.create(
            page_id=1, description="Root page"
        )
        self.search_pick_2 = self.query.editors_picks.create(
            page_id=2, description="Homepage"
        )

    def test_simple(self):
        response = self.client.get(
            reverse("wagtailsearchpromotions:edit", args=(self.query.id,))
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailsearchpromotions/edit.html")

        url_finder = AdminURLFinder(self.user)
        expected_url = "/admin/searchpicks/%d/" % self.query.id
        self.assertEqual(url_finder.get_edit_url(self.search_pick), expected_url)

    def test_post(self):
        # Submit
        post_data = {
            "query_string": "Hello",
            "editors_picks-TOTAL_FORMS": 2,
            "editors_picks-INITIAL_FORMS": 2,
            "editors_picks-MAX_NUM_FORMS": 1000,
            "editors_picks-0-id": self.search_pick.id,
            "editors_picks-0-DELETE": "",
            "editors_picks-0-ORDER": 0,
            "editors_picks-0-page": 1,
            "editors_picks-0-description": "Description has changed",  # Change
            "editors_picks-1-id": self.search_pick_2.id,
            "editors_picks-1-DELETE": "",
            "editors_picks-1-ORDER": 1,
            "editors_picks-1-page": 2,
            "editors_picks-1-description": "Homepage",
        }
        response = self.client.post(
            reverse("wagtailsearchpromotions:edit", args=(self.query.id,)), post_data
        )

        # User should be redirected back to the index
        self.assertRedirects(response, reverse("wagtailsearchpromotions:index"))

        # Check that the search pick description was edited
        self.assertEqual(
            SearchPromotion.objects.get(id=self.search_pick.id).description,
            "Description has changed",
        )

    def test_post_reorder(self):
        # Check order before reordering
        self.assertEqual(Query.get("Hello").editors_picks.all()[0], self.search_pick)
        self.assertEqual(Query.get("Hello").editors_picks.all()[1], self.search_pick_2)

        # Submit
        post_data = {
            "query_string": "Hello",
            "editors_picks-TOTAL_FORMS": 2,
            "editors_picks-INITIAL_FORMS": 2,
            "editors_picks-MAX_NUM_FORMS": 1000,
            "editors_picks-0-id": self.search_pick.id,
            "editors_picks-0-DELETE": "",
            "editors_picks-0-ORDER": 1,  # Change
            "editors_picks-0-page": 1,
            "editors_picks-0-description": "Root page",
            "editors_picks-1-id": self.search_pick_2.id,
            "editors_picks-1-DELETE": "",
            "editors_picks-1-ORDER": 0,  # Change
            "editors_picks-1-page": 2,
            "editors_picks-1-description": "Homepage",
        }
        response = self.client.post(
            reverse("wagtailsearchpromotions:edit", args=(self.query.id,)), post_data
        )

        # User should be redirected back to the index
        self.assertRedirects(response, reverse("wagtailsearchpromotions:index"))

        # Check that the ordering has been saved correctly
        self.assertEqual(
            SearchPromotion.objects.get(id=self.search_pick.id).sort_order, 1
        )
        self.assertEqual(
            SearchPromotion.objects.get(id=self.search_pick_2.id).sort_order, 0
        )

        # Check that the recommendations were reordered
        self.assertEqual(Query.get("Hello").editors_picks.all()[0], self.search_pick_2)
        self.assertEqual(Query.get("Hello").editors_picks.all()[1], self.search_pick)

    def test_post_delete_recommendation(self):
        # Submit
        post_data = {
            "query_string": "Hello",
            "editors_picks-TOTAL_FORMS": 2,
            "editors_picks-INITIAL_FORMS": 2,
            "editors_picks-MAX_NUM_FORMS": 1000,
            "editors_picks-0-id": self.search_pick.id,
            "editors_picks-0-DELETE": "",
            "editors_picks-0-ORDER": 0,
            "editors_picks-0-page": 1,
            "editors_picks-0-description": "Root page",
            "editors_picks-1-id": self.search_pick_2.id,
            "editors_picks-1-DELETE": 1,
            "editors_picks-1-ORDER": 1,
            "editors_picks-1-page": 2,
            "editors_picks-1-description": "Homepage",
        }
        response = self.client.post(
            reverse("wagtailsearchpromotions:edit", args=(self.query.id,)), post_data
        )

        # User should be redirected back to the index
        self.assertRedirects(response, reverse("wagtailsearchpromotions:index"))

        # Check that the recommendation was deleted
        self.assertFalse(
            SearchPromotion.objects.filter(id=self.search_pick_2.id).exists()
        )

        # The other recommendation should still exist
        self.assertTrue(SearchPromotion.objects.filter(id=self.search_pick.id).exists())

    def test_post_without_recommendations(self):
        # Submit
        post_data = {
            "query_string": "Hello",
            "editors_picks-TOTAL_FORMS": 2,
            "editors_picks-INITIAL_FORMS": 2,
            "editors_picks-MAX_NUM_FORMS": 1000,
            "editors_picks-0-id": self.search_pick.id,
            "editors_picks-0-DELETE": 1,
            "editors_picks-0-ORDER": 0,
            "editors_picks-0-page": 1,
            "editors_picks-0-description": "Description has changed",  # Change
            "editors_picks-1-id": self.search_pick_2.id,
            "editors_picks-1-DELETE": 1,
            "editors_picks-1-ORDER": 1,
            "editors_picks-1-page": 2,
            "editors_picks-1-description": "Homepage",
        }
        response = self.client.post(
            reverse("wagtailsearchpromotions:edit", args=(self.query.id,)), post_data
        )

        # User should be given an error
        self.assertEqual(response.status_code, 200)
        self.assertFormsetError(
            response,
            "searchpicks_formset",
            None,
            None,
            "Please specify at least one recommendation for this search term.",
        )


class TestSearchPromotionsDeleteView(WagtailTestUtils, TestCase):
    def setUp(self):
        self.login()

        # Create an search pick to delete
        self.query = Query.get("Hello")
        self.search_pick = self.query.editors_picks.create(
            page_id=1, description="Root page"
        )
        self.search_pick_2 = self.query.editors_picks.create(
            page_id=2, description="Homepage"
        )

    def test_simple(self):
        response = self.client.get(
            reverse("wagtailsearchpromotions:delete", args=(self.query.id,))
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailsearchpromotions/confirm_delete.html")

    def test_post(self):
        # Submit
        response = self.client.post(
            reverse("wagtailsearchpromotions:delete", args=(self.query.id,))
        )

        # User should be redirected back to the index
        self.assertRedirects(response, reverse("wagtailsearchpromotions:index"))

        # Check that both recommendations were deleted
        self.assertFalse(
            SearchPromotion.objects.filter(id=self.search_pick_2.id).exists()
        )

        # The other recommendation should still exist
        self.assertFalse(
            SearchPromotion.objects.filter(id=self.search_pick.id).exists()
        )


class TestGarbageCollectManagementCommand(TestCase):
    def test_garbage_collect_command(self):
        nowdt = datetime.now()
        old_hit_date = (nowdt - timedelta(days=14)).date()
        recent_hit_date = (nowdt - timedelta(days=1)).date()

        # Add 10 hits that are more than one week old. The related queries and the daily hits
        # should be deleted by the search_garbage_collect command.
        query_ids_to_be_deleted = []
        for i in range(10):
            q = Query.get(f"Hello {i}")
            q.add_hit(date=old_hit_date)
            query_ids_to_be_deleted.append(q.id)

        # Add 10 hits that are less than one week old. These ones should not be deleted.
        recent_query_ids = []
        for i in range(10):
            q = Query.get(f"World {i}")
            q.add_hit(date=recent_hit_date)
            recent_query_ids.append(q.id)

        # Add 10 queries that are promoted. These ones should not be deleted.
        promoted_query_ids = []
        for i in range(10):
            q = Query.get(f"Foo bar {i}")
            q.add_hit(date=old_hit_date)
            SearchPromotion.objects.create(
                query=q, page_id=1, sort_order=0, description="Test"
            )
            promoted_query_ids.append(q.id)

        management.call_command("searchpromotions_garbage_collect", stdout=StringIO())

        self.assertFalse(Query.objects.filter(id__in=query_ids_to_be_deleted).exists())
        self.assertFalse(
            QueryDailyHits.objects.filter(
                date=old_hit_date, query_id__in=query_ids_to_be_deleted
            ).exists()
        )

        self.assertEqual(Query.objects.filter(id__in=recent_query_ids).count(), 10)
        self.assertEqual(
            QueryDailyHits.objects.filter(
                date=recent_hit_date, query_id__in=recent_query_ids
            ).count(),
            10,
        )

        self.assertEqual(Query.objects.filter(id__in=promoted_query_ids).count(), 10)
        self.assertEqual(
            QueryDailyHits.objects.filter(
                date=recent_hit_date, query_id__in=promoted_query_ids
            ).count(),
            0,
        )


class TestCopyDailyHitsFromWagtailSearchManagementCommand(TestCase):
    def run_command(self, **options):
        output = StringIO()
        management.call_command(
            "copy_daily_hits_from_wagtailsearch", stdout=output, **options
        )
        output.seek(0)
        return output

    def test_copy(self):
        # Create some daily hits in the wagtailsearch.{Query,QueryDailyHits} models
        from wagtail.search.models import Query as WSQuery

        query = WSQuery.get("test query")
        query.add_hit(date(2021, 8, 24))
        query.add_hit(date(2021, 8, 24))
        query.add_hit(date(2021, 7, 1))

        # Check that nothing magically got inserted into the new query model
        self.assertFalse(Query.objects.exists())

        # Run the management command
        self.run_command()

        # Check that the query now exists in the new model
        new_query = Query.objects.get()
        self.assertEqual(new_query.query_string, "test query")

        # Check daily hits
        self.assertEqual(new_query.hits, 3)
