from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class WagtailTestsAppConfig(AppConfig):
    default_auto_field = "django.db.models.AutoField"
    name = "wagtail.test.testapp"
    label = "tests"
    verbose_name = _("Wagtail tests")

    def ready(self):
        from wagtail.models.reference_index import ReferenceIndex
        from wagtail.permissions import register_permission_policy

        from . import models

        ReferenceIndex.register_model(models.PageChooserModel)
        models_with_default_permissions = [
            # Snippets
            models.Advert,
            models.AdvertWithCustomPrimaryKey,
            models.AdvertWithCustomUUIDPrimaryKey,
            models.AdvertWithTabbedInterface,
            models.ModelWithCustomManager,
            models.DraftStateCustomPrimaryKeyModel,
            models.PreviewableModel,
            models.CustomPreviewSizesModel,
            models.MultiPreviewModesModel,
            models.NonPreviewableModel,
            models.LockableModel,
            models.RevisableCluster,
            models.CustomPermissionModel,
            models.DraftStateModel,
            models.ModeratedModel,
            models.RevisableModel,
            models.RevisableChildModel,
            models.VariousOnDeleteModel,
            models.SnippetChooserModel,
            # Models registered with ModelViewSet
            models.JSONStreamModel,
            models.JSONMinMaxCountStreamModel,
            models.JSONBlockCountsStreamModel,
            models.FeatureCompleteToy,
            models.SearchTestModel,
        ]
        for model in models_with_default_permissions:
            register_permission_policy(model)
