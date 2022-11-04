from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class WagtailSnippetsAppConfig(AppConfig):
    name = "wagtail.snippets"
    label = "wagtailsnippets"
    verbose_name = _("Wagtail snippets")

    def ready(self):
        # Register all snippets for which register_snippet was called up to this point -
        # these registrations had to be deferred as we could not guarantee that models were
        # fully loaded at that point (but now they are).
        from .models import register_deferred_snippets

        register_deferred_snippets()
