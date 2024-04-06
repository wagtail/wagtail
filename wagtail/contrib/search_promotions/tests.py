import json
from datetime import date, datetime, timedelta
from io import StringIO

from django.contrib.auth.models import Permission
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

    def test_search_pick_link_create(self):
        # Add 3 search picks in a different order to their sort_order values
        # They should be ordered by their sort order values and not their insertion order
        SearchPromotion.objects.create(
            query=Query.get("root page"),
            external_link_url="https://wagtail.org",
            sort_order=0,
            description="First search promotion",
        )

        # Check
        self.assertEqual(Query.get("root page").editors_picks.count(), 1)
        self.assertEqual(
            Query.get("root page").editors_picks.first().external_link_url,
            "https://wagtail.org",
        )

    def test_search_pick_ordering(self):
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
            external_link_url="https://wagtail.org",
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

    def test_get_most_popular(self):
        popularQuery = Query.get("popular")
        for i in range(5):
            popularQuery.add_hit()
        SearchPromotion.objects.create(
            query=Query.get("popular"),
            page_id=2,
            sort_order=0,
            description="Popular search pick",
        )
        SearchPromotion.objects.create(
            query=Query.get("uninteresting"),
            page_id=1,
            sort_order=2,
            description="Uninteresting search pick",
        )

        # Check
        self.assertEqual(Query.get_most_popular().count(), 1)
        popular_picks = Query.get("popular").editors_picks.first()
        self.assertEqual(
            popular_picks.description,
            "Popular search pick",
        )
        self.assertEqual(popular_picks.query.hits, 5)

    def test_get_most_popular_since(self):
        TODAY = date.today()
        TWO_DAYS_AGO = TODAY - timedelta(days=2)
        FIVE_DAYS_AGO = TODAY - timedelta(days=5)

        popularQuery = Query.get("popular")
        for i in range(5):
            popularQuery.add_hit(date=FIVE_DAYS_AGO)

        surpriseQuery = Query.get("surprise")
        surpriseQuery.add_hit(date=TODAY)
        surpriseQuery.add_hit(date=TWO_DAYS_AGO)
        surpriseQuery.add_hit(date=FIVE_DAYS_AGO)
        SearchPromotion.objects.create(
            query=Query.get("popular"),
            page_id=2,
            sort_order=0,
            description="Popular search pick",
        )
        SearchPromotion.objects.create(
            query=Query.get("surprise"),
            page_id=2,
            sort_order=2,
            description="Surprising search pick",
        )

        # Check
        most_popular_queries = Query.get_most_popular(date_since=TWO_DAYS_AGO)
        self.assertEqual(most_popular_queries.count(), 1)
        editors_picks = Query.get("surprise").editors_picks
        surprise_picks = editors_picks.first()
        self.assertEqual(
            surprise_picks.description,
            "Surprising search pick",
        )
        self.assertEqual(surprise_picks.query.hits, 3)


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
        self.user = self.login()

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
        self.assertContains(
            response,
            'Sorry, no promoted results match "<em>Hello</em>"',
        )

    def test_search_with_results(self):
        SearchPromotion.objects.create(
            query=Query.get("search promotion query"),
            page_id=1,
        )
        SearchPromotion.objects.create(
            query=Query.get("search promotion query"),
            external_link_url="https://wagtail.org",
        )

        response = self.client.get(
            reverse("wagtailsearchpromotions:index"), {"q": "search promotion query"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["query_string"], "search promotion query")
        self.assertContains(response, '<a href="/admin/pages/1/edit/" class="nolink">')
        self.assertContains(
            response,
            '<a href="https://wagtail.org" class="nolink" target="_blank" rel="noreferrer">',
        )

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
        self.assertEqual(response.context["page_obj"].number, 2)

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

    def test_num_queries(self):
        url = reverse("wagtailsearchpromotions:index")
        self.make_search_picks()
        # Warm up the cache
        self.client.get(url)

        # Number of queries with the current number of search picks
        with self.assertNumQueries(11):
            self.client.get(url)

        # Add more SearchPromotions and QueryDailyHits to some of the queries
        today = date.today()
        for i in range(20):
            query = Query.get("query " + str(i))
            promos = [
                SearchPromotion(
                    query=query,
                    page_id=j % 2 + 1,
                    sort_order=j,
                    description=f"Search pick {j}",
                )
                for j in range(5)
            ]
            hits = [
                QueryDailyHits(query=query, date=today - timedelta(days=j), hits=j)
                for j in range(5)
            ]
            SearchPromotion.objects.bulk_create(promos)
            QueryDailyHits.objects.bulk_create(hits)

        # Number of queries after the addition of more search picks and hits
        # should remain the same (no N+1 queries)
        with self.assertNumQueries(11):
            self.client.get(url)

    def test_results_are_ordered_alphabetically(self):
        self.make_search_picks()
        SearchPromotion.objects.create(
            query=Query.get("aaargh snake"),
            page_id=1,
            sort_order=0,
            description="ooh, it's a snake",
        )
        # Add another one to make sure it's not ordered descending by pk
        SearchPromotion.objects.create(
            query=Query.get("beloved snake"),
            page_id=1,
            sort_order=0,
            description="beloved snake goes ssSSSS",
        )

        response = self.client.get(reverse("wagtailsearchpromotions:index"))

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailsearchpromotions/index.html")

        # "aargh snake" should be the first result alphabetically
        self.assertEqual(response.context["queries"][0].query_string, "aaargh snake")
        self.assertEqual(response.context["queries"][1].query_string, "beloved snake")

    def test_multiple_searchpromotions(self):
        today = date.today()
        for i in range(10):
            Query.get("root page").add_hit(date=today - timedelta(days=i))
        SearchPromotion.objects.create(
            query=Query.get("root page"),
            page_id=1,
            sort_order=0,
            description="First search pick",
        )
        SearchPromotion.objects.create(
            query=Query.get("root page"),
            page_id=2,
            sort_order=0,
            description="Second search pick",
        )
        response = self.client.get(reverse("wagtailsearchpromotions:index"))

        self.assertContains(response, "<td>10</td>", html=True)
        self.assertEqual(Query.get("root page").hits, 10)

        soup = self.get_soup(response.content)
        root_page_edit_url = reverse("wagtailadmin_pages:edit", args=(1,))
        homepage_edit_url = reverse("wagtailadmin_pages:edit", args=(2,))
        root_page_edit_link = soup.select_one(f'a[href="{root_page_edit_url}"]')
        homepage_edit_link = soup.select_one(f'a[href="{homepage_edit_url}"]')
        self.assertIsNotNone(root_page_edit_link)
        self.assertIsNotNone(homepage_edit_link)
        self.assertEqual(Query.get("root page").editors_picks.count(), 2)

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
        self.assertEqual(response.context["page_obj"][0].query_string, "zyzzyvas")

        # last page, still ordered by query string (reversed)
        response = self.client.get(url + "?ordering=-query_string&p=3")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["page_obj"][-1].query_string, "aardwolf")

        # ordered by querystring (not reversed)
        response = self.client.get(url + "?ordering=query_string")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["page_obj"][0].query_string, "aardwolf")

        # ordered by sum of daily hits (reversed)
        response = self.client.get(url + "?ordering=-views")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["page_obj"][0].query_string, "optimal")
        self.assertEqual(response.context["page_obj"][1].query_string, "suboptimal")

        # ordered by sum of daily hits, last page (not reversed)
        response = self.client.get(url + "?ordering=views&p=3")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["page_obj"][-1].query_string, "optimal")
        self.assertEqual(response.context["page_obj"][-2].query_string, "suboptimal")

    def test_get_with_no_permission(self):
        self.user.is_superuser = False
        self.user.save()
        # Only basic access_admin permission is given
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin",
                codename="access_admin",
            )
        )

        response = self.client.get(reverse("wagtailsearchpromotions:index"))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("wagtailadmin_home"))

    def test_get_with_edit_permission_only(self):
        self.user.is_superuser = False
        self.user.save()
        # Only basic access_admin permission is given
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin",
                codename="access_admin",
            ),
            Permission.objects.get(
                content_type__app_label="wagtailsearchpromotions",
                codename="change_searchpromotion",
            ),
        )

        response = self.client.get(reverse("wagtailsearchpromotions:index"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailsearchpromotions/index.html")

        soup = self.get_soup(response.content)
        add_url = reverse("wagtailsearchpromotions:add")
        # Should not render add link
        self.assertIsNone(soup.select_one(f'a[href="{add_url}"]'))


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

    def test_post_with_external_link(self):
        # Submit
        post_data = {
            "query_string": "test",
            "editors_picks-TOTAL_FORMS": 1,
            "editors_picks-INITIAL_FORMS": 0,
            "editors_picks-MAX_NUM_FORMS": 1000,
            "editors_picks-0-DELETE": "",
            "editors_picks-0-ORDER": 0,
            "editors_picks-0-external_link_url": "https://wagtail.org",
            "editors_picks-0-external_link_text": "Wagtail",
            "editors_picks-0-description": "Hello",
        }
        response = self.client.post(reverse("wagtailsearchpromotions:add"), post_data)

        # User should be redirected back to the index
        self.assertRedirects(response, reverse("wagtailsearchpromotions:index"))

        # Check that the search pick was created
        self.assertTrue(
            Query.get("test")
            .editors_picks.filter(external_link_url="https://wagtail.org")
            .exists()
        )

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
        self.assertFormSetError(
            response.context["searchpicks_formset"],
            None,
            None,
            "Please specify at least one recommendation for this search term.",
        )

    def test_post_with_page_and_external_link(self):
        post_data = {
            "query_string": "test",
            "editors_picks-TOTAL_FORMS": 1,
            "editors_picks-INITIAL_FORMS": 0,
            "editors_picks-MAX_NUM_FORMS": 1000,
            "editors_picks-0-DELETE": "",
            "editors_picks-0-ORDER": 0,
            "editors_picks-0-page": 1,
            "editors_picks-0-external_link_url": "https://wagtail.org",
            "editors_picks-0-external_link_text": "Wagtail",
            "editors_picks-0-description": "Hello",
        }
        response = self.client.post(reverse("wagtailsearchpromotions:add"), post_data)

        # User should be given an error
        self.assertEqual(response.status_code, 200)
        self.assertFormSetError(
            response.context["searchpicks_formset"],
            None,
            None,
            "Please only select a page OR enter an external link.",
        )

    def test_post_missing_recommendation(self):
        post_data = {
            "query_string": "test",
            "editors_picks-TOTAL_FORMS": 1,
            "editors_picks-INITIAL_FORMS": 0,
            "editors_picks-MAX_NUM_FORMS": 1000,
            "editors_picks-0-DELETE": "",
            "editors_picks-0-ORDER": 0,
            "editors_picks-0-description": "Hello",
        }
        response = self.client.post(reverse("wagtailsearchpromotions:add"), post_data)

        # User should be given an error
        self.assertEqual(response.status_code, 200)
        self.assertFormSetError(
            response.context["searchpicks_formset"],
            None,
            None,
            "You must recommend a page OR an external link.",
        )

    def test_post_missing_external_text(self):
        post_data = {
            "query_string": "test",
            "editors_picks-TOTAL_FORMS": 1,
            "editors_picks-INITIAL_FORMS": 0,
            "editors_picks-MAX_NUM_FORMS": 1000,
            "editors_picks-0-DELETE": "",
            "editors_picks-0-ORDER": 0,
            "editors_picks-0-external_link_url": "https://wagtail.org",
        }
        response = self.client.post(reverse("wagtailsearchpromotions:add"), post_data)

        # User should be given an error
        self.assertEqual(response.status_code, 200)
        self.assertFormSetError(
            response.context["searchpicks_formset"],
            None,
            None,
            "You must enter an external link text if you enter an external link URL.",
        )


class TestSearchPromotionsEditView(WagtailTestUtils, TestCase):
    def setUp(self):
        self.user = self.login()

        # Create a search pick to edit
        self.query = Query.get("Hello")
        self.search_pick = self.query.editors_picks.create(
            page_id=1, sort_order=0, description="Root page"
        )
        self.search_pick_2 = self.query.editors_picks.create(
            page_id=2, sort_order=1, description="Homepage"
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
        self.assertFormSetError(
            response.context["searchpicks_formset"],
            None,
            None,
            "Please specify at least one recommendation for this search term.",
        )


class TestSearchPromotionsDeleteView(WagtailTestUtils, TestCase):
    def setUp(self):
        self.login()

        # Create a search pick to delete
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


class TestQueryChooserView(WagtailTestUtils, TestCase):
    def setUp(self):
        self.login()

    def get(self, params={}):
        return self.client.get("/admin/searchpicks/queries/chooser/", params)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "wagtailsearchpromotions/queries/chooser/chooser.html"
        )
        response_json = json.loads(response.content.decode())
        self.assertEqual(response_json["step"], "chooser")

    def test_search(self):
        response = self.get({"q": "Hello"})
        self.assertEqual(response.status_code, 200)

    def test_pagination(self):
        # page numbers in range should be accepted
        response = self.get({"p": 1})
        self.assertEqual(response.status_code, 200)
        # page numbers out of range should return 404
        response = self.get({"p": 9999})
        self.assertEqual(response.status_code, 404)


class TestHitCounter(TestCase):
    def test_no_hits(self):
        self.assertEqual(Query.get("Hello").hits, 0)

    def test_hit(self):
        # Add a hit
        Query.get("Hello").add_hit()

        # Test
        self.assertEqual(Query.get("Hello").hits, 1)

    def test_10_hits(self):
        # Add 10 hits
        for i in range(10):
            Query.get("Hello").add_hit()

        # Test
        self.assertEqual(Query.get("Hello").hits, 10)


class TestQueryStringNormalisation(TestCase):
    def setUp(self):
        self.query = Query.get("  Hello  World!  ")

    def test_normalisation(self):
        self.assertEqual(str(self.query), "hello world!")

    def test_equivalent_queries(self):
        queries = [
            "  Hello World!",
            "Hello World!  ",
            "hello  world!",
            "  Hello  world!  ",
        ]

        for query in queries:
            self.assertEqual(self.query, Query.get(query))

    def test_different_queries(self):
        queries = [
            "HelloWorld",
            "HelloWorld!" "  Hello  World!  ",
            "Hello",
        ]

        for query in queries:
            self.assertNotEqual(self.query, Query.get(query))


class TestQueryPopularity(TestCase):
    def test_query_popularity(self):
        # Add 3 hits to unpopular query
        for i in range(3):
            Query.get("unpopular query").add_hit()

        # Add 10 hits to popular query
        for i in range(10):
            Query.get("popular query").add_hit()

        # Get most popular queries
        popular_queries = Query.get_most_popular()

        # Check list
        self.assertEqual(popular_queries.count(), 2)
        self.assertEqual(popular_queries[0], Query.get("popular query"))
        self.assertEqual(popular_queries[1], Query.get("unpopular query"))

        # Add 5 hits to little popular query
        for i in range(5):
            Query.get("little popular query").add_hit()

        # Check list again, little popular query should be in the middle
        self.assertEqual(popular_queries.count(), 3)
        self.assertEqual(popular_queries[0], Query.get("popular query"))
        self.assertEqual(popular_queries[1], Query.get("little popular query"))
        self.assertEqual(popular_queries[2], Query.get("unpopular query"))

        # Unpopular query goes viral!
        for i in range(20):
            Query.get("unpopular query").add_hit()

        # Unpopular query should be most popular now
        self.assertEqual(popular_queries.count(), 3)
        self.assertEqual(popular_queries[0], Query.get("unpopular query"))
        self.assertEqual(popular_queries[1], Query.get("popular query"))
        self.assertEqual(popular_queries[2], Query.get("little popular query"))
