from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class WagtailSnippetsAppConfig(AppConfig):
    name = 'wagtail.snippets'
    label = 'wagtailsnippets'
    verbose_name = _("Wagtail snippets")
