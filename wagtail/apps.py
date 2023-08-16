import warnings

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

from wagtail.utils.deprecation import removed_in_next_version_warning


class WagtailAppConfig(AppConfig):
    name = "wagtail"
    label = "wagtailcore"
    verbose_name = _("Wagtail core")
    default_auto_field = "django.db.models.AutoField"

    def ready(self):

        # for model in apps.get_models():
        #     if issubclass(model, AbstractPage):
        #         ReferenceIndex.register_model(model)

        from wagtail.signal_handlers import register_signal_handlers

        register_signal_handlers()

        from wagtail import widget_adapters  # noqa: F401

        warnings.simplefilter("default", removed_in_next_version_warning)
