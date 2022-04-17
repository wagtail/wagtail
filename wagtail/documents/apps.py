from django.apps import AppConfig
from django.db.models import ForeignKey
from django.utils.translation import gettext_lazy as _

from . import get_document_model


class WagtailDocsAppConfig(AppConfig):
    name = "wagtail.documents"
    label = "wagtaildocs"
    verbose_name = _("Wagtail documents")
    default_auto_field = "django.db.models.AutoField"

    def ready(self):
        from wagtail.documents.signal_handlers import register_signal_handlers

        register_signal_handlers()

        # Set up model forms to use AdminDocumentChooser for any ForeignKey to the document model
        from wagtail.admin.forms.models import register_form_field_override

        from .widgets import AdminDocumentChooser

        Document = get_document_model()
        register_form_field_override(
            ForeignKey, to=Document, override={"widget": AdminDocumentChooser}
        )
