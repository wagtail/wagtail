from datetime import timedelta
from http import HTTPStatus
from io import StringIO

from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time

from wagtail.log_actions import LogContext, log
from wagtail.models import GroupPagePermission, Page, PageLogEntry, PageViewRestriction
from wagtail.test.testapp.models import SimplePage
from wagtail.test.utils import WagtailTestUtils
from wagtail.test.utils.template_tests import AdminTemplateTestUtils
from wagtail.utils.timestamps import render_timestamp


class TestAuditLogAdmin(AdminTemplateTestUtils, WagtailTestUtils, TestCase):
    base_breadcrumb_items = []

    def setUp(self):
        self.root_page = Page.objects.get(id=2)

        self.hello_page = SimplePage(
            title="Hello world!",
            slug="hello-world",
            content="hello",
            live=False,
        )
        self.root_page.add_child(instance=self.hello_page)

        self.about_page = SimplePage(title="About", slug="about", content="hello")
        self.root_page.add_child(instance=self.about_page)

        self.administrator = self.create_superuser(
            username="administrator",
            email="administrator@email.com",
            password="password",
        )
        self.editor = self.create_user(
            username="the_editor", email="the_editor@example.com", password="password"
        )
        sub_editors = Group.objects.create(name="Sub editors")
        sub_editors.permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            )
        )
        self.editor.groups.add(sub_editors)

        for permission_type in ["add", "change", "publish"]:
            GroupPagePermission.objects.create(
                group=sub_editors, page=self.hello_page, permission_type=permission_type
            )

    def _update_page(self, page):
        # save revision
        page.save_revision(user=self.editor, log_action=True)
        # schedule for publishing
        page.go_live_at = timezone.now() + timedelta(seconds=1)
        revision = page.save_revision(user=self.editor, log_action=True)
        revision.publish(user=self.editor)

        # publish
        with freeze_time(timezone.now() + timedelta(seconds=2)):
            revision.publish(user=self.editor)

            # lock/unlock
            page.save(user=self.editor, log_action="wagtail.lock")
            page.save(user=self.editor, log_action="wagtail.unlock")

            # change privacy
            restriction = PageViewRestriction(
                page=page, restriction_type=PageViewRestriction.LOGIN
            )
            restriction.save(user=self.editor)
            restriction.restriction_type = PageViewRestriction.PASSWORD
            restriction.save(user=self.administrator)
            restriction.delete()

    def test_simple(self):
        history_url = reverse(
            "wagtailadmin_pages:history", kwargs={"page_id": self.hello_page.id}
        )

        self.login(user=self.administrator)

        response = self.client.get(history_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/pages/history.html")
        self.assertTemplateUsed(response, "wagtailadmin/generic/listing.html")

        items = [
            {
                "url": reverse("wagtailadmin_explore_root"),
                "label": "Root",
            },
            {
                "url": reverse("wagtailadmin_explore", args=(self.root_page.id,)),
                "label": "Welcome to your new Wagtail site!",
            },
            {
                "url": reverse("wagtailadmin_explore", args=(self.hello_page.id,)),
                "label": "Hello world! (simple page)",
            },
            {
                "url": "",
                "label": "History",
                "sublabel": "Hello world! (simple page)",
            },
        ]
        self.assertBreadcrumbsItemsRendered(items, response.content)

    def test_page_history(self):
        self._update_page(self.hello_page)

        history_url = reverse(
            "wagtailadmin_pages:history", kwargs={"page_id": self.hello_page.id}
        )

        self.login(user=self.editor)

        response = self.client.get(history_url)
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, "Created", 1)
        self.assertContains(response, "Draft saved", 2)
        self.assertContains(response, "Locked", 1)
        self.assertContains(response, "Unlocked", 1)
        self.assertContains(response, "Page scheduled for publishing", 1)
        self.assertContains(response, "Published", 1)

        self.assertContains(
            response,
            "Added the &#x27;Private, accessible to any logged-in users&#x27; view restriction",
        )
        self.assertContains(
            response,
            "Updated the view restriction to &#x27;Private, accessible with a shared password&#x27;",
        )
        self.assertContains(
            response,
            "Removed the &#x27;Private, accessible with a shared password&#x27; view restriction",
        )

        self.assertContains(
            response, "system", 4
        )  # create without a user + remove restriction + 2 from unrelated admin color theme
        self.assertContains(
            response, "the_editor", 9
        )  # 7 entries by editor + 1 in sidebar menu + 1 in filter
        self.assertContains(
            response, "administrator", 2
        )  # the final restriction change + filter

    def test_history_group_by_uuid_and_action(self):
        # Simulate some edit log entries without UUID
        for _ in range(3):
            self.hello_page.save_revision(user=self.editor, log_action=True)

        with LogContext(user=self.editor) as context_1:
            # Simulate new revisions but share the same log context UUID
            for _ in range(3):
                self.hello_page.save_revision(
                    user=self.editor,
                    log_action=True,
                )
            # Simulate a different action with the same log context UUID
            log(instance=self.hello_page, action="wagtail.publish", user=self.editor)

        # Create a new revision with a new isolated context
        with LogContext(user=self.editor) as context_2:
            revision = self.hello_page.save_revision(
                user=self.editor,
                log_action=True,
            )

        loop_contexts = []
        for _ in range(3):
            # Create a new log context for each iteration to simulate multiple
            # request-response cycles
            with LogContext(user=self.editor) as loop_context:
                loop_contexts.append(loop_context)
                # Overwriting a revision should create log entries using the last
                # UUID for the given revision instead of the current context's UUID.
                self.hello_page.save_revision(
                    overwrite_revision=revision,
                    user=self.editor,
                    log_action=True,
                )

                # Simulate a different action logged a couple times, which should
                # use the new log context UUID
                for _ in range(2):
                    log(
                        instance=self.hello_page,
                        action="wagtail.reorder",
                        user=self.editor,
                        revision=revision,
                    )

        edit_logs = PageLogEntry.objects.for_instance(self.hello_page).filter(
            action="wagtail.edit"
        )
        self.assertEqual(edit_logs.count(), 10)
        uuids = edit_logs.filter(uuid__isnull=False).values_list("uuid", flat=True)
        self.assertEqual(len(set(uuids)), 2)

        actions = (
            PageLogEntry.objects.for_instance(self.hello_page)
            .order_by("timestamp")
            .values_list("action", "uuid")
        )
        self.assertEqual(
            list(actions),
            # Initial creation
            [("wagtail.create", None)]
            # 3 edits without UUID
            + 3 * [("wagtail.edit", None)]
            # A new log context, in which we create 3 edits with new revisions
            # and a publish action. All share the same UUID from the context.
            # The edits will be grouped together when shown, and the publish
            # action should be shown separately.
            + 3 * [("wagtail.edit", context_1.uuid)]
            + [("wagtail.publish", context_1.uuid)]
            # A new log context, in which we create 1 edit with a new revision.
            + [("wagtail.edit", context_2.uuid)]
            # Each of the following 3 iterations create its own log context.
            + [
                item
                for sublist in [
                    [
                        # However, the edit action overwrites a previous revision,
                        # so it should use the last UUID for that
                        # user+revision+action combo instead of the current context.
                        ("wagtail.edit", context_2.uuid),
                        # While other actions should use the current context's UUID
                        # as normal.
                        ("wagtail.reorder", loop_contexts[i].uuid),
                        ("wagtail.reorder", loop_contexts[i].uuid),
                    ]
                    for i in range(3)
                ]
                for item in sublist
            ],
        )

        self.login(user=self.editor)
        history_url = reverse(
            "wagtailadmin_pages:history",
            kwargs={"page_id": self.hello_page.id},
        )
        response = self.client.get(history_url)
        self.assertEqual(response.status_code, 200)
        soup = self.get_soup(response.content)
        actions = soup.select("main td:first-of-type")
        # Remove dropdowns to reduce noise when making assertions
        for dropdown in soup.select("main td [data-controller='w-dropdown']"):
            dropdown.extract()
        self.assertEqual(
            [action.get_text(strip=True, separator=" | ") for action in actions],
            [
                # Two reorder actions grouped as one, iteration 3
                "Reordered",
                # The edit with the same revision and user must share the same
                # UUID (even when using a different log context), and the last
                # edit happened here.
                "Draft saved | Current draft",
                # Two reorder actions grouped as one, iteration 2
                "Reordered",
                # Two reorder actions grouped as one, iteration 1
                "Reordered",
                # Published action in the same log context as below
                "Published | Live version",
                # 3 edits with new revisions but all created within the first
                # log context, so should be grouped as one
                "Draft saved",
                # 3 edits without UUID, each shown separately
                "Draft saved",
                "Draft saved",
                "Draft saved",
                # Initial creation
                "Created",
            ],
        )

    def test_page_history_filters(self):
        self.login(user=self.editor)
        self._update_page(self.hello_page)

        history_url = reverse(
            "wagtailadmin_pages:history", kwargs={"page_id": self.hello_page.id}
        )

        # Should allow filtering by multiple actions
        response = self.client.get(
            f"{history_url}?action=wagtail.edit&action=wagtail.lock"
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Draft saved", count=2)
        self.assertContains(response, "Locked")
        self.assertNotContains(response, "Unlocked")
        self.assertNotContains(response, "Page scheduled for publishing")
        self.assertNotContains(response, "Published")

        # Should render the active filter pills separately for each action
        soup = self.get_soup(response.content)
        active_filters = soup.select('[data-w-active-filter-id="id_action"]')
        self.assertCountEqual(
            [filter.get_text(separator=" ", strip=True) for filter in active_filters],
            ["Action: Edit", "Action: Lock"],
        )

    def test_is_commenting_action_filters(self):
        self.login(user=self.editor)
        self._update_page(self.hello_page)

        history_url = reverse(
            "wagtailadmin_pages:history", kwargs={"page_id": self.hello_page.id}
        )

        log(
            instance=self.hello_page,
            action="wagtail.comments.create",
            user=self.editor,
            revision=self.hello_page.latest_revision,
            data={
                "comment": {
                    "id": 123,
                    "contentpath": "content",
                    "text": "A comment that was added",
                }
            },
        )

        log(
            instance=self.hello_page,
            action="wagtail.comments.edit",
            user=self.editor,
            revision=self.hello_page.latest_revision,
            data={
                "comment": {
                    "id": 123,
                    "contentpath": "content",
                    "text": "A comment that was edited",
                }
            },
        )

        # Without the filter applied
        response = self.client.get(history_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Draft saved", count=2)
        self.assertContains(response, "Locked")
        self.assertContains(response, "Unlocked")
        self.assertContains(response, "Page scheduled for publishing")
        self.assertContains(response, "Published")

        # Filter to only commenting actions
        response = self.client.get(history_url + "?is_commenting_action=true")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "A comment that was added")
        self.assertContains(response, "A comment that was edited")
        self.assertNotContains(response, "Draft saved")
        self.assertNotContains(response, "Locked")
        self.assertNotContains(response, "Unlocked")
        self.assertNotContains(response, "Page scheduled for publishing")
        self.assertNotContains(response, "Published")

        # Filter to only non-commenting actions
        response = self.client.get(history_url + "?is_commenting_action=false")
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "A comment that was added")
        self.assertNotContains(response, "A comment that was edited")
        self.assertContains(response, "Draft saved")
        self.assertContains(response, "Locked")
        self.assertContains(response, "Unlocked")
        self.assertContains(response, "Page scheduled for publishing")
        self.assertContains(response, "Published")

    def test_site_history(self):
        self._update_page(self.hello_page)
        self.about_page.save_revision(user=self.administrator, log_action=True)
        self.about_page.delete(user=self.administrator)

        site_history_url = reverse("wagtailadmin_reports:site_history")

        # the editor has access to the root page, so should see everything
        self.login(user=self.editor)

        response = self.client.get(site_history_url)
        self.assertEqual(response.status_code, 200)

        self.assertNotContains(response, "About")
        self.assertContains(response, "Draft saved", 2)
        self.assertNotContains(response, "Deleted")

        # once a page is deleted, its log entries are only visible to super admins or users with
        # permissions on the root page
        self.hello_page.delete(user=self.administrator)
        response = self.client.get(site_history_url)
        self.assertContains(response, "No log entries found")

        # add the editor user to the Editors group which has permissions on the root page
        self.editor.groups.add(Group.objects.get(name="Editors"))
        response = self.client.get(site_history_url)

        self.assertContains(response, "About", 3)  # create, save draft, delete
        self.assertContains(response, "Created", 2)
        self.assertContains(response, "Deleted", 2)

        # check with super admin
        self.login(user=self.administrator)
        response = self.client.get(site_history_url)

        self.assertContains(response, "About", 3)  # create, save draft, delete
        self.assertContains(response, "Deleted", 2)

    def test_history_with_deleted_user(self):
        self._update_page(self.hello_page)

        expected_deleted_string = f"user {self.editor.pk} (deleted)"
        self.editor.delete()

        self.login(user=self.administrator)

        # check page history
        response = self.client.get(
            reverse(
                "wagtailadmin_pages:history", kwargs={"page_id": self.hello_page.id}
            )
        )
        self.assertContains(response, expected_deleted_string)

        # check site history
        response = self.client.get(reverse("wagtailadmin_reports:site_history"))
        self.assertContains(response, expected_deleted_string)

    def test_page_history_after_revision_purge(self):
        self._update_page(self.hello_page)
        call_command("purge_revisions", days=0, stdout=StringIO())

        history_url = reverse(
            "wagtailadmin_pages:history", kwargs={"page_id": self.hello_page.id}
        )

        self.login(user=self.editor)

        response = self.client.get(history_url)
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, "Created", 1)
        self.assertContains(response, "Draft saved", 2)
        self.assertContains(response, "Locked", 1)
        self.assertContains(response, "Unlocked", 1)
        self.assertContains(response, "Page scheduled for publishing", 1)
        self.assertContains(response, "Published", 1)

    def test_edit_form_has_history_link(self):
        self.hello_page.save_revision()
        self.login(user=self.editor)
        response = self.client.get(
            reverse("wagtailadmin_pages:edit", args=[self.hello_page.id])
        )
        self.assertEqual(response.status_code, 200)
        history_url = reverse("wagtailadmin_pages:history", args=[self.hello_page.id])
        self.assertContains(response, history_url)

    def test_create_and_publish_logs_revision_save(self):
        self.login(user=self.administrator)
        post_data = {
            "title": "New page!",
            "content": "Some content",
            "slug": "hello-world-redux",
            "action-publish": "action-publish",
        }
        response = self.client.post(
            reverse(
                "wagtailadmin_pages:add",
                args=("tests", "simplepage", self.root_page.id),
            ),
            post_data,
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

        page_id = Page.objects.get(
            path__startswith=self.root_page.path, slug="hello-world-redux"
        ).id

        self.assertListEqual(
            list(
                PageLogEntry.objects.filter(page=page_id)
                .values_list("action", flat=True)
                .order_by("action")
            ),
            ["wagtail.create", "wagtail.edit", "wagtail.publish"],
        )

    def test_revert_and_publish_logs_reversion_and_publish(self):
        revision = self.hello_page.save_revision(user=self.editor)
        self.hello_page.save_revision(user=self.editor)

        self.login(user=self.administrator)
        response = self.client.post(
            reverse(
                "wagtailadmin_pages:revisions_revert",
                args=(self.hello_page.id, revision.id),
            ),
            {
                "title": "Hello World!",
                "content": "another hello",
                "slug": "hello-world",
                "action-publish": "action-publish",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

        entries = (
            PageLogEntry.objects.filter(page=self.hello_page)
            .values_list("action", flat=True)
            .order_by("action")
        )
        self.assertListEqual(
            list(entries),
            ["wagtail.create", "wagtail.publish", "wagtail.rename", "wagtail.revert"],
        )

    def test_page_history_after_unscheduled_publication(self):
        # schedule for publishing
        go_live_at = timezone.now() + timedelta(minutes=30)
        if settings.USE_TZ:
            go_live_at = timezone.localtime(go_live_at)
        self.hello_page.go_live_at = go_live_at
        revision = self.hello_page.save_revision(log_action=True)
        revision.publish()

        self.login(user=self.editor)

        response = self.client.post(
            reverse(
                "wagtailadmin_pages:revisions_unschedule",
                args=(self.hello_page.id, revision.id),
            )
        )
        history_url = reverse(
            "wagtailadmin_pages:history", kwargs={"page_id": self.hello_page.id}
        )
        self.assertRedirects(
            response,
            history_url,
        )

        response = self.client.get(history_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            f"Page unscheduled for publishing at {render_timestamp(go_live_at)}",
        )

    def test_page_history_after_unscheduled_revision(self):
        # Prepare clean live page with revisions
        test_page = SimplePage(title="About", slug="about", content="hello")
        self.hello_page.add_child(instance=test_page)
        revision = test_page.save_revision(log_action=True)
        revision.publish()
        test_page.refresh_from_db()

        # Schedule a new version for publishing
        go_live_at = timezone.now() + timedelta(minutes=30)
        if settings.USE_TZ:
            go_live_at = timezone.localtime(go_live_at)
        test_page.go_live_at = go_live_at
        revision = test_page.save_revision(log_action=True)
        revision.publish()

        self.login(user=self.editor)

        response = self.client.post(
            reverse(
                "wagtailadmin_pages:revisions_unschedule",
                args=(test_page.id, revision.id),
            )
        )
        history_url = reverse(
            "wagtailadmin_pages:history", kwargs={"page_id": test_page.id}
        )
        self.assertRedirects(
            response,
            history_url,
        )

        response = self.client.get(history_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            f"Revision {revision.id} from {render_timestamp(revision.created_at)} unscheduled from publishing at {render_timestamp(go_live_at)}.",
        )

    def test_page_history_requires_edit_permission_for_access(self):
        # the editor user only has access to the Hello page and its children
        self.login(user=self.editor)

        response = self.client.get(
            reverse(
                "wagtailadmin_pages:history", kwargs={"page_id": self.about_page.id}
            ),
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(
            response.context["message"],
            "Sorry, you do not have permission to access this area.",
        )
        response = self.client.get(
            reverse(
                "wagtailadmin_pages:history", kwargs={"page_id": self.hello_page.id}
            ),
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_num_queries(self):
        self.login(user=self.editor)

        history_url = reverse(
            "wagtailadmin_pages:history", kwargs={"page_id": self.hello_page.id}
        )

        # Warm up the cache
        self.client.get(history_url)

        # Initial load, without any log entries
        with self.assertNumQueries(19):
            self.client.get(history_url)

        # With some log entries
        self._update_page(self.hello_page)
        with self.assertNumQueries(21):
            self.client.get(history_url)

        # With even more log entries, should remain the same (no N+1 queries)
        log(
            instance=self.hello_page,
            action="wagtail.comments.create",
            user=self.editor,
            revision=self.hello_page.latest_revision,
            data={
                "comment": {
                    "id": 123,
                    "contentpath": "content",
                    "text": "A comment that was added",
                }
            },
        )

        log(
            instance=self.hello_page,
            action="wagtail.comments.edit",
            user=self.editor,
            revision=self.hello_page.latest_revision,
            data={
                "comment": {
                    "id": 123,
                    "contentpath": "content",
                    "text": "A comment that was edited",
                }
            },
        )
        self._update_page(self.hello_page)
        with self.assertNumQueries(21):
            self.client.get(history_url)
