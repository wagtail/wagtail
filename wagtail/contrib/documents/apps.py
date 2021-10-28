from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class WagtailDocsAppConfig(AppConfig):
    name = 'wagtail.contrib.documents'
    label = 'wagtaildocs'
    verbose_name = _("Wagtail documents")
    default_auto_field = 'django.db.models.AutoField'

    def ready(self):
        from wagtail.contrib.documents.signal_handlers import register_signal_handlers
        register_signal_handlers()
