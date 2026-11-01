import swapper
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

from . import checks  # NOQA: F401


class WagtailAdminAppConfig(AppConfig):
    name = "wagtail.admin"
    label = "wagtailadmin"
    verbose_name = _("Wagtail admin")
    default_auto_field = "django.db.models.AutoField"

    def ready(self):
        from wagtail.admin.forms.pages import WagtailAdminPageForm
        from wagtail.admin.panels.page_utils import _get_page_edit_handler
        from wagtail.admin.signal_handlers import register_signal_handlers

        register_signal_handlers()
        Page = swapper.load_model("wagtailcore", "Page")
        Page.get_edit_handler = _get_page_edit_handler
        Page.base_form_class = WagtailAdminPageForm

        from wagtail.admin.telepath import widgets  # noqa: F401
