from django.core.urlresolvers import reverse
from django.apps import apps
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import capfirst
from django.utils.translation import ugettext as _

from wagtail.utils.pagination import paginate
from wagtail.wagtailadmin import messages
from wagtail.wagtailadmin.edit_handlers import (
    ObjectList, extract_panel_definitions_from_model_class)
from wagtail.wagtailadmin.forms import SearchForm
from wagtail.wagtailadmin.utils import permission_denied
from wagtail.wagtailsearch.backends import get_search_backend
from wagtail.wagtailsearch.index import class_is_indexed
from wagtail.wagtailsnippets.models import get_snippet_models
from wagtail.wagtailsnippets.permissions import (
    get_permission_name, user_can_edit_snippet_type)


# == Helper functions ==
def get_snippet_model_from_url_params(app_name, model_name):
    """
    Retrieve a model from an app_label / model_name combo.
    Raise Http404 if the model is not a valid snippet type.
    """
    try:
        model = apps.get_model(app_name, model_name)
    except LookupError:
        raise Http404
    if model not in get_snippet_models():
        # don't allow people to hack the URL to edit content types that aren't registered as snippets
        raise Http404

    return model


SNIPPET_EDIT_HANDLERS = {}


def get_snippet_edit_handler(model):
    if model not in SNIPPET_EDIT_HANDLERS:
        if hasattr(model, 'edit_handler'):
            # use the edit handler specified on the page class
            edit_handler = model.edit_handler
        else:
            panels = extract_panel_definitions_from_model_class(model)
            edit_handler = ObjectList(panels)

        SNIPPET_EDIT_HANDLERS[model] = edit_handler.bind_to_model(model)

    return SNIPPET_EDIT_HANDLERS[model]


# == Views ==


def index(request):
    snippet_model_opts = [
        model._meta for model in get_snippet_models()
        if user_can_edit_snippet_type(request.user, model)]
    return render(request, 'wagtailsnippets/snippets/index.html', {
        'snippet_model_opts': sorted(
            snippet_model_opts, key=lambda x: x.verbose_name.lower())})


def list(request, app_label, model_name):
    model = get_snippet_model_from_url_params(app_label, model_name)

    permissions = [
        get_permission_name(action, model)
        for action in ['add', 'change', 'delete']
    ]
    if not any([request.user.has_perm(perm) for perm in permissions]):
        return permission_denied(request)

    items = model.objects.all()

    # Search
    is_searchable = class_is_indexed(model)
    is_searching = False
    search_query = None
    if is_searchable and 'q' in request.GET:
        search_form = SearchForm(request.GET, placeholder=_("Search %(snippet_type_name)s") % {
            'snippet_type_name': model._meta.verbose_name_plural
        })

        if search_form.is_valid():
            search_query = search_form.cleaned_data['q']

            search_backend = get_search_backend()
            items = search_backend.search(search_query, items)
            is_searching = True

    else:
        search_form = SearchForm(placeholder=_("Search %(snippet_type_name)s") % {
            'snippet_type_name': model._meta.verbose_name_plural
        })

    paginator, paginated_items = paginate(request, items)

    # Template
    if request.is_ajax():
        template = 'wagtailsnippets/snippets/results.html'
    else:
        template = 'wagtailsnippets/snippets/type_index.html'

    return render(request, template, {
        'model_opts': model._meta,
        'items': paginated_items,
        'can_add_snippet': request.user.has_perm(get_permission_name('add', model)),
        'is_searchable': is_searchable,
        'search_form': search_form,
        'is_searching': is_searching,
        'query_string': search_query,
    })


def create(request, app_label, model_name):
    model = get_snippet_model_from_url_params(app_label, model_name)

    permission = get_permission_name('add', model)
    if not request.user.has_perm(permission):
        return permission_denied(request)

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
                    snippet_type=capfirst(model._meta.verbose_name),
                    instance=instance
                ),
                buttons=[
                    messages.button(reverse(
                        'wagtailsnippets:edit', args=(app_label, model_name, instance.id)
                    ), _('Edit'))
                ]
            )
            return redirect('wagtailsnippets:list', app_label, model_name)
        else:
            messages.error(request, _("The snippet could not be created due to errors."))
            edit_handler = edit_handler_class(instance=instance, form=form)
    else:
        form = form_class(instance=instance)
        edit_handler = edit_handler_class(instance=instance, form=form)

    return render(request, 'wagtailsnippets/snippets/create.html', {
        'model_opts': model._meta,
        'edit_handler': edit_handler,
    })


def edit(request, app_label, model_name, id):
    model = get_snippet_model_from_url_params(app_label, model_name)

    permission = get_permission_name('change', model)
    if not request.user.has_perm(permission):
        return permission_denied(request)

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
                    snippet_type=capfirst(model._meta.verbose_name_plural),
                    instance=instance
                ),
                buttons=[
                    messages.button(reverse(
                        'wagtailsnippets:edit', args=(app_label, model_name, instance.id)
                    ), _('Edit'))
                ]
            )
            return redirect('wagtailsnippets:list', app_label, model_name)
        else:
            messages.error(request, _("The snippet could not be saved due to errors."))
            edit_handler = edit_handler_class(instance=instance, form=form)
    else:
        form = form_class(instance=instance)
        edit_handler = edit_handler_class(instance=instance, form=form)

    return render(request, 'wagtailsnippets/snippets/edit.html', {
        'model_opts': model._meta,
        'instance': instance,
        'edit_handler': edit_handler
    })


def delete(request, app_label, model_name, id):
    model = get_snippet_model_from_url_params(app_label, model_name)

    permission = get_permission_name('delete', model)
    if not request.user.has_perm(permission):
        return permission_denied(request)

    instance = get_object_or_404(model, id=id)

    if request.POST:
        instance.delete()
        messages.success(
            request,
            _("{snippet_type} '{instance}' deleted.").format(
                snippet_type=capfirst(model._meta.verbose_name_plural),
                instance=instance
            )
        )
        return redirect('wagtailsnippets:list', app_label, model_name)

    return render(request, 'wagtailsnippets/snippets/confirm_delete.html', {
        'model_opts': model._meta,
        'instance': instance,
    })


def usage(request, app_label, model_name, id):
    model = get_snippet_model_from_url_params(app_label, model_name)
    instance = get_object_or_404(model, id=id)

    paginator, used_by = paginate(request, instance.get_usage())

    return render(request, "wagtailsnippets/snippets/usage.html", {
        'instance': instance,
        'used_by': used_by
    })
