from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class WagtailTestsAppConfig(AppConfig):
    default_auto_field = "django.db.models.AutoField"
    name = "wagtail.test.testapp"
    label = "tests"
    verbose_name = _("Wagtail tests")

    def ready(self):
        from wagtail.models.reference_index import ReferenceIndex

        from .models import PageChooserModel

        ReferenceIndex.register_model(PageChooserModel)
