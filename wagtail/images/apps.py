from django.apps import AppConfig
from django.db.models import ForeignKey
from django.utils.translation import gettext_lazy as _

from . import checks, get_image_model  # NOQA
from .signal_handlers import register_signal_handlers


class WagtailImagesAppConfig(AppConfig):
    name = "wagtail.images"
    label = "wagtailimages"
    verbose_name = _("Wagtail images")
    default_auto_field = "django.db.models.AutoField"

    def ready(self):
        register_signal_handlers()

        # Set up model forms to use AdminImageChooser for any ForeignKey to the image model
        from wagtail.admin.forms.models import register_form_field_override

        from .widgets import AdminImageChooser

        Image = get_image_model()
        register_form_field_override(
            ForeignKey, to=Image, override={"widget": AdminImageChooser}
        )

        # Set up image ForeignKeys to use ImageFieldComparison as the comparison class
        # when comparing page revisions
        from wagtail.admin.compare import register_comparison_class

        from .edit_handlers import ImageFieldComparison

        register_comparison_class(
            ForeignKey, to=Image, comparison_class=ImageFieldComparison
        )
