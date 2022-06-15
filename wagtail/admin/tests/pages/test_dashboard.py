from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from wagtail.admin.views.home import RecentEditsPanel
from wagtail.models import Page
from wagtail.test.testapp.models import SimplePage
from wagtail.test.utils import WagtailTestUtils


class TestRecentEditsPanel(TestCase, WagtailTestUtils):
    def setUp(self):
        # Find root page
        self.root_page = Page.objects.get(id=2)

        # Add child page
        child_page = SimplePage(
            title="Hello world!",
            slug="hello-world",
            content="Some content here",
        )
        self.root_page.add_child(instance=child_page)
        child_page.save_revision().publish()
        self.child_page = SimplePage.objects.get(id=child_page.id)

        self.create_superuser(username="alice", password="password")
        self.create_superuser(username="bob", password="password")

    def change_something(self, title):
        post_data = {"title": title, "content": "Some content", "slug": "hello-world"}
        response = self.client.post(
            reverse("wagtailadmin_pages:edit", args=(self.child_page.id,)), post_data
        )

        # Should be redirected to edit page
        self.assertRedirects(
            response, reverse("wagtailadmin_pages:edit", args=(self.child_page.id,))
        )

        # The page should have "has_unpublished_changes" flag set
        child_page_new = SimplePage.objects.get(id=self.child_page.id)
        self.assertTrue(child_page_new.has_unpublished_changes)

    def go_to_dashboard_response(self):
        response = self.client.get(reverse("wagtailadmin_home"))
        self.assertEqual(response.status_code, 200)
        return response

    def test_your_recent_edits(self):
        # Login as Bob
        self.login(username="bob", password="password")

        # Bob hasn't edited anything yet
        response = self.client.get(reverse("wagtailadmin_home"))
        self.assertNotIn("Your most recent edits", response.content.decode("utf-8"))

        # Login as Alice
        self.client.logout()
        self.login(username="alice", password="password")

        # Alice changes something
        self.change_something("Alice's edit")

        # Edit should show up on dashboard
        response = self.go_to_dashboard_response()
        self.assertIn("Your most recent edits", response.content.decode("utf-8"))

        # Bob changes something
        self.login(username="bob", password="password")
        self.change_something("Bob's edit")

        # Edit shows up on Bobs dashboard
        response = self.go_to_dashboard_response()
        self.assertIn("Your most recent edits", response.content.decode("utf-8"))

        # Login as Alice again
        self.client.logout()
        self.login(username="alice", password="password")

        # Alice's dashboard should still list that first edit
        response = self.go_to_dashboard_response()
        self.assertIn("Your most recent edits", response.content.decode("utf-8"))

    def test_panel(self):
        """Test if the panel actually returns expected pages"""
        self.login(username="bob", password="password")
        # change a page
        self.change_something("Bob's edit")
        # set a user to 'mock' a request
        self.client.user = get_user_model().objects.get(email="bob@example.com")
        # get the panel to get the last edits
        panel = RecentEditsPanel()
        ctx = panel.get_context_data({"request": self.client})

        page = Page.objects.get(pk=self.child_page.id).specific

        # check if the revision is the revision of edited Page
        self.assertEqual(ctx["last_edits"][0][0].content_object, page)
        # check if the page in this list is the specific page of this revision
        self.assertEqual(ctx["last_edits"][0][1], page)


class TestRecentEditsQueryCount(TestCase, WagtailTestUtils):
    fixtures = ["test.json"]

    def setUp(self):
        self.bob = self.create_superuser(username="bob", password="password")

        # make a bunch of page edits (all to EventPages, so that calls to specific() don't add
        # an unpredictable number of queries)
        pages_to_edit = Page.objects.filter(id__in=[4, 5, 6, 9, 12, 13]).specific()
        for page in pages_to_edit:
            page.save_revision(user=self.bob)

    def test_panel_query_count(self):
        # fake a request object with bob as the user
        self.client.user = self.bob
        with self.assertNumQueries(4):
            # Instantiating/getting context of RecentEditsPanel should not generate N+1 queries -
            # i.e. any number less than 6 would be reasonable here
            panel = RecentEditsPanel()
            parent_context = {"request": self.client}
            panel.get_context_data(parent_context)

        # check that the panel is still actually returning results
        html = panel.render_html(parent_context)
        self.assertIn("Ameristralia Day", html)
