from django.apps import apps
from django.core import checks
from django.db import models
from django.test import TestCase

from wagtail.models import DraftStateMixin, LockableMixin, RevisionMixin, WorkflowMixin


class TestWorkflowMixin(TestCase):
    def tearDown(self):
        # Unregister the models from the overall model registry
        # so that it doesn't break tests elsewhere.
        # We can probably replace this with Django's @isolate_apps decorator.
        for package in ("wagtailcore", "wagtail.tests"):
            try:
                for model in (
                    "workflowwithoutrevisionmodel",
                    "workflowwithoutdraftstatemodel",
                    "workflowincorrectordermodel1",
                    "workflowincorrectordermodel2",
                    "correctworkflowmodel",
                    "correctnotlockableworkflowmodel",
                ):
                    del apps.all_models[package][model]
            except KeyError:
                pass
        apps.clear_cache()

    def test_missing_revision_or_draftstate_mixins(self):
        error = checks.Error(
            "WorkflowMixin requires DraftStateMixin and RevisionMixin (in that order).",
            hint=(
                "Make sure your model's inheritance order is as follows: "
                "WorkflowMixin, DraftStateMixin, RevisionMixin."
            ),
            id="wagtailcore.E006",
        )

        class WorkflowWithoutRevisionModel(WorkflowMixin, models.Model):
            pass

        class WorkflowWithoutDraftStateModel(
            WorkflowMixin, RevisionMixin, models.Model
        ):
            pass

        for model in (WorkflowWithoutRevisionModel, WorkflowWithoutDraftStateModel):
            with self.subTest(model=model):
                error.obj = model
                self.assertEqual(model.check(), [error])

    def test_incorrect_mixins_order(self):
        error = checks.Error(
            "WorkflowMixin requires DraftStateMixin and RevisionMixin (in that order).",
            hint=(
                "Make sure your model's inheritance order is as follows: "
                "WorkflowMixin, DraftStateMixin, RevisionMixin."
            ),
            id="wagtailcore.E006",
        )

        class WorkflowIncorrectOrderModel1(
            DraftStateMixin, WorkflowMixin, RevisionMixin, LockableMixin, models.Model
        ):
            pass

        class WorkflowIncorrectOrderModel2(
            DraftStateMixin, RevisionMixin, WorkflowMixin, models.Model
        ):
            pass

        for model in (WorkflowIncorrectOrderModel1, WorkflowIncorrectOrderModel2):
            with self.subTest(model=model):
                error.obj = model
                self.assertEqual(model.check(), [error])

    def test_correct_mixins_order(self):
        class CorrectWorkflowModel(
            WorkflowMixin, DraftStateMixin, LockableMixin, RevisionMixin, models.Model
        ):
            pass

        class CorrectNotLockableWorkflowModel(
            WorkflowMixin, DraftStateMixin, RevisionMixin, models.Model
        ):
            pass

        for model in (CorrectWorkflowModel, CorrectNotLockableWorkflowModel):
            with self.subTest(model=model):
                self.assertEqual(model.check(), [])
