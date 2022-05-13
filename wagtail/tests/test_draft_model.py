from django.apps import apps
from django.core import checks
from django.db import models
from django.test import TestCase

from wagtail.models import DraftStateMixin, RevisionMixin


class TestDraftStateMixin(TestCase):
    def tearDown(self):
        # unregister DeprecatedStreamModel from the overall model registry
        # so that it doesn't break tests elsewhere
        for package in ("wagtailcore", "wagtail.tests"):
            try:
                for model in (
                    "draftstatewithoutrevisionmodel",
                    "draftstatewithrevisionmodel",
                ):
                    del apps.all_models[package][model]
            except KeyError:
                pass
        apps.clear_cache()

    def test_incorrect_model(self):
        class DraftStateWithoutRevisionModel(DraftStateMixin, models.Model):
            pass

        self.assertEqual(
            DraftStateWithoutRevisionModel.check(),
            [
                checks.Error(
                    "DraftStateMixin requires RevisionMixin to be applied.",
                    hint="Add RevisionMixin to the model's base classes before DraftStateMixin.",
                    obj=DraftStateWithoutRevisionModel,
                    id="wagtail.EXXX",
                )
            ],
        )

    def test_correct_model(self):
        class DraftStateWithRevisionModel(RevisionMixin, DraftStateMixin, models.Model):
            pass

        self.assertEqual(DraftStateWithRevisionModel.check(), [])
