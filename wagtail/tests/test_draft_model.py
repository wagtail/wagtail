from django.apps import apps
from django.core import checks
from django.db import models
from django.test import TestCase

from wagtail.models import DraftStateMixin, RevisionMixin


class TestDraftStateMixin(TestCase):
    def tearDown(self):
        # Unregister the models from the overall model registry
        # so that it doesn't break tests elsewhere.
        # We can probably replace this with Django's @isolate_apps decorator.
        for package in ("wagtailcore", "wagtail.tests"):
            try:
                for model in (
                    "draftstatewithoutrevisionmodel",
                    "draftstateincorrectrevisionmodel",
                    "draftstatewithrevisionmodel",
                ):
                    del apps.all_models[package][model]
            except KeyError:
                pass
        apps.clear_cache()

    def test_missing_revision_mixin(self):
        class DraftStateWithoutRevisionModel(DraftStateMixin, models.Model):
            pass

        self.assertEqual(
            DraftStateWithoutRevisionModel.check(),
            [
                checks.Error(
                    "DraftStateMixin requires RevisionMixin to be applied after DraftStateMixin.",
                    hint="Add RevisionMixin to the model's base classes after DraftStateMixin.",
                    obj=DraftStateWithoutRevisionModel,
                    id="wagtailcore.E004",
                )
            ],
        )

    def test_incorrect_revision_mixin_order(self):
        class DraftStateIncorrectRevisionModel(
            RevisionMixin, DraftStateMixin, models.Model
        ):
            pass

        self.assertEqual(
            DraftStateIncorrectRevisionModel.check(),
            [
                checks.Error(
                    "DraftStateMixin requires RevisionMixin to be applied after DraftStateMixin.",
                    hint="Add RevisionMixin to the model's base classes after DraftStateMixin.",
                    obj=DraftStateIncorrectRevisionModel,
                    id="wagtailcore.E004",
                )
            ],
        )

    def test_correct_model(self):
        class DraftStateWithRevisionModel(DraftStateMixin, RevisionMixin, models.Model):
            pass

        self.assertEqual(DraftStateWithRevisionModel.check(), [])
