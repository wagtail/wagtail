from django.db import models
from django.test import TestCase
from modelcluster.contrib.taggit import ClusterTaggableManager
from modelcluster.fields import ParentalManyToManyField
from modelcluster.models import ClusterableModel
from taggit.managers import TaggableManager

from wagtail.checks import clusterable_model_field_check
from wagtail.models import RevisionMixin


class TestClusterableModelFieldCheck(TestCase):
    """
    Tests for the system check that warns when revision-enabled ClusterableModels
    use standard ManyToManyField or TaggableManager instead of their
    modelcluster-aware counterparts.
    """

    def _get_errors_for_model(self, model):
        """Helper to extract warnings for a specific model from the check output."""
        return [e for e in clusterable_model_field_check(None) if e.obj is model]

    # --- ManyToManyField checks ---

    def test_m2m_on_revision_clusterable_model_warns(self):
        """A plain ManyToManyField on a RevisionMixin + ClusterableModel should warn."""

        class BadM2MModel(RevisionMixin, ClusterableModel):
            m2m = models.ManyToManyField("auth.Group")

            class Meta:
                app_label = "wagtailcore"

        errors = self._get_errors_for_model(BadM2MModel)

        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].id, "wagtailcore.W002")
        self.assertIn("ManyToManyField", errors[0].msg)
        self.assertIn("BadM2MModel", errors[0].msg)
        self.assertIn("m2m", errors[0].msg)
        self.assertIn("ParentalManyToManyField", errors[0].hint)

    def test_parental_m2m_does_not_warn(self):
        """A ParentalManyToManyField should not trigger any warning."""

        class GoodM2MModel(RevisionMixin, ClusterableModel):
            m2m = ParentalManyToManyField("auth.Group")

            class Meta:
                app_label = "wagtailcore"

        errors = self._get_errors_for_model(GoodM2MModel)
        self.assertEqual(len(errors), 0)

    # --- TaggableManager checks ---

    def test_taggable_manager_on_revision_clusterable_model_warns(self):
        """A plain TaggableManager on a RevisionMixin + ClusterableModel should warn."""

        class BadTagModel(RevisionMixin, ClusterableModel):
            tags = TaggableManager()

            class Meta:
                app_label = "wagtailcore"

        errors = self._get_errors_for_model(BadTagModel)

        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].id, "wagtailcore.W003")
        self.assertIn("TaggableManager", errors[0].msg)
        self.assertIn("BadTagModel", errors[0].msg)
        self.assertIn("tags", errors[0].msg)
        self.assertIn("ClusterTaggableManager", errors[0].hint)

    def test_cluster_taggable_manager_does_not_warn(self):
        """A ClusterTaggableManager should not trigger any warning."""

        class GoodTagModel(RevisionMixin, ClusterableModel):
            tags = ClusterTaggableManager()

            class Meta:
                app_label = "wagtailcore"

        errors = self._get_errors_for_model(GoodTagModel)
        self.assertEqual(len(errors), 0)

    # --- Condition scope checks ---

    def test_clusterable_without_revision_mixin_does_not_warn(self):
        """
        A ClusterableModel WITHOUT RevisionMixin should not warn, even with
        plain TaggableManager or ManyToManyField. Per Wagtail docs, plain
        TaggableManager is valid when RevisionMixin is not applied.
        """

        class NonRevisionModel(ClusterableModel):
            tags = TaggableManager()
            m2m = models.ManyToManyField("auth.Group")

            class Meta:
                app_label = "wagtailcore"

        errors = self._get_errors_for_model(NonRevisionModel)
        self.assertEqual(len(errors), 0)

    # --- Duplicate/inheritance checks ---

    def test_inherited_field_does_not_produce_duplicate_warning(self):
        """
        If a parent model declares a bad field, only the parent should get the
        warning. Child models that inherit the field should not produce
        duplicate warnings.
        """

        class ParentModel(RevisionMixin, ClusterableModel):
            m2m = models.ManyToManyField("auth.Group")

            class Meta:
                app_label = "wagtailcore"

        class ChildModel(ParentModel):
            class Meta:
                app_label = "wagtailcore"

        parent_errors = self._get_errors_for_model(ParentModel)
        child_errors = self._get_errors_for_model(ChildModel)

        self.assertEqual(len(parent_errors), 1)
        self.assertEqual(len(child_errors), 0)

    # --- Combined checks ---

    def test_model_with_both_bad_fields(self):
        """A model with both a bad M2M and a bad TaggableManager gets two warnings."""

        class DoubleBadModel(RevisionMixin, ClusterableModel):
            m2m = models.ManyToManyField("auth.Group")
            tags = TaggableManager()

            class Meta:
                app_label = "wagtailcore"

        errors = self._get_errors_for_model(DoubleBadModel)

        self.assertEqual(len(errors), 2)
        ids = {e.id for e in errors}
        self.assertEqual(ids, {"wagtailcore.W002", "wagtailcore.W003"})

    def test_model_with_all_correct_fields(self):
        """A model using all correct field types should produce zero warnings."""

        class AllGoodModel(RevisionMixin, ClusterableModel):
            m2m = ParentalManyToManyField("auth.Group")
            tags = ClusterTaggableManager()

            class Meta:
                app_label = "wagtailcore"

        errors = self._get_errors_for_model(AllGoodModel)
        self.assertEqual(len(errors), 0)

    # --- obj value ---

    def test_warning_obj_is_model_class(self):
        """The warning's obj attribute should be the model class, not the field."""

        class ObjCheckModel(RevisionMixin, ClusterableModel):
            m2m = models.ManyToManyField("auth.Group")

            class Meta:
                app_label = "wagtailcore"

        errors = self._get_errors_for_model(ObjCheckModel)
        self.assertEqual(len(errors), 1)
        self.assertIs(errors[0].obj, ObjCheckModel)
