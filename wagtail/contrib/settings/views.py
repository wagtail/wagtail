from functools import lru_cache

from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.utils.text import capfirst
from django.utils.translation import gettext as _

from wagtail.admin import messages
from wagtail.admin.panels import ObjectList, extract_panel_definitions_from_model_class
from wagtail.admin.views import generic
from wagtail.models import Locale, Site
from wagtail.permission_policies import ModelPermissionPolicy

from .models import AbstractGenericSetting, AbstractSiteSetting
from .registry import registry
from .utils import get_edit_setting_url, get_locale_for


def get_model_from_url_params(app_name, model_name):
    """
    retrieve a content type from an app_name / model_name combo.
    Throw Http404 if not a valid setting type
    """
    model = registry.get_by_natural_key(app_name, model_name)
    if model is None:
        raise Http404
    return model


@lru_cache()
def get_setting_edit_handler(model):
    if hasattr(model, "edit_handler"):
        edit_handler = model.edit_handler
    else:
        if issubclass(model, AbstractSiteSetting):
            panels = extract_panel_definitions_from_model_class(model, ["site"])
        elif issubclass(model, AbstractGenericSetting):
            panels = extract_panel_definitions_from_model_class(model)
        else:
            raise NotImplementedError

        edit_handler = ObjectList(panels)
    return edit_handler.bind_to_model(model)


def redirect_to_relevant_instance(request, app_name, model_name):
    model = get_model_from_url_params(app_name, model_name)

    if issubclass(model, AbstractSiteSetting):
        # Redirect the user to the edit page for the current site
        # (or the current request does not correspond to a site, the first site in the list)
        site_request = Site.find_for_request(request)
        site = site_request or Site.objects.first()
        if site:
            locale = get_locale_for(request=request, model=model)
            return redirect(
                get_edit_setting_url(app_name, model_name, site.pk, locale=locale)
            )
        else:
            messages.error(
                request,
                _("This setting could not be opened because there is no site defined."),
            )
            return redirect("wagtailadmin_home")
    elif issubclass(model, AbstractGenericSetting):
        return edit_generic_settings(request, app_name, model_name, model)
    else:
        raise NotImplementedError


class EditView(generic.EditView):
    template_name = "wagtailsettings/edit.html"
    site = None

    def setup(self, request, app_name, model_name, model, *args, **kwargs):
        self.app_name = app_name
        self.model_name = model_name
        self.model = model
        self.permission_policy = ModelPermissionPolicy(self.model)
        super().setup(request, *args, **kwargs)

    def get_locale(self):
        return get_locale_for(request=self.request, model=self.model)

    def get_panel(self):
        return get_setting_edit_handler(self.model)

    def get_success_buttons(self):
        return []

    def get_success_url(self):
        return self.get_edit_url()

    def get_success_message(self):
        return _("%(setting_type)s updated.") % {
            "setting_type": capfirst(self.model._meta.verbose_name),
            "instance": self.object,
        }

    def get_error_message(self):
        return _("The setting could not be saved due to errors.")

    def get_form_kwargs(self):
        return {
            **super().get_form_kwargs(),
            "instance": self.object,
            "for_user": self.request.user,
        }

    def save_instance(self):
        return self.form.save()

    def get_translations(self, all_locales):
        raise NotImplementedError

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.locale:
            all_locales = Locale.objects.annotate_default_language().all()
            context.update(
                {
                    "all_locales": all_locales,
                    "translations": self.get_translations(all_locales),
                }
            )

        context.update(
            {
                "site": self.site,
                "setting_type_name": self.model._meta.verbose_name,
            }
        )
        return context


class EditSiteSettingsView(EditView):
    def get_object(self):
        self.site = get_object_or_404(Site, pk=self.kwargs["pk"])
        return self.model.for_site(self.site, locale=self.locale)

    def _get_edit_url(self, site_pk, locale):
        return get_edit_setting_url(
            self.app_name, self.model_name, site_pk, locale=locale
        )

    def get_edit_url(self):
        return self._get_edit_url(self.site.pk, self.locale)

    def get_site_choices(self):
        current_locale = self.locale

        return [
            {
                "site": site_choice,
                "url": self._get_edit_url(site_choice.pk, current_locale),
            }
            for site_choice in Site.objects.all().exclude(pk=self.site.pk)
        ]

    def get_translations(self, all_locales):
        current_site_pk = self.site.pk
        current_locale_pk = self.locale.pk

        return [
            {
                "locale": locale,
                "url": self._get_edit_url(current_site_pk, locale),
            }
            for locale in all_locales
            if locale.pk != current_locale_pk
        ]

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "site_choices": self.get_site_choices(),
        }


edit_site_settings = EditSiteSettingsView.as_view()


class EditGenericSettingsView(EditView):
    def get_object(self):
        return self.model._get_or_create(locale=self.locale)

    def _get_edit_url(self, locale):
        return get_edit_setting_url(self.app_name, self.model_name, locale=locale)

    def get_edit_url(self):
        return self._get_edit_url(self.locale)

    def get_translations(self, all_locales):
        current_locale_pk = self.locale.pk

        return [
            {
                "locale": locale,
                "url": self._get_edit_url(locale),
            }
            for locale in all_locales
            if locale.pk != current_locale_pk
        ]


edit_generic_settings = EditGenericSettingsView.as_view()


def edit(request, app_name, model_name, pk):
    model = get_model_from_url_params(app_name, model_name)
    return edit_site_settings(request, app_name, model_name, model, pk=pk)
