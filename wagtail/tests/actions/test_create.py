from unittest import mock

from django.contrib.auth.models import Permission
from django.forms.models import modelform_factory
from django.test import TestCase

from wagtail.actions.create import CreateAction, CreatePermissionError
from wagtail.log_actions import registry as log_registry
from wagtail.models import Revision
from wagtail.permission_policies import ModelPermissionPolicy
from wagtail.signals import published
from wagtail.test.testapp.models import (
    Advert,
    DraftStateModel,
    FullFeaturedSnippet,
    RevisableModel,
)
from wagtail.test.utils import WagtailTestUtils

AdvertForm = modelform_factory(Advert, fields=["text", "url", "tags"])
DraftStateModelForm = modelform_factory(DraftStateModel, fields=["text"])


class TestCreateAction(WagtailTestUtils, TestCase):
    def setUp(self):
        self.user = self.create_superuser(username="admin")

    def test_create_plain_model(self):
        advert = Advert(text="Test advert", url="https://example.com")
        result = CreateAction(advert, user=self.user).execute()

        self.assertEqual(result, advert)
        self.assertIsNotNone(advert.pk)
        self.assertTrue(Advert.objects.filter(pk=advert.pk).exists())

        # Exactly one log entry, with no revision.
        entries = log_registry.get_logs_for_instance(advert).filter(
            action="wagtail.create"
        )
        self.assertEqual(entries.count(), 1)
        self.assertIsNone(entries.first().revision)

    def test_create_revisable_model(self):
        # RevisableModel has no registered permission policy, so the action
        # should fall back to ModelPermissionPolicy.
        action = CreateAction(RevisableModel(text="Hello"), user=self.user)
        self.assertIsInstance(action.permission_policy, ModelPermissionPolicy)

        instance = action.execute()
        self.assertIsNotNone(instance.pk)

        # A revision is created and referenced by the log entry.
        self.assertEqual(Revision.objects.for_instance(instance).count(), 1)
        entries = log_registry.get_logs_for_instance(instance).filter(
            action="wagtail.create"
        )
        self.assertEqual(entries.count(), 1)
        self.assertIsNotNone(entries.first().revision)

    def test_create_draftstate_model_as_draft(self):
        instance = DraftStateModel(text="Draft")
        CreateAction(instance, user=self.user).execute()

        # Created as a draft: not live, but has a revision.
        self.assertFalse(instance.live)
        self.assertIsNotNone(instance.latest_revision)
        self.assertIsNone(instance.live_revision)

        # Only a create log entry, no publish.
        self.assertEqual(
            log_registry.get_logs_for_instance(instance)
            .filter(action="wagtail.create")
            .count(),
            1,
        )
        self.assertEqual(
            log_registry.get_logs_for_instance(instance)
            .filter(action="wagtail.publish")
            .count(),
            0,
        )

    def test_create_draftstate_model_and_publish(self):
        instance = DraftStateModel(text="Published")
        mock_handler = mock.MagicMock()
        published.connect(mock_handler)
        self.addCleanup(published.disconnect, mock_handler)
        CreateAction(instance, user=self.user, publish=True).execute()

        instance.refresh_from_db()
        self.assertTrue(instance.live)
        self.assertIsNotNone(instance.live_revision)

        # Both a create entry and a publish entry are written.
        self.assertEqual(
            log_registry.get_logs_for_instance(instance)
            .filter(action="wagtail.create")
            .count(),
            1,
        )
        self.assertEqual(
            log_registry.get_logs_for_instance(instance)
            .filter(action="wagtail.publish")
            .count(),
            1,
        )

        # The published signal fired once.
        self.assertEqual(mock_handler.call_count, 1)
        self.assertEqual(mock_handler.call_args.kwargs["instance"], instance)

    def test_create_orderable_model_sets_sort_order(self):
        first = FullFeaturedSnippet(text="First")
        CreateAction(first, user=self.user).execute()
        second = FullFeaturedSnippet(text="Second")
        CreateAction(second, user=self.user).execute()

        self.assertIsNotNone(first.sort_order)
        self.assertIsNotNone(second.sort_order)
        self.assertGreater(second.sort_order, first.sort_order)

    def test_create_orderable_model_keeps_explicit_sort_order(self):
        instance = FullFeaturedSnippet(text="Explicit", sort_order=42)
        CreateAction(instance, user=self.user).execute()
        self.assertEqual(instance.sort_order, 42)

    def test_create_with_form_saves_instance_and_m2m(self):
        form = AdvertForm(
            {"text": "From form", "url": "https://example.com", "tags": "alpha, beta"}
        )
        self.assertTrue(form.is_valid())

        action = CreateAction(form.instance, user=self.user, form=form)
        instance = action.execute()

        self.assertIsNotNone(instance.pk)
        instance.refresh_from_db()
        self.assertEqual(instance.text, "From form")
        # Many-to-many data is saved via the form.
        self.assertEqual(
            sorted(instance.tags.values_list("name", flat=True)),
            ["alpha", "beta"],
        )

    def test_create_draftstate_with_form_is_not_live(self):
        form = DraftStateModelForm({"text": "Draft from form"})
        self.assertTrue(form.is_valid())

        action = CreateAction(form.instance, user=self.user, form=form)
        instance = action.execute()

        instance.refresh_from_db()
        self.assertFalse(instance.live)
        self.assertEqual(instance.text, "Draft from form")
        self.assertIsNotNone(instance.latest_revision)

    def test_sort_order_field_none_disables_ordering(self):
        instance = FullFeaturedSnippet(text="No order")
        CreateAction(instance, user=self.user, sort_order_field=None).execute()
        self.assertIsNone(instance.sort_order)

    def test_sort_order_field_explicit_override(self):
        instance = FullFeaturedSnippet(text="Explicit field")
        CreateAction(instance, user=self.user, sort_order_field="sort_order").execute()
        self.assertIsNotNone(instance.sort_order)

    def test_revision_exposed_on_action(self):
        action = CreateAction(RevisableModel(text="Hello"), user=self.user)
        self.assertIsNone(action.revision)
        action.execute()
        self.assertIsNotNone(action.revision)
        self.assertEqual(action.revision, action.instance.latest_revision)

    def test_clean_defaults(self):
        # Non-draftstate: validated by default.
        self.assertTrue(CreateAction(RevisableModel(text="x"), user=self.user).clean)
        # Draftstate without publishing: not validated (drafts may be incomplete).
        self.assertFalse(CreateAction(DraftStateModel(text="x"), user=self.user).clean)
        # Draftstate with publishing: validated.
        self.assertTrue(
            CreateAction(DraftStateModel(text="x"), user=self.user, publish=True).clean
        )
        # Explicit override wins.
        self.assertTrue(
            CreateAction(DraftStateModel(text="x"), user=self.user, clean=True).clean
        )

    def test_log_action_override(self):
        advert = Advert(text="Custom log", url="https://example.com")
        CreateAction(advert, user=self.user, log_action="wagtail.copy").execute()
        self.assertEqual(
            log_registry.get_logs_for_instance(advert)
            .filter(action="wagtail.copy")
            .count(),
            1,
        )
        self.assertEqual(
            log_registry.get_logs_for_instance(advert)
            .filter(action="wagtail.create")
            .count(),
            0,
        )

    def test_log_action_disabled(self):
        advert = Advert(text="No log", url="https://example.com")
        CreateAction(advert, user=self.user, log_action=False).execute()
        self.assertEqual(log_registry.get_logs_for_instance(advert).count(), 0)
        # The object is still created.
        self.assertIsNotNone(advert.pk)

    def test_permission_denied(self):
        user = self.create_user(username="editor")
        user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="tests", codename="change_advert"
            )
        )
        advert = Advert(text="Denied", url="https://example.com")
        with self.assertRaises(CreatePermissionError):
            CreateAction(advert, user=user).execute()
        self.assertIsNone(advert.pk)

    def test_permission_granted(self):
        user = self.create_user(username="adder")
        user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="tests", codename="add_advert"
            )
        )
        advert = Advert(text="Allowed", url="https://example.com")
        CreateAction(advert, user=user).execute()
        self.assertIsNotNone(advert.pk)

    def test_skip_permission_checks(self):
        user = self.create_user(username="powerless")
        advert = Advert(text="Bypass", url="https://example.com")
        CreateAction(advert, user=user).execute(skip_permission_checks=True)
        self.assertIsNotNone(advert.pk)

    def test_no_user_skips_permission_checks(self):
        advert = Advert(text="No user", url="https://example.com")
        CreateAction(advert).execute()
        self.assertIsNotNone(advert.pk)
