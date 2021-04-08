from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class WagtailTestsAppConfig(AppConfig):
    default_auto_field = 'django.db.models.AutoField'
    name = 'wagtail.tests.testapp'
    label = 'tests'
    verbose_name = _("Wagtail tests")
