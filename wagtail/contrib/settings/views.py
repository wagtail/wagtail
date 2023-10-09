from functools import lru_cache
from typing import Optional

from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils.text import capfirst
from django.utils.translation import gettext as _

from wagtail.admin import messages
from wagtail.admin.panels import (
    ObjectList,
    TabbedInterface,
    extract_panel_definitions_from_model_class,
)
from wagtail.log_actions import log
from wagtail.models import Site

from .forms import SiteSwitchForm
from .models import BaseGenericSetting, BaseSiteSetting
from .permissions import user_can_edit_setting_type
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


def edit(request, app_name, model_name, pk):
    model = get_model_from_url_params(app_name, model_name)

    if not user_can_edit_setting_type(request.user, model):
        raise PermissionDenied

    setting_type_name = model._meta.verbose_name
    edit_handler = get_setting_edit_handler(model)
    form_class = edit_handler.get_form_class()
    site: Optional[Site] = None
    site_switcher = None

    if issubclass(model, BaseSiteSetting):
        site = get_object_or_404(Site, pk=pk)
        form_id = site.pk
        instance = model.for_site(site)

        if request.method == "POST":
            form = form_class(
                request.POST, request.FILES, instance=instance, for_user=request.user
            )

            if form.is_valid():
                with transaction.atomic():
                    form.save()
                    log(instance, "wagtail.edit")

                messages.success(
                    request,
                    _("%(setting_type)s updated.")
                    % {
                        "setting_type": capfirst(setting_type_name),
                        "instance": instance,
                    },
                )
                return redirect("wagtailsettings:edit", app_name, model_name, site.pk)
            else:
                messages.validation_error(
                    request, _("The setting could not be saved due to errors."), form
                )
        else:
            form = form_class(instance=instance, for_user=request.user)

        edit_handler = edit_handler.get_bound_panel(
            instance=instance, request=request, form=form
        )

        media = form.media + edit_handler.media

        # Show a site switcher form if there are multiple sites
        if Site.objects.count() > 1:
            site_switcher = SiteSwitchForm(site, model)
            media += site_switcher.media

    elif issubclass(model, BaseGenericSetting):
        queryset = model.base_queryset()

        # Create the instance if we haven't already.
        if queryset.count() == 0:
            model.objects.create()

        instance = get_object_or_404(model, pk=pk)
        form_id = instance.pk

        if request.method == "POST":
            form = form_class(
                request.POST, request.FILES, instance=instance, for_user=request.user
            )

            if form.is_valid():
                with transaction.atomic():
                    form.save()
                    log(instance, "wagtail.edit")

                messages.success(
                    request,
                    _("%(setting_type)s updated.")
                    % {
                        "setting_type": capfirst(setting_type_name),
                        "instance": instance,
                    },
                )
                return redirect("wagtailsettings:edit", app_name, model_name)
            else:
                messages.validation_error(
                    request, _("The setting could not be saved due to errors."), form
                )
        else:
            form = form_class(instance=instance, for_user=request.user)

        edit_handler = edit_handler.get_bound_panel(
            instance=instance, request=request, form=form
        )

        media = form.media + edit_handler.media

    else:
        raise NotImplementedError

    return TemplateResponse(
        request,
        "wagtailsettings/edit.html",
        {
            "opts": model._meta,
            "setting_type_name": setting_type_name,
            "instance": instance,
            "edit_handler": edit_handler,
            "form": form,
            "site": site,
            "site_switcher": site_switcher,
            "tabbed": isinstance(edit_handler.panel, TabbedInterface),
            "media": media,
            "form_id": form_id,
        },
    )
