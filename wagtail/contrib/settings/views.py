from functools import lru_cache

# from typing import Optional
# from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse

# from django.template.response import TemplateResponse
from django.utils.text import capfirst
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

# from django.views import View
from wagtail.admin import messages
from wagtail.admin.panels import (
    ObjectList,
    TabbedInterface,
    extract_panel_definitions_from_model_class,
)
from wagtail.admin.views import generic
from wagtail.log_actions import log
from wagtail.models import Site

from .forms import SiteSwitchForm
from .models import BaseGenericSetting, BaseSiteSetting

# from .permissions import user_can_edit_setting_type
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
    error_message = gettext_lazy("The setting could not be saved due to errors.")

    def setup(self, request, app_name, model_name, *args, **kwargs):
        self.app_name = app_name
        self.model_name = model_name
        self.model = get_model_from_url_params(app_name, model_name)
        self.pk = kwargs.get(self.pk_url_kwarg)
        super().setup(request, app_name, model_name, *args, **kwargs)

    def get_object(self, queryset=None):
        self.site = None
        if issubclass(self.model, BaseSiteSetting):
            self.site = get_object_or_404(Site, pk=self.pk)
            return self.model.for_site(self.site)
        else:
            return get_object_or_404(self.model, pk=self.pk)

    def get_form_class(self):
        return get_setting_edit_handler(self.model).get_form_class()

    def get_edit_url(self):
        return reverse(
            "wagtailsettings:edit",
            args=(
                self.app_name,
                self.model_name,
                self.pk,
            ),
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        self.site = None
        site_switcher = None

        if issubclass(self.model, BaseSiteSetting):
            self.site = get_object_or_404(Site, pk=self.kwargs["pk"])
            self.object = self.model.for_site(self.site)

            # Show a site switcher form if there are multiple sites
            if Site.objects.count() > 1:
                site_switcher = SiteSwitchForm(self.site, self.model)
                media = context.get("media") + site_switcher.media
        else:
            self.object = get_object_or_404(self.model, pk=self.kwargs["pk"])

        form = self.get_form()

        edit_handler = get_setting_edit_handler(self.model).get_bound_panel(
            instance=self.object, request=self.request, form=form
        )

        media = form.media + edit_handler.media

        context.update(
            {
                "setting_type_name": self.model._meta.verbose_name,
                "instance": self.object,
                "edit_handler": edit_handler,
                "site": self.site,
                "site_switcher": site_switcher,
                "tabbed": isinstance(
                    get_setting_edit_handler(self.model), TabbedInterface
                ),
                "media": media,
                "opts": self.model._meta,
                "form_id": self.object.pk,
            }
        )

        return context

    def get_success_url(self):
        return self.get_edit_url()

    def form_valid(self, form):
        with transaction.atomic():
            form.save()
            log(self.object, "wagtail.edit")

            messages.success(
                self.request,
                _("%(setting_type)s updated.")
                % {
                    "setting_type": capfirst(self.model._meta.verbose_name),
                    "instance": self.object,
                },
            )

        return redirect(
            "wagtailsettings:edit",
            app_name=self.model._meta.app_label,
            model_name=self.model._meta.model_name,
        )
