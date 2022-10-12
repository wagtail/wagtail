from functools import lru_cache

from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.text import capfirst
from django.utils.translation import gettext as _

from wagtail.admin import messages
from wagtail.admin.panels import (
    ObjectList,
    TabbedInterface,
    extract_panel_definitions_from_model_class,
)
from wagtail.admin.views import generic
from wagtail.models import Site
from wagtail.permission_policies import ModelPermissionPolicy

from .forms import SiteSwitchForm
from .models import BaseGenericSetting, BaseSiteSetting
from .registry import registry


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
        if issubclass(model, BaseSiteSetting):
            panels = extract_panel_definitions_from_model_class(model, ["site"])
        elif issubclass(model, BaseGenericSetting):
            panels = extract_panel_definitions_from_model_class(model)
        else:
            raise NotImplementedError

        edit_handler = ObjectList(panels)
    return edit_handler.bind_to_model(model)


def redirect_to_relevant_instance(request, app_name, model_name):
    model = get_model_from_url_params(app_name, model_name)

    if issubclass(model, BaseSiteSetting):
        # Redirect the user to the edit page for the current site
        # (or the current request does not correspond to a site, the first site in the list)
        site_request = Site.find_for_request(request)
        site = site_request or Site.objects.first()
        if not site:
            messages.error(
                request,
                _("This setting could not be opened because there is no site defined."),
            )
            return redirect("wagtailadmin_home")
        return redirect(
            "wagtailsettings:edit",
            app_name,
            model_name,
            site.pk,
        )
    elif issubclass(model, BaseGenericSetting):
        return redirect(
            "wagtailsettings:edit",
            app_name,
            model_name,
            model.load(request_or_site=request).id,
        )
    else:
        raise NotImplementedError


class EditView(generic.EditView):
    template_name = "wagtailsettings/edit.html"
    site = None
    site_switcher = None

    def setup(self, request, app_name, model_name, model, *args, **kwargs):
        self.app_name = app_name
        self.model_name = model_name
        self.model = model
        self.permission_policy = ModelPermissionPolicy(self.model)
        super().setup(request, *args, **kwargs)

    def get_site(self):
        return self.site

    def get_site_switcher(self):
        return self.site_switcher

    def get_panel(self):
        return get_setting_edit_handler(self.model)

    def get_form_id(self):
        raise NotImplementedError(
            "Subclasses of wagtail.contrib.settings.views.EditView"
            "must provide a get_form_id method"
        )

    def get_form_kwargs(self):
        return {
            **super().get_form_kwargs(),
            "instance": self.object,
            "for_user": self.request.user,
        }

    def get_success_url(self):
        return self.get_edit_url()

    def get_success_message(self):
        return _("%(setting_type)s updated.") % {
            "setting_type": capfirst(self.model._meta.verbose_name),
            "instance": self.object,
        }

    def get_success_buttons(self):
        return []

    def get_error_message(self):
        return _("The setting could not be saved due to errors.")

    def save_instance(self):
        return self.form.save()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        media = context["media"]
        site_switcher = self.get_site_switcher()
        if site_switcher:
            media += site_switcher.media

        context.update(
            {
                "opts": self.model._meta,
                "setting_type_name": self.model._meta.verbose_name,
                "instance": self.object,
                "media": media,
                "site": self.get_site(),
                "site_switcher": site_switcher,
                "tabbed": isinstance(context["panel"].panel, TabbedInterface),
                "form_id": self.get_form_id(),
            }
        )

        return context


class EditSiteSettingsView(EditView):
    def get_form_id(self):
        return self.site.pk

    def get_object(self):
        self.site = get_object_or_404(Site, pk=self.kwargs["pk"])
        return self.model.for_site(self.site)

    def get_edit_url(self):
        return reverse(
            "wagtailsettings:edit",
            args=[
                self.app_name,
                self.model_name,
                self.object.site_id,
            ],
        )

    def get_site_switcher(self):
        # Show a site switcher form if there are multiple sites
        if Site.objects.count() > 1:
            return SiteSwitchForm(self.site, self.model)
        return None


edit_site_settings = EditSiteSettingsView.as_view()


class EditGenericSettingsView(EditView):
    def get_form_id(self):
        return self.object.pk

    def get_object(self):
        queryset = self.model.base_queryset()

        # Create the instance if we haven't already.
        if queryset.count() == 0:
            self.model.objects.create()

        return get_object_or_404(self.model, pk=self.kwargs["pk"])

    def get_edit_url(self):
        return reverse(
            "wagtailsettings:edit",
            args=[
                self.app_name,
                self.model_name,
            ],
        )


edit_generic_settings = EditGenericSettingsView.as_view()


def edit(request, app_name, model_name, pk):
    # The following will raise a 404 error
    # if app_name-model_name is an invalid setting type.
    model = get_model_from_url_params(app_name, model_name)

    if issubclass(model, BaseSiteSetting):
        view = edit_site_settings
    elif issubclass(model, BaseGenericSetting):
        view = edit_generic_settings

    return view(request, app_name, model_name, model, pk=pk)
