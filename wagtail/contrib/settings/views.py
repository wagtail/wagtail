from functools import lru_cache

from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.utils.text import capfirst
from django.utils.translation import gettext as _

from wagtail.admin import messages
from wagtail.admin.panels import (
    ObjectList,
    TabbedInterface,
    extract_panel_definitions_from_model_class,
)
from wagtail.admin.views import generic
from wagtail.models import Locale, Site
from wagtail.permission_policies import ModelPermissionPolicy

from .models import AbstractSiteSetting, BaseGenericSetting
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
        elif issubclass(model, BaseGenericSetting):
            panels = extract_panel_definitions_from_model_class(model)
        else:
            raise NotImplementedError

        edit_handler = ObjectList(panels)
    return edit_handler.bind_to_model(model)


def redirect_to_relevant_instance(request, app_name, model_name):
    model = get_model_from_url_params(app_name, model_name)
    pk = None

    if issubclass(model, AbstractSiteSetting):
        # Redirect the user to the edit page for the current site
        # (or the current request does not correspond to a site, the first site in the list)
        site_request = Site.find_for_request(request)
        site = site_request or Site.objects.first()
        if site:
            pk = site.pk
        else:
            messages.error(
                request,
                _("This setting could not be opened because there is no site defined."),
            )
            return redirect("wagtailadmin_home")
    elif issubclass(model, BaseGenericSetting):
        pk = model.load(request_or_site=request).id
    else:
        raise NotImplementedError

    locale = get_locale_for(request=request, model=model)
    return redirect(get_edit_setting_url(app_name, model_name, pk, locale=locale))


class EditView(generic.EditView):
    template_name = "wagtailsettings/edit.html"
    site = None
    form_id = None

    def setup(self, request, app_name, model_name, model, *args, **kwargs):
        self.app_name = app_name
        self.model_name = model_name
        self.model = model
        self.permission_policy = ModelPermissionPolicy(self.model)
        super().setup(request, *args, **kwargs)

    def get_panel(self):
        return get_setting_edit_handler(self.model)

    def get_edit_url(self):
        return get_edit_setting_url(
            self.app_name, self.model_name, self.form_id, self.locale
        )

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

    def get_translations(self):
        return [
            {
                "locale": locale,
                "url": get_edit_setting_url(
                    self.app_name, self.model_name, self.form_id, locale
                ),
            }
            for locale in Locale.objects.all().exclude(id=self.locale.id)
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.locale:
            context["translations"] = self.get_translations()

        context.update(
            {
                "opts": self.model._meta,
                "site": self.site,
                "instance": self.object,
                "form_id": self.form_id,
                "setting_type_name": self.model._meta.verbose_name,
                "tabbed": isinstance(context["panel"].panel, TabbedInterface),
            }
        )
        return context


class EditSiteSettingsView(EditView):
    def get_object(self):
        self.site = get_object_or_404(Site, pk=self.kwargs["pk"])
        self.form_id = self.site.pk
        return self.model.for_site(self.site, locale=self.locale)

    def get_site_choices(self):
        return [
            {
                "site": site_choice,
                "url": get_edit_setting_url(
                    self.app_name, self.model_name, site_choice.pk, self.locale
                ),
            }
            for site_choice in Site.objects.all().exclude(id=self.site.id)
        ]

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "site_choices": self.get_site_choices(),
        }


edit_site_settings = EditSiteSettingsView.as_view()


class EditGenericSettingsView(EditView):
    def get_object(self):
        queryset = self.model.base_queryset()

        # Create the instance if we haven't already.
        if queryset.count() == 0:
            self.model.objects.create()

        self.form_id = self.kwargs["pk"]
        return get_object_or_404(self.model, pk=self.form_id)


edit_generic_settings = EditGenericSettingsView.as_view()


def edit(request, app_name, model_name, pk):
    # The following will raise a 404 error
    # if app_name-model_name is an invalid setting type.
    model = get_model_from_url_params(app_name, model_name)

    if issubclass(model, AbstractSiteSetting):
        view = edit_site_settings
    elif issubclass(model, BaseGenericSetting):
        view = edit_generic_settings

    return view(request, app_name, model_name, model, pk=pk)
