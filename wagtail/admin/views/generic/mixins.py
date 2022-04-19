from django.conf import settings
from django.forms import Media
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

        if hasattr(self, "object") and self.object:
            return self.object.locale

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


class PanelMixin:
    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.panel = self.get_panel()

    def get_panel(self):
        return None

    def get_bound_panel(self, form):
        if not self.panel:
            return None
        return self.panel.get_bound_panel(
            request=self.request, instance=form.instance, form=form
        )

    def get_form_class(self):
        if not self.panel:
            return super().get_form_class()
        return self.panel.get_form_class()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        form = context.get("form")
        panel = self.get_bound_panel(form)

        media = context.get("media", Media())
        if form:
            media += form.media
        if panel:
            media += panel.media

        context.update(
            {
                "panel": panel,
                "media": media,
            }
        )

        return context
