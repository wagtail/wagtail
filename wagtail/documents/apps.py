from django.apps import AppConfig
from django.db.models import ForeignKey
from django.utils.translation import gettext_lazy as _

from . import get_document_model, get_permission_policy


class WagtailDocsAppConfig(AppConfig):
    name = "wagtail.documents"
    label = "wagtaildocs"
    verbose_name = _("Wagtail documents")
    default_auto_field = "django.db.models.AutoField"

    def ready(self):
        from wagtail.documents.signal_handlers import register_signal_handlers
        from wagtail.permissions import register_permission_policy

        Document = get_document_model()
        register_permission_policy(Document, get_permission_policy())
        register_signal_handlers()

        from wagtail.admin.ui.fields import register_display_class

        from .components import DocumentDisplay

        register_display_class(ForeignKey, to=Document, display_class=DocumentDisplay)

        from wagtail.models.reference_index import ReferenceIndex

        ReferenceIndex.register_model(Document)

        from .api.v3.registry import register_content_types

        register_content_types()

        from wagtail.api.v3.api import api

        from .api.v3.router import router

        api.add_router("/documents/", router)
