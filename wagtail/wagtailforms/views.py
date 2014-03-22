from django.http import Http404
from django.shortcuts import get_object_or_404, render, redirect
from django.utils.encoding import force_text
from django.utils.text import capfirst
from django.contrib.contenttypes.models import ContentType
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.core.exceptions import PermissionDenied
from django.utils.translation import ugettext as _

from wagtail.wagtailadmin.edit_handlers import ObjectList, extract_panel_definitions_from_model_class
from wagtail.wagtailcore.models import Page
from wagtail.wagtailforms.models import FormSubmission, get_form_types


def get_form_type_from_url_params(app_name, model_name):
    """
    Retrieve a form type from an app_name / model_name combo.
    Throw Http404 if not a valid form type
    """
    try:
        content_type = ContentType.objects.get_by_natural_key(app_name, model_name)
    except ContentType.DoesNotExist:
        raise Http404
    if content_type not in get_form_types():
        raise Http404

    return content_type


@permission_required('wagtailadmin.access_admin')
def index(request):
    form_types = get_form_types()
    form_pages = Page.objects.filter(content_type__in=form_types)
    
    return render(request, 'wagtailforms/index.html', {
        'form_pages': form_pages,
    })

@permission_required('wagtailadmin.access_admin')
def list_submissions(request, app_label, model, id):

    model = get_form_type_from_url_params(app_label, model).model_class()
    form_page = get_object_or_404(model, id=id)

    submissions = FormSubmission.objects.filter(form_page=form_page)

    return render(request, 'wagtailforms/form_index.html', {
         'form_page': form_page,
         'submissions': submissions,
    })

"""

@permission_required('wagtailadmin.access_admin')  # further permissions are enforced within the view
def create(request, content_type_app_name, content_type_model_name):
    content_type = get_content_type_from_url_params(content_type_app_name, content_type_model_name)
    if not user_can_edit_snippet_type(request.user, content_type):
        raise PermissionDenied

    model = content_type.model_class()
    snippet_type_name = get_snippet_type_name(content_type)[0]

    instance = model()
    edit_handler_class = get_snippet_edit_handler(model)
    form_class = edit_handler_class.get_form_class(model)

    if request.POST:
        form = form_class(request.POST, request.FILES, instance=instance)

        if form.is_valid():
            form.save()

            messages.success(
                request,
                _("{snippet_type} '{instance}' created.").format(
                    snippet_type=capfirst(get_snippet_type_name(content_type)[0]), 
                    instance=instance
                )
            )
            return redirect('wagtailsnippets_list', content_type.app_label, content_type.model)
        else:
            messages.error(request, _("The snippet could not be created due to errors."))
            edit_handler = edit_handler_class(instance=instance, form=form)
    else:
        form = form_class(instance=instance)
        edit_handler = edit_handler_class(instance=instance, form=form)

    return render(request, 'wagtailsnippets/snippets/create.html', {
        'content_type': content_type,
        'snippet_type_name': snippet_type_name,
        'edit_handler': edit_handler,
    })


@permission_required('wagtailadmin.access_admin')  # further permissions are enforced within the view
def edit(request, content_type_app_name, content_type_model_name, id):
    content_type = get_content_type_from_url_params(content_type_app_name, content_type_model_name)
    if not user_can_edit_snippet_type(request.user, content_type):
        raise PermissionDenied

    model = content_type.model_class()
    snippet_type_name = get_snippet_type_name(content_type)[0]

    instance = get_object_or_404(model, id=id)
    edit_handler_class = get_snippet_edit_handler(model)
    form_class = edit_handler_class.get_form_class(model)

    if request.POST:
        form = form_class(request.POST, request.FILES, instance=instance)

        if form.is_valid():
            form.save()

            messages.success(
                request,
                _("{snippet_type} '{instance}' updated.").format(
                    snippet_type=capfirst(snippet_type_name), 
                    instance=instance
                )
            )
            return redirect('wagtailsnippets_list', content_type.app_label, content_type.model)
        else:
            messages.error(request, _("The snippet could not be saved due to errors."))
            edit_handler = edit_handler_class(instance=instance, form=form)
    else:
        form = form_class(instance=instance)
        edit_handler = edit_handler_class(instance=instance, form=form)

    return render(request, 'wagtailsnippets/snippets/edit.html', {
        'content_type': content_type,
        'snippet_type_name': snippet_type_name,
        'instance': instance,
        'edit_handler': edit_handler,
    })


"""