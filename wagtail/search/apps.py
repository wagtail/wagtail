from django.utils.translation import gettext_lazy as _
from modelsearch.apps import ModelSearchAppConfig

from . import checks  # NOQA: F401


class WagtailSearchAppConfig(ModelSearchAppConfig):
    name = "wagtail.search"
    label = "wagtailsearch"
    verbose_name = _("Wagtail search")
    backend_setting_name = "WAGTAILSEARCH_BACKENDS"
    default = True
