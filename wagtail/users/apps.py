from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class WagtailUsersAppConfig(AppConfig):
    name = 'wagtail.users'
    label = 'wagtailusers'
    verbose_name = _("Wagtail users")
