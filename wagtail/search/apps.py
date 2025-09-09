from django.utils.translation import gettext_lazy as _
from wagtailsearch.apps import WagtailSearchAppConfig as _WagtailSearchAppConfig


class WagtailSearchAppConfig(_WagtailSearchAppConfig):
    name = "wagtail.search"
    label = "wagtailsearch"
    verbose_name = _("Wagtail search")
    default = True
