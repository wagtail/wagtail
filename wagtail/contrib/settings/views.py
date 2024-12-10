from functools import lru_cache

from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.text import capfirst
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from wagtail.admin import messages
from wagtail.admin.panels import (
    ObjectList,
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


@lru_cache(maxsize=None)
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
    edit_url_name = "wagtailsettings:edit"
    error_message = gettext_lazy("The setting could not be saved due to errors.")
    permission_required = "change"

    def setup(self, request, app_name, model_name, *args, **kwargs):
        self.app_name = app_name
        self.model_name = model_name
        self.model = get_model_from_url_params(app_name, model_name)
        self.permission_policy = ModelPermissionPolicy(self.model)
        self.pk = kwargs.get(self.pk_url_kwarg)
        super().setup(request, app_name, model_name, *args, **kwargs)

    def get_header_icon(self):
        return registry._model_icons.get(self.model)

    def get_object(self, queryset=None):
        self.site = None
        if issubclass(self.model, BaseSiteSetting):
            self.site = get_object_or_404(Site, pk=self.pk)
            return self.model.for_site(self.site)
        else:
            return get_object_or_404(self.model, pk=self.pk)

    def get_panel(self):
        return get_setting_edit_handler(self.model)

    def get_edit_url(self):
        return reverse(
            self.edit_url_name,
            args=(self.app_name, self.model_name, self.pk),
        )

    def get_success_buttons(self):
        return None

    def get_page_subtitle(self):
        return capfirst(self.model._meta.verbose_name)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        site_switcher = None
        if self.site and Site.objects.count() > 1:
            site_switcher = SiteSwitchForm(self.site, self.model)
            context["media"] += site_switcher.media

        context["site_switcher"] = site_switcher
        return context

    def get_success_url(self):
        return self.get_edit_url()

    def get_success_message(self):
        return capfirst(
            _("%(setting_type)s updated.")
            % {"setting_type": self.model._meta.verbose_name}
        )
