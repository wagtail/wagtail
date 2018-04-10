from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class WagtailSearchPromotionsAppConfig(AppConfig):
    name = 'wagtail.contrib.search_promotions'
    label = 'wagtailsearchpromotions'
    verbose_name = _("Wagtail search promotions")
