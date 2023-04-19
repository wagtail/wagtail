from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time

from wagtail.models import GroupPagePermission, Page, PageLogEntry, PageViewRestriction
from wagtail.test.testapp.models import SimplePage
from wagtail.test.utils import WagtailTestUtils


class TestAuditLogAdmin(WagtailTestUtils, TestCase):
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

        for permission_type in ["add", "edit", "publish"]:
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
            "Added the &#x27;Private, accessible to logged-in users&#x27; view restriction",
        )
        self.assertContains(
            response,
            "Updated the view restriction to &#x27;Private, accessible with the following password&#x27;",
        )
        self.assertContains(
            response,
            "Removed the &#x27;Private, accessible with the following password&#x27; view restriction",
        )

        self.assertContains(
            response, "system", 3
        )  # create without a user + remove restriction + 1 from unrelated admin color theme
        self.assertContains(
            response, "the_editor", 9
        )  # 7 entries by editor + 1 in sidebar menu + 1 in filter
        self.assertContains(
            response, "administrator", 2
        )  # the final restriction change + filter

    def test_page_history_filters(self):
        self.login(user=self.editor)
        self._update_page(self.hello_page)

        history_url = reverse(
            "wagtailadmin_pages:history", kwargs={"page_id": self.hello_page.id}
        )
        response = self.client.get(history_url + "?action=wagtail.edit")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Draft saved", count=2)
        self.assertNotContains(response, "Locked")
        self.assertNotContains(response, "Unlocked")
        self.assertNotContains(response, "Page scheduled for publishing")
        self.assertNotContains(response, "Published")

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
            reverse("wagtailadmin_pages:edit", args=(self.hello_page.id,)),
            {
                "title": "Hello World!",
                "content": "another hello",
                "slug": "hello-world",
                "revision": revision.id,
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
            f"Page unscheduled for publishing at {go_live_at.strftime('%d %b %Y %H:%M')}",
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
            f"Revision {revision.id} from {revision.created_at.strftime('%d %b %Y %H:%M')} unscheduled from publishing at {go_live_at.strftime('%d %b %Y %H:%M')}.",
        )
