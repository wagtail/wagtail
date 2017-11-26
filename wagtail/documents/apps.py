from django.apps import AppConfig


class WagtailDocsAppConfig(AppConfig):
    name = 'wagtail.documents'
    label = 'wagtaildocs'
    verbose_name = "Wagtail documents"

    def ready(self):
        from wagtail.documents.signal_handlers import register_signal_handlers
        register_signal_handlers()
