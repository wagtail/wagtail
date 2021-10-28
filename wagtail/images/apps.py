from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

from . import checks  # NOQA


class WagtailImagesAppConfig(AppConfig):
    name = "wagtail.images"
    label = "wagtailimages"
    verbose_name = _("Wagtail images")
    default_auto_field = "django.db.models.AutoField"

    def ready(self):
        from wagtail.images.signal_handlers import register_signal_handlers

        register_signal_handlers()

        # Set up model forms to use AdminImageChooser for any ForeignKey to the image model
        from wagtail.admin.forms.models import FOREIGN_KEY_MODEL_OVERRIDES

        from . import get_image_model
        from .widgets import AdminImageChooser

        FOREIGN_KEY_MODEL_OVERRIDES[get_image_model()] = {"widget": AdminImageChooser}
