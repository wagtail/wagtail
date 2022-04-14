from django.conf import settings
from django.shortcuts import get_object_or_404

from wagtail.models import Locale, TranslatableMixin


class LocaleMixin:
    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.locale = self.get_locale()

    def get_translations_context(self):
        return []

    def get_locale(self):
        i18n_enabled = getattr(settings, "WAGTAIL_I18N_ENABLED", False)
        if hasattr(self, "model"):
            i18n_enabled = i18n_enabled and issubclass(self.model, TranslatableMixin)

        if not i18n_enabled:
            return None

        selected_locale = self.request.GET.get("locale")
        if selected_locale:
            return get_object_or_404(Locale, language_code=selected_locale)
        return Locale.get_default()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if not self.locale:
            return context

        context["locale"] = self.locale
        context["translations"] = self.get_translations_context()
        return context
