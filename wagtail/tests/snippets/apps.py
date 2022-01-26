from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class WagtailSnippetsTestsAppConfig(AppConfig):
    default_auto_field = 'django.db.models.AutoField'
    name = 'wagtail.tests.snippets'
    label = 'snippetstests'
    verbose_name = _("Wagtail snippets tests")
