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

        Document = get_document_model()

        from wagtail.admin.ui.fields import register_display_class

        from .components import DocumentDisplay

        register_display_class(ForeignKey, to=Document, display_class=DocumentDisplay)

        from wagtail.models.reference_index import ReferenceIndex

        ReferenceIndex.register_model(Document)
