from django.apps import AppConfig, apps
from django.utils.translation import gettext_lazy as _


class WagtailAppConfig(AppConfig):
    name = "wagtail"
    label = "wagtailcore"
    verbose_name = _("Wagtail core")
    default_auto_field = "django.db.models.AutoField"

    def ready(self):
        from wagtail.documents.models import AbstractDocument
        from wagtail.images.models import AbstractImage
        from wagtail.models import AbstractPage
        from wagtail.models.reference_index import ReferenceIndex

        for model in apps.get_models():
            if (
                issubclass(model, AbstractPage)
                or issubclass(model, AbstractImage)
                or issubclass(model, AbstractDocument)
            ):
                ReferenceIndex.register_model(model)

        from wagtail.signal_handlers import register_signal_handlers

        register_signal_handlers()

        from wagtail import widget_adapters  # noqa
