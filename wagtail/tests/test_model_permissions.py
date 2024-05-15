from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase, override_settings
from django.utils import timezone

from wagtail.models import (
    GroupApprovalTask,
    ModelPermissionTester,
    Workflow,
    WorkflowContentType,
    WorkflowTask,
)
from wagtail.test.testapp.models import Advert, FullFeaturedSnippet
from wagtail.test.utils.wagtail_tests import WagtailTestUtils


class TestModelPermission(WagtailTestUtils, TestCase):
    # This follows the tests from test_page_permissions

    def create_workflow_and_task(self):
        workflow = Workflow.objects.create(name="test_workflow")
        task_1 = GroupApprovalTask.objects.create(name="test_task_1")
        task_1.groups.add(self.moderator_group)
        WorkflowTask.objects.create(
            workflow=workflow, task=task_1.task_ptr, sort_order=1
        )
        WorkflowContentType.objects.create(
            workflow=workflow,
            content_type=ContentType.objects.get_for_model(FullFeaturedSnippet),
        )
        return workflow, task_1

    @classmethod
    def setUpTestData(cls):
        cls.editor = cls.create_user("editor", password="password")
        cls.moderator = cls.create_user("moderator", password="password")
        cls.superuser = cls.create_superuser("superuser", password="password")

        cls.editor_group = Group.objects.get(name="Editors")
        cls.moderator_group = Group.objects.get(name="Moderators")

        cls.editor.groups.add(cls.editor_group)
        cls.moderator.groups.add(cls.moderator_group)

        # Default Django permissions
        editor_permissions = []
        for model in [Advert, FullFeaturedSnippet]:
            editor_permissions.append(
                Permission.objects.get(
                    content_type__app_label="tests",
                    codename=f"add_{model._meta.model_name}",
                )
            )
            editor_permissions.append(
                Permission.objects.get(
                    content_type__app_label="tests",
                    codename=f"change_{model._meta.model_name}",
                )
            )
            editor_permissions.append(
                Permission.objects.get(
                    content_type__app_label="tests",
                    codename=f"delete_{model._meta.model_name}",
                )
            )

        # Allow moderators to publish
        moderator_permissions = editor_permissions + [
            Permission.objects.get(
                content_type__app_label="tests",
                codename=f"publish_{FullFeaturedSnippet._meta.model_name}",
            ),
        ]

        cls.editor_group.permissions.add(*editor_permissions)
        cls.moderator_group.permissions.add(*moderator_permissions)

        # Model with no extra features
        cls.standard = Advert.objects.create(text="Hello standard")

        # Model with all the features
        cls.draft = FullFeaturedSnippet.objects.create(text="Hello draft", live=False)
        cls.live = FullFeaturedSnippet.objects.create(text="Hello live", live=True)

    def test_unimplemented_permissions(self):
        tester = ModelPermissionTester(self.superuser, self.live)

        # These are specific to pages for now
        for method in [
            tester.can_add_subobject,
            tester.can_set_view_restrictions,
            tester.can_publish_subobject,
            tester.can_reorder_children,
            tester.can_move,
        ]:
            with self.assertRaises(NotImplementedError):
                method()

        with self.assertRaises(NotImplementedError):
            tester.can_move_to(None)
        with self.assertRaises(NotImplementedError):
            tester.can_copy_to(None)

    def test_nonpublisher_permissions(self):
        standard_perms = ModelPermissionTester(self.editor, self.standard)
        draft_perms = ModelPermissionTester(self.editor, self.draft)
        live_perms = ModelPermissionTester(self.editor, self.live)

        # Can edit standard, draft, and live
        self.assertTrue(standard_perms.can_edit())
        self.assertTrue(draft_perms.can_edit())
        self.assertTrue(live_perms.can_edit())

        # Can only delete standard and draft
        self.assertTrue(standard_perms.can_delete())
        self.assertTrue(draft_perms.can_delete())
        self.assertFalse(live_perms.can_delete())

        # Can't publish standard, draft, nor live
        self.assertFalse(standard_perms.can_publish())
        self.assertFalse(draft_perms.can_publish())
        self.assertFalse(live_perms.can_publish())

        # Can't unpublish standard, draft, nor live
        self.assertFalse(standard_perms.can_unpublish())
        self.assertFalse(draft_perms.can_unpublish())
        self.assertFalse(live_perms.can_unpublish())

        # Can copy standard, draft, and live
        self.assertTrue(standard_perms.can_copy())
        self.assertTrue(draft_perms.can_copy())
        self.assertTrue(live_perms.can_copy())

        # Can view "revisions" (history) for standard, draft, and live
        # This corresponds to being able to see the history view (not actual
        # revisions) for -historical- reasons...
        # This method in PagePermissionTester has been around since before
        # log actions were introduced. This was used to check for access to the
        # "revisions index" view, which has since been replaced by the "history"
        # view. The history view is applicable to all models as it uses log
        # entries instead of revisions, so we should not require the object to
        # be an instance of RevisionMixin. Hence, it returns true for standard.
        self.assertTrue(standard_perms.can_view_revisions())
        self.assertTrue(draft_perms.can_view_revisions())
        self.assertTrue(live_perms.can_view_revisions())

    def test_publisher_permissions(self):
        standard_perms = ModelPermissionTester(self.moderator, self.standard)
        draft_perms = ModelPermissionTester(self.moderator, self.draft)
        live_perms = ModelPermissionTester(self.moderator, self.live)

        # Can edit standard, draft, and live
        self.assertTrue(standard_perms.can_edit())
        self.assertTrue(draft_perms.can_edit())
        self.assertTrue(live_perms.can_edit())

        # Can delete standard, draft, and live
        self.assertTrue(standard_perms.can_delete())
        self.assertTrue(draft_perms.can_delete())
        self.assertTrue(live_perms.can_delete())

        # Can't publish standard as it does not support publishing
        self.assertFalse(standard_perms.can_publish())

        # Can publish draft and live
        self.assertTrue(draft_perms.can_publish())
        self.assertTrue(live_perms.can_publish())

        # Can't unpublish standard as it does not support publishing
        self.assertFalse(standard_perms.can_unpublish())

        # Can't unpublish draft as it is not published
        self.assertFalse(draft_perms.can_unpublish())

        # Can unpublish live
        self.assertTrue(live_perms.can_unpublish())

        # Can copy standard, draft, and live
        self.assertTrue(standard_perms.can_copy())
        self.assertTrue(draft_perms.can_copy())
        self.assertTrue(live_perms.can_copy())

        # Can view "revisions" (history) for standard, draft, and live
        self.assertTrue(standard_perms.can_view_revisions())
        self.assertTrue(draft_perms.can_view_revisions())
        self.assertTrue(live_perms.can_view_revisions())

    def test_publish_permissions_without_edit(self):
        self.moderator_group.permissions.remove(
            Permission.objects.get(
                content_type__app_label="tests",
                codename=f"change_{FullFeaturedSnippet._meta.model_name}",
            ),
            Permission.objects.get(
                content_type__app_label="tests",
                codename=f"change_{Advert._meta.model_name}",
            ),
        )

        standard_perms = ModelPermissionTester(self.moderator, self.standard)
        draft_perms = ModelPermissionTester(self.moderator, self.draft)
        live_perms = ModelPermissionTester(self.moderator, self.live)

        # There is no concept of ownership (as of now), so we can't edit anything
        self.assertFalse(standard_perms.can_edit())
        self.assertFalse(draft_perms.can_edit())
        self.assertFalse(live_perms.can_edit())

        # Can delete standard, draft, and live
        self.assertTrue(standard_perms.can_delete())
        self.assertTrue(draft_perms.can_delete())
        self.assertTrue(live_perms.can_delete())

        # Can't publish standard as it does not support publishing
        self.assertFalse(standard_perms.can_publish())

        # Can still publish draft and live
        self.assertTrue(draft_perms.can_publish())
        self.assertTrue(live_perms.can_publish())

        # Can't unpublish standard as it does not support publishing
        self.assertFalse(standard_perms.can_unpublish())

        # Can't unpublish draft as it is not published
        self.assertFalse(draft_perms.can_unpublish())

        # Can still unpublish live
        self.assertTrue(live_perms.can_unpublish())

        # Can copy standard, draft, and live
        self.assertTrue(standard_perms.can_copy())
        self.assertTrue(draft_perms.can_copy())
        self.assertTrue(live_perms.can_copy())

        # Can view "revisions" (history) for standard, draft, and live
        self.assertTrue(standard_perms.can_view_revisions())
        self.assertTrue(draft_perms.can_view_revisions())
        self.assertTrue(live_perms.can_view_revisions())

    def test_inactive_user_has_no_permissions(self):
        self.superuser.is_active = False
        self.superuser.save()

        standard_perms = ModelPermissionTester(self.superuser, self.standard)
        draft_perms = ModelPermissionTester(self.superuser, self.draft)
        live_perms = ModelPermissionTester(self.superuser, self.live)

        # Can't do anything
        self.assertFalse(standard_perms.can_edit())
        self.assertFalse(draft_perms.can_edit())
        self.assertFalse(live_perms.can_edit())
        self.assertFalse(standard_perms.can_delete())
        self.assertFalse(draft_perms.can_delete())
        self.assertFalse(live_perms.can_delete())
        self.assertFalse(standard_perms.can_publish())
        self.assertFalse(draft_perms.can_publish())
        self.assertFalse(live_perms.can_publish())
        self.assertFalse(standard_perms.can_unpublish())
        self.assertFalse(draft_perms.can_unpublish())
        self.assertFalse(live_perms.can_unpublish())
        self.assertFalse(standard_perms.can_copy())
        self.assertFalse(draft_perms.can_copy())
        self.assertFalse(live_perms.can_copy())
        self.assertFalse(standard_perms.can_view_revisions())
        self.assertFalse(draft_perms.can_view_revisions())
        self.assertFalse(live_perms.can_view_revisions())

    def test_superuser_has_full_permissions(self):
        standard_perms = ModelPermissionTester(self.superuser, self.standard)
        draft_perms = ModelPermissionTester(self.superuser, self.draft)
        live_perms = ModelPermissionTester(self.superuser, self.live)

        # Can edit standard, draft, and live
        self.assertTrue(standard_perms.can_edit())
        self.assertTrue(draft_perms.can_edit())
        self.assertTrue(live_perms.can_edit())

        # Can delete standard, draft, and live
        self.assertTrue(standard_perms.can_delete())
        self.assertTrue(draft_perms.can_delete())
        self.assertTrue(live_perms.can_delete())

        # Can't publish standard as it does not support publishing
        self.assertFalse(standard_perms.can_publish())

        # Can publish draft and live
        self.assertTrue(draft_perms.can_publish())
        self.assertTrue(live_perms.can_publish())

        # Can't unpublish standard as it does not support publishing
        self.assertFalse(standard_perms.can_unpublish())

        # Can't unpublish draft as it is not published
        self.assertFalse(draft_perms.can_unpublish())

        # Can unpublish live
        self.assertTrue(live_perms.can_unpublish())

        # Can copy standard, draft, and live
        self.assertTrue(standard_perms.can_copy())
        self.assertTrue(draft_perms.can_copy())
        self.assertTrue(live_perms.can_copy())

        # Can view "revisions" (history) for standard, draft, and live
        self.assertTrue(standard_perms.can_view_revisions())
        self.assertTrue(draft_perms.can_view_revisions())
        self.assertTrue(live_perms.can_view_revisions())

    def test_lock_for_superuser(self):
        standard_perms = ModelPermissionTester(self.superuser, self.standard)
        draft_perms = ModelPermissionTester(self.superuser, self.draft)
        live_perms = ModelPermissionTester(self.superuser, self.live)

        # Can't lock standard as it does not support locking
        self.assertFalse(standard_perms.can_lock())

        # Can lock draft and live
        self.assertTrue(draft_perms.can_lock())
        self.assertTrue(live_perms.can_lock())

        # Can't unlock standard as it does not support locking
        self.assertFalse(standard_perms.can_unlock())

        # Can unlock draft and live
        # Historically, can_unlock returns True even if it's currently unlocked
        # as long as the user has the permission to unlock
        self.assertTrue(draft_perms.can_unlock())
        self.assertTrue(live_perms.can_unlock())

        # Lock by someone else
        self.live.locked = True
        self.live.locked_by = self.moderator
        self.live.locked_at = timezone.now()
        self.live.save()

        # Historically, can_lock returns True even if it's currently locked by
        # anyone as long as the user has the permission to lock
        self.assertTrue(live_perms.can_lock())

        # Can't unpublish if locked by someone else
        self.assertFalse(live_perms.can_unpublish())

        # Can unlock even if locked by someone else
        self.assertTrue(live_perms.can_unlock())

        # Lock by self
        self.live.locked_by = self.superuser
        self.live.save()

        # Can unpublish if locked by self, as the object appears to be unlocked
        self.assertTrue(live_perms.can_unpublish())

        # Can also unlock
        self.assertTrue(live_perms.can_unlock())

    def test_lock_for_user_with_lock_and_unlock_permissions(self):
        self.moderator_group.permissions.add(
            Permission.objects.get(
                content_type__app_label="tests",
                codename=f"lock_{FullFeaturedSnippet._meta.model_name}",
            ),
            Permission.objects.get(
                content_type__app_label="tests",
                codename=f"unlock_{FullFeaturedSnippet._meta.model_name}",
            ),
        )
        standard_perms = ModelPermissionTester(self.moderator, self.standard)
        draft_perms = ModelPermissionTester(self.moderator, self.draft)
        live_perms = ModelPermissionTester(self.moderator, self.live)

        # Can't lock standard as it does not support locking
        self.assertFalse(standard_perms.can_lock())

        # Can lock draft and live
        self.assertTrue(draft_perms.can_lock())
        self.assertTrue(live_perms.can_lock())

        # Can't unlock standard as it does not support locking
        self.assertFalse(standard_perms.can_unlock())

        # Can unlock draft and live
        # Historically, can_unlock returns True even if it's currently unlocked
        # as long as the user has the permission to unlock
        self.assertTrue(draft_perms.can_unlock())
        self.assertTrue(live_perms.can_unlock())

        # Lock by someone else
        self.live.locked = True
        self.live.locked_by = self.superuser
        self.live.locked_at = timezone.now()
        self.live.save()

        # Historically, can_lock returns True even if it's currently locked by
        # anyone as long as the user has the permission to lock
        self.assertTrue(live_perms.can_lock())

        # Can't unpublish if locked by someone else
        self.assertFalse(live_perms.can_unpublish())

        # Can unlock even if locked by someone else,
        # as long as they have the unlock permission
        self.assertTrue(live_perms.can_unlock())

        # Lock by self
        self.live.locked_by = self.moderator
        self.live.save()

        # Can unpublish if locked by self, as the object appears to be unlocked
        self.assertTrue(live_perms.can_unpublish())

        # Can also unlock
        self.assertTrue(live_perms.can_unlock())

    def test_lock_for_user_with_lock_permission_only(self):
        self.editor_group.permissions.add(
            Permission.objects.get(
                content_type__app_label="tests",
                codename=f"lock_{FullFeaturedSnippet._meta.model_name}",
            ),
        )
        standard_perms = ModelPermissionTester(self.editor, self.standard)
        draft_perms = ModelPermissionTester(self.editor, self.draft)
        live_perms = ModelPermissionTester(self.editor, self.live)

        # Can't lock standard as it does not support locking
        self.assertFalse(standard_perms.can_lock())

        # Can lock draft and live
        self.assertTrue(draft_perms.can_lock())
        self.assertTrue(live_perms.can_lock())

        # Can't unlock standard as it does not support locking
        self.assertFalse(standard_perms.can_unlock())

        # Can't unlock draft and live as they don't have the unlock permission
        self.assertFalse(draft_perms.can_unlock())
        self.assertFalse(live_perms.can_unlock())

        # Lock by someone else
        self.live.locked = True
        self.live.locked_by = self.superuser
        self.live.locked_at = timezone.now()
        self.live.save()

        # Historically, can_lock returns True even if it's currently locked by
        # anyone as long as the user has the permission to lock
        self.assertTrue(live_perms.can_lock())

        # Can't unpublish as they don't have the publish permission
        self.assertFalse(live_perms.can_unpublish())

        # Can't unlock if locked by someone else,
        # as they don't have the unlock permission
        self.assertFalse(live_perms.can_unlock())

        # Lock by self
        self.live.locked_by = self.editor
        self.live.save()

        # Can't unpublish as they don't have the publish permission
        self.assertFalse(live_perms.can_unpublish())

        # Can unlock even without the unlock permission, as they locked it
        self.assertTrue(live_perms.can_unlock())

    def test_lock_for_user_without_lock_and_unlock_permission(self):
        standard_perms = ModelPermissionTester(self.editor, self.standard)
        draft_perms = ModelPermissionTester(self.editor, self.draft)
        live_perms = ModelPermissionTester(self.editor, self.live)

        # Can't lock standard as it does not support locking
        self.assertFalse(standard_perms.can_lock())

        # Can't lock draft and live as they don't have the lock permission
        self.assertFalse(standard_perms.can_lock())
        self.assertFalse(draft_perms.can_lock())

        # Can't unlock standard as it does not support locking
        self.assertFalse(standard_perms.can_unlock())

        # Can't unlock draft and live as they don't have the unlock permission
        self.assertFalse(draft_perms.can_unlock())
        self.assertFalse(live_perms.can_unlock())

        # Lock by someone else
        self.live.locked = True
        self.live.locked_by = self.superuser
        self.live.locked_at = timezone.now()
        self.live.save()

        # Can't lock as they don't have the lock permission
        self.assertFalse(live_perms.can_lock())

        # Can't unpublish as they don't have the publish permission
        self.assertFalse(live_perms.can_unpublish())

        # Can't unlock if locked by someone else,
        # as they don't have the unlock permission
        self.assertFalse(live_perms.can_unlock())

        # Lock by self
        # This may happen if the user locked it before losing the permission
        self.live.locked_by = self.editor
        self.live.save()

        # Can't unpublish as they don't have the publish permission
        self.assertFalse(live_perms.can_unpublish())

        # Can unlock even without the unlock permission, as they locked it
        self.assertTrue(live_perms.can_unlock())

    def test_lock_for_non_editing_user(self):
        self.editor_group.permissions.clear()
        self.editor_group.permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin",
                codename="access_admin",
            )
        )

        perms = ModelPermissionTester(self.editor, self.live)

        self.assertFalse(perms.can_lock())
        self.assertFalse(perms.can_unlock())

    def test_object_locked_for_unlocked_object(self):
        standard_perms = ModelPermissionTester(self.superuser, self.standard)
        live_perms = ModelPermissionTester(self.superuser, self.live)

        # Not locked as it does not support locking
        self.assertFalse(standard_perms.object_locked())

        # Not locked as it is not locked
        self.assertFalse(live_perms.object_locked())

    def test_object_locked_for_locked_object(self):
        self.editor_group.permissions.add(
            Permission.objects.get(
                content_type__app_label="tests",
                codename=f"lock_{FullFeaturedSnippet._meta.model_name}",
            ),
        )
        perms = ModelPermissionTester(self.editor, self.live)

        # Lock the object
        self.live.locked = True
        self.live.locked_by = self.editor
        self.live.locked_at = timezone.now()
        self.live.save()

        # The user who locked the object shouldn't see the object as locked
        self.assertFalse(perms.object_locked())

        # Other users should see the object as locked
        other_perms = ModelPermissionTester(self.superuser, self.live)
        self.assertTrue(other_perms.object_locked())

    @override_settings(WAGTAILADMIN_GLOBAL_EDIT_LOCK=True)
    def test_object_locked_for_locked_object_with_global_lock_enabled(self):
        self.editor_group.permissions.add(
            Permission.objects.get(
                content_type__app_label="tests",
                codename=f"lock_{FullFeaturedSnippet._meta.model_name}",
            ),
        )
        perms = ModelPermissionTester(self.editor, self.live)

        # Lock the object
        self.live.locked = True
        self.live.locked_by = self.editor
        self.live.locked_at = timezone.now()
        self.live.save()

        # The user who locked the object should now also see the object as locked
        self.assertTrue(perms.object_locked())

        # Other users should see the object as locked, like before
        other_perms = ModelPermissionTester(self.superuser, self.live)
        self.assertTrue(other_perms.object_locked())

    def test_object_locked_in_workflow(self):
        workflow, task = self.create_workflow_and_task()
        self.live.save_revision()
        workflow.start(self.live, self.editor)

        moderator_perms = ModelPermissionTester(self.moderator, self.live)

        # the moderator is in the group assigned to moderate the task, so the object should
        # not be locked for them
        self.assertFalse(moderator_perms.object_locked())

        superuser_perms = ModelPermissionTester(self.superuser, self.live)

        # superusers can moderate any GroupApprovalTask, so the object should not be locked
        # for them
        self.assertFalse(superuser_perms.object_locked())

        editor_perms = ModelPermissionTester(self.editor, self.live)

        # the editor is not in the group assigned to moderate the task, so the object should
        # be locked for them
        self.assertTrue(editor_perms.object_locked())

    def test_object_lock_in_workflow(self):
        workflow, task = self.create_workflow_and_task()
        self.live.save_revision()
        workflow.start(self.live, self.editor)

        moderator_perms = ModelPermissionTester(self.moderator, self.live)

        # the moderator is in the group assigned to moderate the task, so they can lock the object, but can't unlock it
        # unless they're the locker
        self.assertTrue(moderator_perms.can_lock())
        self.assertFalse(moderator_perms.can_unlock())

        editor_perms = ModelPermissionTester(self.editor, self.live)

        # the editor is not in the group assigned to moderate the task, so they can't lock or unlock the object
        self.assertFalse(editor_perms.can_lock())
        self.assertFalse(editor_perms.can_unlock())

        # Lock the object
        self.live.locked = True
        self.live.locked_by = self.moderator
        self.live.locked_at = timezone.now()
        self.live.save()

        # the moderator can unlock the object as they're the locker
        self.assertTrue(moderator_perms.can_unlock())
