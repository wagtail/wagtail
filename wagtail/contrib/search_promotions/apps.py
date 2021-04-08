from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class WagtailSearchPromotionsAppConfig(AppConfig):
    name = 'wagtail.contrib.search_promotions'
    label = 'wagtailsearchpromotions'
    verbose_name = _("Wagtail search promotions")
    default_auto_field = 'django.db.models.AutoField'
