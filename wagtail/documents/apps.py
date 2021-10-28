from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class WagtailDocsAppConfig(AppConfig):
    name = "wagtail.documents"
    label = "wagtaildocs"
    verbose_name = _("Wagtail documents")
    default_auto_field = "django.db.models.AutoField"

    def ready(self):
        from wagtail.documents.signal_handlers import register_signal_handlers

        register_signal_handlers()

        # Set up model forms to use AdminDocumentChooser for any ForeignKey to the document model
        from wagtail.admin.forms.models import FOREIGN_KEY_MODEL_OVERRIDES

        from . import get_document_model
        from .widgets import AdminDocumentChooser

        FOREIGN_KEY_MODEL_OVERRIDES[get_document_model()] = {
            "widget": AdminDocumentChooser
        }
