from django.contrib.auth.models import Permission
from django.test import TestCase

from wagtail.actions.delete import DeleteAction, DeletePermissionError
from wagtail.log_actions import registry as log_registry
from wagtail.permission_policies import ModelPermissionPolicy
from wagtail.test.testapp.models import Advert, DraftStateModel, RevisableModel
from wagtail.test.utils import WagtailTestUtils


class TestDeleteAction(WagtailTestUtils, TestCase):
    def setUp(self):
        self.user = self.create_superuser(username="admin")

    def test_delete_plain_model(self):
        advert = Advert.objects.create(text="To delete", url="https://example.com")
        pk = advert.pk
        DeleteAction(advert, user=self.user).execute()

        self.assertFalse(Advert.objects.filter(pk=pk).exists())

        # Deleting clears the in-memory pk; restore it to look up the log entry.
        advert.pk = pk
        # The log entry is written and marked as deleted (so it survives the
        # object being removed).
        entries = log_registry.get_logs_for_instance(advert).filter(
            action="wagtail.delete"
        )
        self.assertEqual(entries.count(), 1)
        self.assertTrue(entries.first().deleted)

    def test_delete_revisable_model(self):
        # RevisableModel has no registered permission policy -> falls back to
        # ModelPermissionPolicy.
        instance = RevisableModel.objects.create(text="To delete")
        action = DeleteAction(instance, user=self.user)
        self.assertIsInstance(action.permission_policy, ModelPermissionPolicy)
        pk = instance.pk
        action.execute()
        self.assertFalse(RevisableModel.objects.filter(pk=pk).exists())

    def test_delete_draftstate_model(self):
        instance = DraftStateModel.objects.create(text="To delete")
        pk = instance.pk
        DeleteAction(instance, user=self.user).execute()
        self.assertFalse(DraftStateModel.objects.filter(pk=pk).exists())

    def test_log_action_override(self):
        advert = Advert.objects.create(text="To delete", url="https://example.com")
        pk = advert.pk
        DeleteAction(advert, user=self.user, log_action="wagtail.copy").execute()
        advert.pk = pk
        entries = log_registry.get_logs_for_instance(advert)
        self.assertEqual(entries.filter(action="wagtail.copy").count(), 1)
        self.assertEqual(entries.filter(action="wagtail.delete").count(), 0)

    def test_log_action_disabled(self):
        advert = Advert.objects.create(text="To delete", url="https://example.com")
        pk = advert.pk
        DeleteAction(advert, user=self.user, log_action=False).execute()
        self.assertFalse(Advert.objects.filter(pk=pk).exists())
        advert.pk = pk
        self.assertEqual(log_registry.get_logs_for_instance(advert).count(), 0)

    def test_permission_denied(self):
        advert = Advert.objects.create(text="Keep", url="https://example.com")
        user = self.create_user(username="editor")
        user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="tests", codename="change_advert"
            )
        )
        with self.assertRaises(DeletePermissionError):
            DeleteAction(advert, user=user).execute()
        # The object is not deleted.
        self.assertTrue(Advert.objects.filter(pk=advert.pk).exists())

    def test_permission_granted(self):
        advert = Advert.objects.create(text="Delete me", url="https://example.com")
        user = self.create_user(username="deleter")
        user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="tests", codename="delete_advert"
            )
        )
        DeleteAction(advert, user=user).execute()
        self.assertFalse(Advert.objects.filter(pk=advert.pk).exists())

    def test_skip_permission_checks(self):
        advert = Advert.objects.create(text="Delete me", url="https://example.com")
        user = self.create_user(username="powerless")
        DeleteAction(advert, user=user).execute(skip_permission_checks=True)
        self.assertFalse(Advert.objects.filter(pk=advert.pk).exists())
