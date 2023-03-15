from django.contrib.admin.utils import quote
from django.contrib.auth import get_permission_codename
from django.contrib.auth.models import Group, Permission
from django.test import TestCase, override_settings
from django.urls import NoReverseMatch, reverse
from django.utils import timezone

from wagtail.admin.utils import get_user_display_name
from wagtail.locks import WorkflowLock
from wagtail.models import GroupApprovalTask, Workflow, WorkflowTask
from wagtail.test.testapp.models import (
    Advert,
    DraftStateModel,
    FullFeaturedSnippet,
    LockableModel,
)
from wagtail.test.utils import WagtailTestUtils


class BaseLockingTestCase(WagtailTestUtils, TestCase):
    model = LockableModel

    def setUp(self):
        self.user = self.login()
        self.snippet = self.model.objects.create(text="I'm a lockable snippet!")

    @property
    def model_name(self):
        return self.model._meta.verbose_name

    def get_url(self, name, args=None):
        args = args if args is not None else [quote(self.snippet.pk)]
        return reverse(self.snippet.snippet_viewset.get_url_name(name), args=args)

    def lock_snippet(self, user=None):
        self.snippet.locked = True
        self.snippet.locked_by = user
        self.snippet.locked_at = timezone.now()
        self.snippet.save()

    def refresh_snippet(self):
        self.snippet.refresh_from_db()

    def set_permissions(self, permission_names, user=None):
        if user is None:
            user = self.user

        user.is_superuser = False

        permissions = [
            Permission.objects.get(
                content_type__app_label="wagtailadmin",
                codename="access_admin",
            )
        ]

        for name in permission_names:
            permissions.append(
                Permission.objects.get(
                    content_type__app_label="tests",
                    codename=get_permission_codename(name, self.model._meta),
                )
            )

        user.user_permissions.set(permissions)
        user.save()


class DraftStateModelTestCase:
    model = DraftStateModel

    def refresh_snippet(self):
        self.snippet.refresh_from_db()
        self.snippet = self.snippet.get_latest_revision_as_object()


class TestLocking(BaseLockingTestCase):
    def test_lock_post(self):
        response = self.client.post(self.get_url("lock"))
        self.refresh_snippet()

        # Check response
        self.assertRedirects(response, self.get_url("edit"))

        # Check that the snippet is locked
        self.assertTrue(self.snippet.locked)
        self.assertEqual(self.snippet.locked_by, self.user)
        self.assertIsNotNone(self.snippet.locked_at)

    def test_lock_get(self):
        response = self.client.get(self.get_url("lock"))
        self.refresh_snippet()

        # Check response
        self.assertEqual(response.status_code, 405)

        # Check that the snippet is still unlocked
        self.assertFalse(self.snippet.locked)
        self.assertIsNone(self.snippet.locked_by)
        self.assertIsNone(self.snippet.locked_at)

    def test_lock_post_already_locked(self):
        # Lock the snippet
        self.lock_snippet(self.user)

        response = self.client.post(self.get_url("lock"))
        self.refresh_snippet()

        # Check response
        self.assertRedirects(response, self.get_url("edit"))

        # Check that the snippet is still locked
        self.assertTrue(self.snippet.locked)
        self.assertEqual(self.snippet.locked_by, self.user)
        self.assertIsNotNone(self.snippet.locked_at)

    def test_lock_post_with_good_redirect(self):
        next_url = self.get_url("list", args=[])
        response = self.client.post(self.get_url("lock"), {"next": next_url})
        self.refresh_snippet()

        # Check response
        self.assertRedirects(response, next_url)

        # Check that the snippet is locked
        self.assertTrue(self.snippet.locked)
        self.assertEqual(self.snippet.locked_by, self.user)
        self.assertIsNotNone(self.snippet.locked_at)

    def test_lock_post_with_bad_redirect(self):
        response = self.client.post(
            self.get_url("lock"),
            {"next": "http://www.google.co.uk"},
        )
        self.refresh_snippet()

        # Check response
        self.assertRedirects(response, self.get_url("edit"))

        # Check that the snippet is locked
        self.assertTrue(self.snippet.locked)
        self.assertEqual(self.snippet.locked_by, self.user)
        self.assertIsNotNone(self.snippet.locked_at)

    def test_lock_post_bad_snippet(self):
        response = self.client.post(self.get_url("edit", args=[quote(9999999)]))
        self.refresh_snippet()

        # Check response
        self.assertEqual(response.status_code, 404)

        # Check that the snippet is still unlocked
        self.assertFalse(self.snippet.locked)
        self.assertIsNone(self.snippet.locked_by)
        self.assertIsNone(self.snippet.locked_at)

    def test_lock_post_not_enabled_snippet(self):
        self.snippet = Advert.objects.create(text="I'm a non-lockable snippet!")

        with self.assertRaises(NoReverseMatch):
            self.client.post(self.get_url("lock"))

    def test_lock_post_bad_permissions(self):
        # Remove privileges from user
        self.set_permissions([])

        response = self.client.post(self.get_url("lock"))
        self.refresh_snippet()

        # Check response
        self.assertRedirects(response, reverse("wagtailadmin_home"))

        # Check that the snippet is still unlocked
        self.assertFalse(self.snippet.locked)
        self.assertIsNone(self.snippet.locked_by)
        self.assertIsNone(self.snippet.locked_at)

    def test_unlock_post(self):
        # Lock the snippet
        self.lock_snippet(self.user)

        response = self.client.post(self.get_url("unlock"))
        self.refresh_snippet()

        # Check response
        self.assertRedirects(response, self.get_url("edit"))

        # Check that the snippet is unlocked
        self.assertFalse(self.snippet.locked)
        self.assertIsNone(self.snippet.locked_by)
        self.assertIsNone(self.snippet.locked_at)

    def test_unlock_get(self):
        # Lock the snippet
        self.lock_snippet(self.user)

        response = self.client.get(self.get_url("unlock"))
        self.refresh_snippet()

        # Check response
        self.assertEqual(response.status_code, 405)

        # Check that the snippet is still locked
        self.assertTrue(self.snippet.locked)
        self.assertEqual(self.snippet.locked_by, self.user)
        self.assertIsNotNone(self.snippet.locked_at)

    def test_unlock_post_already_unlocked(self):
        response = self.client.post(self.get_url("unlock"))
        self.refresh_snippet()

        # Check response
        self.assertRedirects(response, self.get_url("edit"))

        # Check that the snippet is still unlocked
        self.assertFalse(self.snippet.locked)
        self.assertIsNone(self.snippet.locked_by)
        self.assertIsNone(self.snippet.locked_at)

    def test_unlock_post_with_good_redirect(self):
        # Lock the snippet
        self.lock_snippet(self.user)

        next_url = self.get_url("list", args=[])
        response = self.client.post(self.get_url("unlock"), {"next": next_url})
        self.refresh_snippet()

        # Check response
        self.assertRedirects(response, next_url)

        # Check that the snippet is unlocked
        self.assertFalse(self.snippet.locked)
        self.assertIsNone(self.snippet.locked_by)
        self.assertIsNone(self.snippet.locked_at)

    def test_unlock_post_with_bad_redirect(self):
        # Lock the snippet
        self.lock_snippet(self.user)

        response = self.client.post(
            self.get_url("unlock"),
            {"next": "http://www.google.co.uk"},
        )
        self.refresh_snippet()

        # Check response
        self.assertRedirects(response, self.get_url("edit"))

        # Check that the snippet is unlocked
        self.assertFalse(self.snippet.locked)
        self.assertIsNone(self.snippet.locked_by)
        self.assertIsNone(self.snippet.locked_at)

    def test_unlock_post_bad_snippet(self):
        # Lock the snippet
        self.lock_snippet(self.user)

        response = self.client.post(self.get_url("unlock", args=[quote(9999999)]))
        self.refresh_snippet()

        # Check response
        self.assertEqual(response.status_code, 404)

        # Check that the snippet is still locked
        self.assertTrue(self.snippet.locked)
        self.assertEqual(self.snippet.locked_by, self.user)
        self.assertIsNotNone(self.snippet.locked_at)

    def test_unlock_post_not_enabled_snippet(self):
        self.snippet = Advert.objects.create(text="I'm a non-lockable snippet!")
        with self.assertRaises(NoReverseMatch):
            self.client.post(self.get_url("unlock"))

    def test_unlock_post_bad_permissions(self):
        # Remove privileges from user
        self.user.is_superuser = False
        self.user.groups.add(Group.objects.get(name="Editors"))
        self.user.save()

        # Lock the snippet
        self.lock_snippet(self.create_user("user2"))

        response = self.client.post(self.get_url("unlock"))
        self.refresh_snippet()

        # Check response
        self.assertEqual(response.status_code, 302)

        # Check that the snippet is still locked
        self.assertTrue(self.snippet.locked)
        self.assertIsNotNone(self.snippet.locked_at)

    def test_unlock_post_own_snippet_with_bad_permissions(self):
        """User can unlock a snippet they have locked without the unlock permission."""

        # Remove privileges from user
        self.user.is_superuser = False
        self.user.groups.add(Group.objects.get(name="Editors"))
        self.user.save()

        # Lock the snippet
        self.lock_snippet(self.user)

        next_url = reverse("wagtailadmin_home")
        response = self.client.post(self.get_url("unlock"), {"next": next_url})
        self.refresh_snippet()

        # Check response
        self.assertRedirects(response, next_url)

        # Check that the snippet is not locked
        self.assertFalse(self.snippet.locked)
        self.assertIsNone(self.snippet.locked_by)
        self.assertIsNone(self.snippet.locked_at)


class TestLockingWithDraftState(DraftStateModelTestCase, TestLocking):
    pass


class TestEditLockedSnippet(BaseLockingTestCase):
    save_button_label = "Save"

    def test_edit_post_locked_by_another_user(self):
        """A user cannot edit a snippet that is locked by another user."""
        # Lock the snippet
        self.lock_snippet(self.create_user("user2"))

        # Try to edit the snippet
        response = self.client.post(
            self.get_url("edit"),
            {"text": "Edited while locked"},
        )
        self.refresh_snippet()

        # Should show lock message
        self.assertContains(
            response,
            f"The {self.model_name} could not be saved as it is locked",
        )

        # Check that the snippet is still locked
        self.assertTrue(self.snippet.locked)

        # Check that the snippet is not edited
        self.assertEqual(self.snippet.text, "I'm a lockable snippet!")

    def test_edit_post_locked_by_self(self):
        """A user can edit a snippet that is locked by themselves."""
        # Lock the snippet
        self.lock_snippet(self.user)

        # Try to edit the snippet
        response = self.client.post(
            self.get_url("edit"),
            {"text": "Edited while locked"},
            follow=True,
        )
        self.refresh_snippet()

        # Should not show error message
        self.assertNotContains(
            response,
            f"The {self.model_name} could not be saved as it is locked",
        )

        # Check that the snippet is still locked
        self.assertTrue(self.snippet.locked)

        # Check that the snippet is edited
        self.assertEqual(self.snippet.text, "Edited while locked")

    @override_settings(WAGTAILADMIN_GLOBAL_EDIT_LOCK=True)
    def test_edit_post_locked_by_self_with_global_lock_enabled(self):
        """A user cannot edit a snippet that is locked by themselves if the setting is enabled."""
        # Lock the snippet
        self.lock_snippet(self.user)

        # Try to edit the snippet
        response = self.client.post(
            self.get_url("edit"),
            {"text": "Edited while locked"},
        )
        self.refresh_snippet()

        # Should show lock message
        self.assertContains(
            response,
            f"The {self.model_name} could not be saved as it is locked",
        )

        # Check that the snippet is still locked
        self.assertTrue(self.snippet.locked)

        # Check that the snippet is not edited
        self.assertEqual(self.snippet.text, "I'm a lockable snippet!")

    def test_edit_get_locked_by_self(self):
        """A user can edit and unlock a snippet that is locked by themselves."""
        cases = [
            (["change", "unlock"]),
            (["change"]),  # Can unlock even without unlock permission
        ]

        for permissions in cases:
            with self.subTest(
                "User can edit and unlock an object they have locked",
                permissions=permissions,
            ):
                # Lock the snippet
                self.lock_snippet(self.user)

                # Use the specified permissions
                self.set_permissions(permissions)

                # Get the edit page
                response = self.client.get(self.get_url("edit"))
                html = response.content.decode()
                unlock_url = self.get_url("unlock")

                # Should show lock message
                self.assertContains(
                    response,
                    "<b>'I&#x27;m a lockable snippet!' was locked</b> by <b>you</b> on",
                )

                # Should show Save action menu item
                self.assertContains(
                    response,
                    f'<em data-w-progress-target="label">{self.save_button_label}</em>',
                    html=True,
                )

                # Should not show Locked action menu item
                self.assertTagInHTML(
                    '<button type="submit" disabled>Locked</button>',
                    html,
                    count=0,
                    allow_extra_attrs=True,
                )

                # Should show lock information in the side panel
                self.assertContains(
                    response,
                    f"Only you can make changes while the {self.model_name} is locked",
                )

                # Should show unlock toggle in the side panel
                self.assertTagInHTML(
                    f'<input type="checkbox" checked data-action="click->w-action#post" data-controller="w-action" data-w-action-url-value="{unlock_url}">',
                    html,
                    count=1,
                    allow_extra_attrs=True,
                )
                # Should show unlock button in the message
                self.assertTagInHTML(
                    f'<button type="button" data-action="w-action#post" data-controller="w-action" data-w-action-url-value="{unlock_url}">Unlock</button>',
                    html,
                    count=1,
                    allow_extra_attrs=True,
                )

    def test_edit_get_locked_by_another_user_has_unlock_permission(self):
        """A user needs to unlock a snippet that's locked by another user in order to edit it."""
        user = self.create_user("user2")
        # Lock the snippet
        self.lock_snippet(user)

        # Use edit and unlock permissions
        self.set_permissions(["change", "unlock"])

        # Get the edit page
        response = self.client.get(self.get_url("edit"))
        html = response.content.decode()
        unlock_url = self.get_url("unlock")
        display_name = get_user_display_name(user)

        # Should show lock message
        self.assertContains(
            response,
            f"<b>'I&#x27;m a lockable snippet!' was locked</b> by <b>{user}</b> on",
        )

        # Should show lock information in the side panel
        self.assertContains(
            response,
            f"Only {display_name} can make changes while the {self.model_name} is locked",
        )

        # Should not show Save action menu item
        self.assertNotContains(
            response,
            f'<em data-w-progress-target="label">{self.save_button_label}</em>',
            html=True,
        )

        # Should show Locked action menu item
        self.assertTagInHTML(
            '<button type="submit" disabled>Locked</button>',
            html,
            count=1,
            allow_extra_attrs=True,
        )

        # Should show unlock toggle in the side panel
        self.assertTagInHTML(
            f'<input type="checkbox" checked data-action="click->w-action#post" data-controller="w-action" data-w-action-url-value="{unlock_url}">',
            html,
            count=1,
            allow_extra_attrs=True,
        )
        # Should show unlock button in the message
        self.assertTagInHTML(
            f'<button type="button" data-action="w-action#post" data-controller="w-action" data-w-action-url-value="{unlock_url}">Unlock</button>',
            html,
            count=1,
            allow_extra_attrs=True,
        )

    def test_edit_get_locked_by_another_user_no_unlock_permission(self):
        """
        A different user cannot unlock the object without the unlock permission.
        """
        user = self.create_user("user2")
        # Lock the snippet
        self.lock_snippet(user)

        # Use edit permission only
        self.set_permissions(["change"])

        # Get the edit page
        response = self.client.get(self.get_url("edit"))
        html = response.content.decode()
        unlock_url = self.get_url("unlock")
        display_name = get_user_display_name(user)

        # Should show lock message
        self.assertContains(
            response,
            f"<b>'I&#x27;m a lockable snippet!' was locked</b> by <b>{user}</b> on",
        )

        # Should show lock information in the side panel
        self.assertContains(
            response,
            f"Only {display_name} can make changes while the {self.model_name} is locked",
        )

        # Should not show instruction to unlock
        self.assertNotContains(response, "Unlock")

        # Should not show Save action menu item
        self.assertNotContains(
            response,
            f'<em data-w-progress-target="label">{self.save_button_label}</em>',
            html=True,
        )

        # Should show Locked action menu item
        self.assertTagInHTML(
            '<button type="submit" disabled>Locked</button>',
            html,
            count=1,
            allow_extra_attrs=True,
        )

        # Should not show unlock toggle in the side panel
        self.assertTagInHTML(
            f'<input type="checkbox" checked data-action="click->w-action#post" data-controller="w-action" data-w-action-url-value="{unlock_url}">',
            html,
            count=0,
            allow_extra_attrs=True,
        )
        # Should not show unlock button in the message
        self.assertTagInHTML(
            f'<button type="button" data-action="w-action#post" data-controller="w-action" data-w-action-url-value="{unlock_url}">Unlock</button>',
            html,
            count=0,
            allow_extra_attrs=True,
        )

    def test_edit_get_unlocked_no_lock_permission(self):
        """A user cannot lock an object without the lock permission."""
        # Use edit permission only
        self.set_permissions(["change"])

        # Get the edit page
        response = self.client.get(self.get_url("edit"))
        html = response.content.decode()
        lock_url = self.get_url("lock")

        # Should not show lock message
        self.assertNotContains(
            response,
            "<b>'I&#x27;m a lockable snippet!' was locked</b>",
        )

        # Should show unlocked information in the side panel
        self.assertContains(
            response,
            f"Anyone can edit this {self.model_name}",
        )

        # Should not show info to lock the object in the side panel
        self.assertNotContains(
            response,
            "lock it to prevent others from editing",
        )

        # Should show Save action menu item
        self.assertContains(
            response,
            f'<em data-w-progress-target="label">{self.save_button_label}</em>',
            html=True,
        )

        # Should not show Locked action menu item
        self.assertTagInHTML(
            '<button type="submit" disabled>Locked</button>',
            html,
            count=0,
            allow_extra_attrs=True,
        )

        # Should not show lock toggle in the side panel
        self.assertTagInHTML(
            f'<input type="checkbox" data-action="click->w-action#post" data-controller="w-action" data-w-action-url-value="{lock_url}">',
            html,
            count=0,
            allow_extra_attrs=True,
        )
        # Should not show lock button in the message
        self.assertTagInHTML(
            f'<button type="button" data-action="w-action#post" data-controller="w-action" data-w-action-url-value="{lock_url}">Lock</button>',
            html,
            count=0,
            allow_extra_attrs=True,
        )

    def test_edit_get_unlocked_has_lock_permission(self):
        """A user can lock an object with the lock permission."""
        # Use edit and lock permissions
        self.set_permissions(["change", "lock"])

        # Get the edit page
        response = self.client.get(self.get_url("edit"))
        html = response.content.decode()
        lock_url = self.get_url("lock")

        # Should not show lock message
        self.assertNotContains(
            response,
            "<b>'I&#x27;m a lockable snippet!' was locked</b>",
        )

        # Should show unlocked information in the side panel
        self.assertContains(
            response,
            f"Anyone can edit this {self.model_name} – lock it to prevent others from editing",
        )

        # Should show Save action menu item
        self.assertContains(
            response,
            f'<em data-w-progress-target="label">{self.save_button_label}</em>',
            html=True,
        )

        # Should not show Locked action menu item
        self.assertTagInHTML(
            '<button type="submit" disabled>Locked</button>',
            html,
            count=0,
            allow_extra_attrs=True,
        )

        # Should show lock toggle in the side panel
        self.assertTagInHTML(
            f'<input type="checkbox" data-action="click->w-action#post" data-controller="w-action" data-w-action-url-value="{lock_url}">',
            html,
            count=1,
            allow_extra_attrs=True,
        )


class TestEditLockedDraftStateSnippet(DraftStateModelTestCase, TestEditLockedSnippet):
    save_button_label = "Save draft"


class TestWorkflowLock(BaseLockingTestCase):
    model = FullFeaturedSnippet

    def setUp(self):
        super().setUp()
        self.snippet.save_revision()
        self.moderator = self.create_user("moderator")
        self.moderators = Group.objects.get(name="Moderators")
        self.moderator.groups.add(self.moderators)
        self.set_permissions(["change"], user=self.user)
        self.set_permissions(["change", "publish"], user=self.moderator)

    def test_when_locked_by_workflow(self):
        workflow = Workflow.objects.create(name="test_workflow")
        task = GroupApprovalTask.objects.create(name="test_task")
        task.groups.add(self.moderators)
        WorkflowTask.objects.create(workflow=workflow, task=task, sort_order=1)
        workflow.start(self.snippet, self.user)

        lock = self.snippet.get_lock()
        self.assertIsInstance(lock, WorkflowLock)
        self.assertTrue(lock.for_user(self.user))
        self.assertFalse(lock.for_user(self.moderator))
        self.assertEqual(
            lock.get_message(self.user),
            "This full-featured snippet is currently awaiting moderation. "
            "Only reviewers for this task can edit the full-featured snippet.",
        )
        self.assertIsNone(lock.get_message(self.moderator))

        # When visiting a snippet in a workflow with multiple tasks, the message
        # displayed to users changes to show the current task the snippet is on

        # Add a second task to the workflow
        other_task = GroupApprovalTask.objects.create(name="another_task")
        WorkflowTask.objects.create(workflow=workflow, task=other_task, sort_order=2)

        lock = self.snippet.get_lock()
        self.assertEqual(
            lock.get_message(self.user),
            "This full-featured snippet is awaiting <b>'test_task'</b> in the "
            "<b>'test_workflow'</b> workflow. Only reviewers for this task "
            "can edit the full-featured snippet.",
        )
