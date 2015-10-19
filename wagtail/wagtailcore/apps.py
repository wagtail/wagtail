from django.apps import AppConfig


class WagtailCoreAppConfig(AppConfig):
    name = 'wagtail.wagtailcore'
    label = 'wagtailcore'
    verbose_name = "Wagtail core"

    def ready(self):
        AppConfig.ready(self)

        from wagtail.wagtailcore.fields import configure_default_rich_text_editor
        configure_default_rich_text_editor()
