from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time

from wagtail.admin.views.home import (
    LockedPagesPanel,
    RecentEditsPanel,
    UserObjectsInWorkflowModerationPanel,
    WorkflowObjectsToModeratePanel,
)
from wagtail.coreutils import get_dummy_request
from wagtail.models import GroupPagePermission, Page, Workflow, WorkflowContentType
from wagtail.test.testapp.models import FullFeaturedSnippet, SimplePage
from wagtail.test.utils import WagtailTestUtils
from wagtail.users.models import UserProfile


class TestRecentEditsPanel(WagtailTestUtils, TestCase):
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
        self.revision = child_page.save_revision()
        self.revision.publish()
        self.child_page = SimplePage.objects.get(id=child_page.id)

        self.user_alice = self.create_superuser(username="alice", password="password")
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

    def test_missing_page_record(self):
        # Ensure that the panel still renders when one of the page IDs returned from querying
        # PageLogEntry has no corresponding Page object. This can happen if a page is deleted,
        # because PageLogEntry records are kept on deletion.

        self.login(username="alice", password="password")
        self.change_something("Alice's edit")
        self.child_page.delete()
        response = self.client.get(reverse("wagtailadmin_home"))
        self.assertEqual(response.status_code, 200)

    def test_panel(self):
        """Test if the panel actually returns expected pages"""
        self.login(username="bob", password="password")
        # change a page

        edit_timestamp = timezone.now()
        with freeze_time(edit_timestamp):
            self.change_something("Bob's edit")

        # set a user to 'mock' a request
        self.client.user = get_user_model().objects.get(email="bob@example.com")
        # get the panel to get the last edits
        panel = RecentEditsPanel()
        ctx = panel.get_context_data({"request": self.client})

        page = Page.objects.get(pk=self.child_page.id).specific

        # check the timestamp matches the edit
        self.assertEqual(ctx["last_edits"][0][0], edit_timestamp)
        # check if the page in this list is the specific page
        self.assertEqual(ctx["last_edits"][0][1], page)

    def test_copying_does_not_count_as_an_edit(self):
        self.login(username="bob", password="password")
        # change a page
        self.change_something("Bob was ere")

        # copy the page
        post_data = {
            "new_title": "Goodbye world!",
            "new_slug": "goodbye-world",
            "new_parent_page": str(self.root_page.id),
            "copy_subpages": False,
            "alias": False,
        }
        self.client.post(
            reverse("wagtailadmin_pages:copy", args=(self.child_page.id,)), post_data
        )
        # check that page has been copied
        self.assertTrue(Page.objects.get(title="Goodbye world!"))

        response = self.client.get(reverse("wagtailadmin_home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Your most recent edits")
        self.assertContains(response, "Bob was ere")
        self.assertNotContains(response, "Goodbye world!")


class TestRecentEditsQueryCount(WagtailTestUtils, TestCase):
    fixtures = ["test.json"]

    def setUp(self):
        self.bob = self.create_superuser(username="bob", password="password")
        self.dummy_request = get_dummy_request()
        self.dummy_request.user = self.bob
        workflow = Workflow.objects.first()
        workflow_pages = {5, 6}
        locked_pages = {6, 9}
        scheduled_pages = {9, 12}
        # make a bunch of page edits (all to EventPages, so that calls to specific() don't add
        # an unpredictable number of queries)
        pages_to_edit = list(
            Page.objects.filter(id__in=[4, 5, 6, 9, 12, 13]).order_by("pk").specific()
        )
        for page in pages_to_edit:
            revision = page.save_revision(user=self.bob, log_action=True)
            if page.pk in workflow_pages:
                workflow.start(page, self.bob)
            if page.pk in locked_pages:
                page.locked = True
                page.locked_by = self.bob
                page.locked_at = timezone.now()
                page.save()
            if page.pk in scheduled_pages:
                revision.approved_go_live_at = timezone.now()
                revision.save()

    def test_panel_query_count(self):
        panel = RecentEditsPanel()
        parent_context = {"request": self.dummy_request}
        # Warm up the cache
        html = panel.render_html(parent_context)

        with self.assertNumQueries(5):
            # Rendering RecentEditsPanel should not generate N+1 queries -
            # i.e. any number less than 6 would be reasonable here
            html = panel.render_html(parent_context)
        # check that the panel is still actually returning results
        self.assertIn("Ameristralia Day", html)
        soup = self.get_soup(html)
        self.assertEqual(len(soup.select('svg use[href="#icon-lock"]')), 2)
        expected_statuses = [
            "live + draft",
            "live + scheduled",
            "live + scheduled",
            "in moderation",
            "in moderation",
        ]
        statuses = [
            "".join(e.find_all(string=True, recursive=False)).strip()
            for e in soup.select(".w-status")
        ]
        self.assertEqual(statuses, expected_statuses)


class TestLockedPagesQueryCount(WagtailTestUtils, TestCase):
    fixtures = ["test.json"]

    def setUp(self):
        self.bob = self.create_superuser(username="bob", password="password")
        self.dummy_request = get_dummy_request()
        self.dummy_request.user = self.bob

        pages = Page.objects.filter(pk__in=[9, 12, 13]).order_by("pk")
        for i, page in enumerate(pages):
            page.locked = True
            page.locked_by = self.bob
            page.locked_at = timezone.now() + timezone.timedelta(hours=i)
            page.save()

    def test_panel_query_count(self):
        panel = LockedPagesPanel()
        parent_context = {"request": self.dummy_request, "csrf_token": "dummy"}
        # Warm up the cache
        html = panel.render_html(parent_context)

        with self.assertNumQueries(7):
            html = panel.render_html(parent_context)
        soup = self.get_soup(html)
        # Should be sorted descending by locked_at
        expected_titles = [
            "Saint Patrick (single event)",
            "Steal underpants",
            "Ameristralia Day",
        ]
        titles = [e.get_text(strip=True) for e in soup.select(".title-wrapper a")]
        self.assertEqual(titles, expected_titles)


class UserObjectsInWorkflowModerationQueryCount(WagtailTestUtils, TestCase):
    fixtures = ["test.json"]

    def setUp(self):
        self.superuser = self.create_superuser(username="admin", password="password")
        self.bob = self.create_user(username="bob", password="password")
        self.someone_else = self.create_user(
            username="someoneelse", password="password"
        )
        editors = Group.objects.get(name="Editors")
        editors.user_set.add(self.bob, self.someone_else)

        workflow = Workflow.objects.first()
        WorkflowContentType.objects.create(
            workflow=workflow,
            content_type=ContentType.objects.get_for_model(FullFeaturedSnippet),
        )
        GroupPagePermission.objects.create(
            group=editors, page=Page.get_first_root_node(), permission_type="change"
        )
        editors.permissions.add(
            Permission.objects.get(codename="change_fullfeaturedsnippet")
        )

        # Pages owned by bob, but workflow started by someone else
        Page.objects.filter(id__in=[9, 12]).update(owner=self.bob)
        for page in Page.objects.filter(id__in=[9, 12]).specific():
            page.save_revision()
            workflow.start(page, self.someone_else)
            # Lock it to test the lock indicator
            page.locked = True
            page.locked_by = self.superuser
            page.locked_at = timezone.now()
            page.save()

        # Page workflow started by bob
        for page in Page.objects.filter(id__in=[4, 13]).specific():
            page.save_revision()
            workflow.start(page, self.bob)

        # Snippet workflow started by bob
        for i in range(1, 3):
            obj = FullFeaturedSnippet.objects.create(text=f"Some obj {i}")
            obj.save_revision()
            workflow.start(obj, self.bob)

        self.dummy_request = get_dummy_request()
        self.dummy_request.user = self.bob

    def test_panel_query_count(self):
        panel = UserObjectsInWorkflowModerationPanel()
        parent_context = {"request": self.dummy_request}
        # Warm up the cache
        html = panel.render_html(parent_context)

        with self.assertNumQueries(4):
            html = panel.render_html(parent_context)

        soup = self.get_soup(html)
        self.assertEqual(len(soup.select('svg use[href="#icon-lock"]')), 2)
        expected_titles = [
            "Some obj 2",
            "Some obj 1",
            "Saint Patrick (single event)",
            "Christmas",
            "Steal underpants",
            "Ameristralia Day",
        ]
        titles = [e.get_text(strip=True) for e in soup.select(".title-wrapper a")]
        self.assertEqual(titles, expected_titles)


class WorkflowObjectsToModerateQueryCount(WagtailTestUtils, TestCase):
    fixtures = ["test.json"]

    def setUp(self):
        self.superuser = self.create_superuser(username="admin", password="password")
        self.bob = self.create_user(username="bob", password="password")
        self.moderator = self.create_user(username="moderator", password="password")

        editors = Group.objects.get(name="Editors")
        moderators = Group.objects.get(name="Moderators")

        editors.user_set.add(self.bob)
        moderators.user_set.add(self.moderator)

        root = Page.get_first_root_node()
        GroupPagePermission.objects.create(
            group=editors, page=root, permission_type="change"
        )
        GroupPagePermission.objects.create(
            group=moderators, page=root, permission_type="change"
        )
        GroupPagePermission.objects.create(
            group=moderators, page=root, permission_type="publish"
        )

        editors.permissions.add(
            Permission.objects.get(codename="change_fullfeaturedsnippet")
        )
        moderators.permissions.add(
            *Permission.objects.filter(
                codename__in=[
                    "change_fullfeaturedsnippet",
                    "publish_fullfeaturedsnippet",
                ]
            ),
        )

        workflow = Workflow.objects.first()
        WorkflowContentType.objects.create(
            workflow=workflow,
            content_type=ContentType.objects.get_for_model(FullFeaturedSnippet),
        )

        # Pages workflow started by bob and locked by moderator
        for page in Page.objects.filter(id__in=[9, 12]).specific():
            page.save_revision()
            workflow.start(page, self.bob)
            # Lock it to test the lock indicator
            page.locked = True
            page.locked_by = self.moderator
            page.locked_at = timezone.now()
            page.save()

        # Page workflow started by bob
        for page in Page.objects.filter(id__in=[4, 13]).specific():
            page.save_revision()
            workflow.start(page, self.bob)

        # Snippet workflow started by bob
        for i in range(1, 3):
            obj = FullFeaturedSnippet.objects.create(text=f"Some obj {i}")
            obj.save_revision()
            workflow.start(obj, self.bob)

        self.dummy_request = get_dummy_request()
        self.dummy_request.user = self.moderator

    def test_panel_query_count(self):
        panel = WorkflowObjectsToModeratePanel()
        parent_context = {"request": self.dummy_request, "csrf_token": "dummy"}
        # Warm up the cache
        html = panel.render_html(parent_context)

        with self.assertNumQueries(13):
            html = panel.render_html(parent_context)

        soup = self.get_soup(html)
        self.assertEqual(len(soup.select('svg use[href="#icon-lock"]')), 2)
        expected_titles = [
            "Some obj 2",
            "Some obj 1",
            "Saint Patrick (single event)",
            "Christmas",
            "Steal underpants",
            "Ameristralia Day",
        ]
        titles = [e.get_text(strip=True) for e in soup.select(".title-wrapper a")]
        self.assertEqual(titles, expected_titles)


class CommonAdminBaseTemplate(WagtailTestUtils, TestCase):
    def setUp(self):
        self.user = self.login()

    def test_common_admin_base_template(self):
        response = self.client.get(reverse("wagtailadmin_home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/skeleton.html")
        self.assertTemplateUsed(response, "wagtailadmin/admin_base.html")

    def test_meta_color_scheme(self):
        profile = UserProfile.get_for_user(self.user)
        profile.theme = "dark"
        profile.save()

        response = self.client.get(reverse("wagtailadmin_home"))
        self.assertEqual(response.status_code, 200)
        soup = self.get_soup(response.content)
        meta_tag = soup.find("meta", attrs={"name": "color-scheme"})

        self.assertIsNotNone(meta_tag)
        self.assertEqual(meta_tag["content"], "dark")
