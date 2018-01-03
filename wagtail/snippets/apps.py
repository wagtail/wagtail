from django.apps import AppConfig

from . import checks  # NOQA


class WagtailSnippetsAppConfig(AppConfig):
    name = 'wagtail.snippets'
    label = 'wagtailsnippets'
    verbose_name = "Wagtail snippets"
