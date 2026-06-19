from unittest import mock

from django.contrib.auth.models import Permission
from django.forms.models import modelform_factory
from django.test import TestCase

from wagtail.actions.edit import EditAction, EditPermissionError
from wagtail.log_actions import registry as log_registry
from wagtail.models import Revision
from wagtail.permission_policies import ModelPermissionPolicy
from wagtail.signals import published
from wagtail.test.testapp.models import Advert, DraftStateModel, RevisableModel
from wagtail.test.utils import WagtailTestUtils

AdvertForm = modelform_factory(Advert, fields=["text", "url", "tags"])
DraftStateModelForm = modelform_factory(DraftStateModel, fields=["text"])


class TestEditAction(WagtailTestUtils, TestCase):
    def setUp(self):
        self.user = self.create_superuser(username="admin")

    def test_edit_plain_model(self):
        advert = Advert.objects.create(text="Original", url="https://example.com")
        advert.text = "Edited"
        result = EditAction(advert, user=self.user).execute()

        self.assertEqual(result, advert)
        advert.refresh_from_db()
        self.assertEqual(advert.text, "Edited")

        entries = log_registry.get_logs_for_instance(advert).filter(
            action="wagtail.edit"
        )
        self.assertEqual(entries.count(), 1)
        self.assertIsNone(entries.first().revision)

    def test_edit_revisable_model(self):
        instance = RevisableModel.objects.create(text="Original")
        instance.text = "Edited"
        action = EditAction(instance, user=self.user)
        # No registered permission policy -> ModelPermissionPolicy fallback.
        self.assertIsInstance(action.permission_policy, ModelPermissionPolicy)
        action.execute()

        self.assertEqual(Revision.objects.for_instance(instance).count(), 1)
        entries = log_registry.get_logs_for_instance(instance).filter(
            action="wagtail.edit"
        )
        self.assertEqual(entries.count(), 1)
        self.assertIsNotNone(entries.first().revision)

    def test_edit_draftstate_model_as_draft(self):
        # Create an unpublished draft to edit.
        instance = DraftStateModel.objects.create(text="Original", live=False)
        instance.text = "Draft edit"
        EditAction(instance, user=self.user).execute()

        # Editing as a draft does not publish the object.
        instance.refresh_from_db()
        self.assertFalse(instance.live)
        self.assertEqual(
            log_registry.get_logs_for_instance(instance)
            .filter(action="wagtail.edit")
            .count(),
            1,
        )
        self.assertEqual(
            log_registry.get_logs_for_instance(instance)
            .filter(action="wagtail.publish")
            .count(),
            0,
        )
        # The new content lives in the latest revision, not the live object.
        self.assertEqual(
            instance.latest_revision.content["text"],
            "Draft edit",
        )

    def test_edit_draftstate_model_and_publish(self):
        instance = DraftStateModel.objects.create(text="Original")
        instance.text = "Published edit"
        mock_handler = mock.MagicMock()
        published.connect(mock_handler)
        self.addCleanup(published.disconnect, mock_handler)
        EditAction(instance, user=self.user, publish=True).execute()

        instance.refresh_from_db()
        self.assertTrue(instance.live)
        self.assertEqual(instance.text, "Published edit")
        self.assertEqual(
            log_registry.get_logs_for_instance(instance)
            .filter(action="wagtail.edit")
            .count(),
            1,
        )
        self.assertEqual(
            log_registry.get_logs_for_instance(instance)
            .filter(action="wagtail.publish")
            .count(),
            1,
        )
        self.assertEqual(mock_handler.call_count, 1)

    def test_edit_with_overwrite_revision(self):
        instance = RevisableModel.objects.create(text="Original")
        instance.text = "First revision"
        EditAction(instance, user=self.user).execute()
        first_revision = instance.latest_revision

        instance.text = "Overwritten"
        EditAction(
            instance, user=self.user, overwrite_revision=first_revision
        ).execute()

        # The revision was overwritten rather than a new one created.
        self.assertEqual(Revision.objects.for_instance(instance).count(), 1)
        instance.refresh_from_db()
        self.assertEqual(instance.latest_revision.content["text"], "Overwritten")

    def test_edit_with_form_saves_instance_and_m2m(self):
        advert = Advert.objects.create(text="Original", url="https://example.com")
        form = AdvertForm(
            {"text": "Edited", "url": "https://example.com", "tags": "alpha, beta"},
            instance=advert,
        )
        self.assertTrue(form.is_valid())

        EditAction(advert, user=self.user, form=form).execute()

        advert.refresh_from_db()
        self.assertEqual(advert.text, "Edited")
        self.assertEqual(
            sorted(advert.tags.values_list("name", flat=True)),
            ["alpha", "beta"],
        )

    def test_edit_live_draftstate_with_form_leaves_live_version_untouched(self):
        instance = DraftStateModel.objects.create(text="Live", live=True)
        form = DraftStateModelForm({"text": "Draft edit"}, instance=instance)
        self.assertTrue(form.is_valid())

        EditAction(instance, user=self.user, form=form).execute()

        # The live row is unchanged; the edit only created a new revision.
        instance.refresh_from_db()
        self.assertTrue(instance.live)
        self.assertEqual(instance.text, "Live")
        self.assertEqual(instance.latest_revision.content["text"], "Draft edit")

    def test_content_changed_derived_from_form(self):
        advert = Advert.objects.create(text="Original", url="https://example.com")
        # An unchanged form -> content_changed is False.
        unchanged = AdvertForm(
            {"text": "Original", "url": "https://example.com"}, instance=advert
        )
        self.assertTrue(unchanged.is_valid())
        self.assertFalse(
            EditAction(advert, user=self.user, form=unchanged).content_changed
        )

        # A changed form -> content_changed is True.
        changed = AdvertForm(
            {"text": "Different", "url": "https://example.com"}, instance=advert
        )
        self.assertTrue(changed.is_valid())
        self.assertTrue(
            EditAction(advert, user=self.user, form=changed).content_changed
        )

    def test_content_changed_without_form_assumes_changed(self):
        advert = Advert.objects.create(text="Original", url="https://example.com")
        self.assertTrue(EditAction(advert, user=self.user).content_changed)

    def test_revision_exposed_on_action(self):
        instance = RevisableModel.objects.create(text="Original")
        instance.text = "Edited"
        action = EditAction(instance, user=self.user)
        self.assertIsNone(action.revision)
        action.execute()
        self.assertIsNotNone(action.revision)
        self.assertEqual(action.revision, instance.latest_revision)

    def test_clean_defaults(self):
        # Non-draftstate: validated by default.
        self.assertTrue(EditAction(RevisableModel(text="x"), user=self.user).clean)
        # Draftstate without publishing: not validated.
        self.assertFalse(EditAction(DraftStateModel(text="x"), user=self.user).clean)
        # Draftstate with publishing: validated.
        self.assertTrue(
            EditAction(DraftStateModel(text="x"), user=self.user, publish=True).clean
        )
        # Explicit override wins.
        self.assertFalse(
            EditAction(RevisableModel(text="x"), user=self.user, clean=False).clean
        )

    def test_log_action_override(self):
        advert = Advert.objects.create(text="Original", url="https://example.com")
        advert.text = "Renamed"
        EditAction(advert, user=self.user, log_action="wagtail.rename").execute()
        self.assertEqual(
            log_registry.get_logs_for_instance(advert)
            .filter(action="wagtail.rename")
            .count(),
            1,
        )
        self.assertEqual(
            log_registry.get_logs_for_instance(advert)
            .filter(action="wagtail.edit")
            .count(),
            0,
        )

    def test_log_action_disabled(self):
        advert = Advert.objects.create(text="Original", url="https://example.com")
        advert.text = "No log"
        EditAction(advert, user=self.user, log_action=False).execute()
        self.assertEqual(log_registry.get_logs_for_instance(advert).count(), 0)
        advert.refresh_from_db()
        self.assertEqual(advert.text, "No log")

    def test_permission_denied(self):
        advert = Advert.objects.create(text="Original", url="https://example.com")
        user = self.create_user(username="adder")
        user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="tests", codename="add_advert"
            )
        )
        advert.text = "Denied"
        with self.assertRaises(EditPermissionError):
            EditAction(advert, user=user).execute()

    def test_permission_granted(self):
        advert = Advert.objects.create(text="Original", url="https://example.com")
        user = self.create_user(username="editor")
        user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="tests", codename="change_advert"
            )
        )
        advert.text = "Allowed"
        EditAction(advert, user=user).execute()
        advert.refresh_from_db()
        self.assertEqual(advert.text, "Allowed")

    def test_skip_permission_checks(self):
        advert = Advert.objects.create(text="Original", url="https://example.com")
        user = self.create_user(username="powerless")
        advert.text = "Bypass"
        EditAction(advert, user=user).execute(skip_permission_checks=True)
        advert.refresh_from_db()
        self.assertEqual(advert.text, "Bypass")
