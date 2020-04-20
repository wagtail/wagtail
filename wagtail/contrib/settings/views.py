from functools import lru_cache

from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import capfirst
from django.utils.translation import ugettext as _

from wagtail.admin import messages
from wagtail.admin.edit_handlers import (
    ObjectList, TabbedInterface, extract_panel_definitions_from_model_class)
from wagtail.core.models import Site

from .forms import SiteSwitchForm
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


@lru_cache()
def get_setting_edit_handler(model):
    if hasattr(model, 'edit_handler'):
        edit_handler = model.edit_handler
    else:
        panels = extract_panel_definitions_from_model_class(model, ['site'])
        edit_handler = ObjectList(panels)
    return edit_handler.bind_to(model=model)


def edit_current_site(request, app_name, model_name):
    # Redirect the user to the edit page for the current site
    # (or the current request does not correspond to a site, the first site in the list)
    site_request = Site.find_for_request(request)
    site = site_request or Site.objects.first()
    if not site:
        messages.error(request, _("This setting could not be opened because there is no site defined."))
        return redirect('wagtailadmin_home')
    return redirect('wagtailsettings:edit', app_name, model_name, site.pk)


def edit(request, app_name, model_name, site_pk):
    model = get_model_from_url_params(app_name, model_name)
    if not user_can_edit_setting_type(request.user, model):
        raise PermissionDenied
    site = get_object_or_404(Site, pk=site_pk)

    setting_type_name = model._meta.verbose_name

    instance = model.for_site(site)
    edit_handler = get_setting_edit_handler(model)
    edit_handler = edit_handler.bind_to(instance=instance, request=request)
    form_class = edit_handler.get_form_class()

    if request.method == 'POST':
        form = form_class(request.POST, request.FILES, instance=instance)

        if form.is_valid():
            form.save()

            messages.success(
                request,
                _("%(setting_type)s updated.") % {
                    'setting_type': capfirst(setting_type_name),
                    'instance': instance
                }
            )
            return redirect('wagtailsettings:edit', app_name, model_name, site.pk)
        else:
            messages.validation_error(
                request, _("The setting could not be saved due to errors."), form
            )
    else:
        form = form_class(instance=instance)

    edit_handler = edit_handler.bind_to(form=form)

    # Show a site switcher form if there are multiple sites
    site_switcher = None
    if Site.objects.count() > 1:
        site_switcher = SiteSwitchForm(site, model)

    return render(request, 'wagtailsettings/edit.html', {
        'opts': model._meta,
        'setting_type_name': setting_type_name,
        'instance': instance,
        'edit_handler': edit_handler,
        'form': form,
        'site': site,
        'site_switcher': site_switcher,
        'tabbed': isinstance(edit_handler, TabbedInterface),
    })
