from django.http import Http404
from django.shortcuts import render, redirect
from django.utils.encoding import force_text
from django.utils.text import capfirst
from django.contrib.contenttypes.models import ContentType
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.core.exceptions import PermissionDenied
from django.utils.translation import ugettext as _

from wagtail.wagtailadmin.edit_handlers import ObjectList, extract_panel_definitions_from_model_class

from wagtail.wagtailsettings.models import get_setting_content_types
from wagtail.wagtailsettings.permissions import user_can_edit_setting_type


# == Helper functions ==


def get_setting_type_name(content_type):
    """ e.g. given the 'advert' content type, return ('Advert', 'Adverts') """
    # why oh why is this so convoluted?
    opts = content_type.model_class()._meta
    return (
        force_text(opts.verbose_name),
        force_text(opts.verbose_name_plural)
    )


def get_setting_type_description(content_type):
    """ return the meta description of the class associated with the given content type """
    opts = content_type.model_class()._meta
    try:
        return force_text(opts.description)
    except:
        return ''


def get_content_type_from_url_params(app_name, model_name):
    """
    retrieve a content type from an app_name / model_name combo.
    Throw Http404 if not a valid setting type
    """
    try:
        content_type = ContentType.objects.get_by_natural_key(app_name, model_name)
    except ContentType.DoesNotExist:
        raise Http404
    if content_type not in get_setting_content_types():
        # don't allow people to hack the URL to edit content types that aren't registered as settings
        raise Http404

    return content_type


SETTING_EDIT_HANDLERS = {}


def get_setting_edit_handler(model):
    if model not in SETTING_EDIT_HANDLERS:
        panels = extract_panel_definitions_from_model_class(model, ['site'])
        edit_handler = ObjectList(panels)

        SETTING_EDIT_HANDLERS[model] = edit_handler

    return SETTING_EDIT_HANDLERS[model]


# == Views ==


@permission_required('wagtailadmin.access_admin')
def index(request):
    setting_types = [
        (
            get_setting_type_name(content_type)[0],
            get_setting_type_description(content_type),
            content_type
        )
        for content_type in get_setting_content_types()
        if user_can_edit_setting_type(request.user, content_type)
    ]
    return render(request, 'wagtailsettings/index.html', {
        'setting_types': setting_types,
    })


@permission_required('wagtailadmin.access_admin')  # further permissions are enforced within the view
def edit(request, content_type_app_name, content_type_model_name):
    content_type = get_content_type_from_url_params(content_type_app_name, content_type_model_name)
    if not user_can_edit_setting_type(request.user, content_type):
        raise PermissionDenied

    model = content_type.model_class()
    setting_type_name = get_setting_type_name(content_type)[0]

    (instance, created) = model.objects.get_or_create(site=request.site)
    edit_handler_class = get_setting_edit_handler(model)
    form_class = edit_handler_class.get_form_class(model)

    if request.POST:
        form = form_class(request.POST, request.FILES, instance=instance)

        if form.is_valid():
            form.save()

            messages.success(
                request,
                _("{setting_type} updated.").format(
                    setting_type=capfirst(setting_type_name),
                    instance=instance
                )
            )
            return redirect('wagtailsettings_index')
        else:
            messages.error(request, _("The setting could not be saved due to errors."))
            edit_handler = edit_handler_class(instance=instance, form=form)
    else:
        form = form_class(instance=instance)
        edit_handler = edit_handler_class(instance=instance, form=form)

    return render(request, 'wagtailsettings/edit.html', {
        'content_type': content_type,
        'setting_type_name': setting_type_name,
        'instance': instance,
        'edit_handler': edit_handler,
    })
