from urllib.parse import urlencode

from django.apps import apps
from django.contrib.admin.utils import quote, unquote
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.text import capfirst
from django.utils.translation import ugettext as _

from wagtail.admin import messages
from wagtail.admin.edit_handlers import ObjectList, extract_panel_definitions_from_model_class
from wagtail.admin.forms.search import SearchForm
from wagtail.admin.utils import permission_denied
from wagtail.search.backends import get_search_backend
from wagtail.search.index import class_is_indexed
from wagtail.snippets.models import get_snippet_models
from wagtail.snippets.permissions import get_permission_name, user_can_edit_snippet_type


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

        SNIPPET_EDIT_HANDLERS[model] = edit_handler.bind_to(model=model)

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

    # Preserve the snippet's model-level ordering if specified, but fall back on PK if not
    # (to ensure pagination is consistent)
    if not items.ordered:
        items = items.order_by('pk')

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

    paginator = Paginator(items, per_page=20)
    paginated_items = paginator.get_page(request.GET.get('p'))

    # Template
    if request.is_ajax():
        template = 'wagtailsnippets/snippets/results.html'
    else:
        template = 'wagtailsnippets/snippets/type_index.html'

    return render(request, template, {
        'model_opts': model._meta,
        'items': paginated_items,
        'can_add_snippet': request.user.has_perm(get_permission_name('add', model)),
        'can_delete_snippets': request.user.has_perm(get_permission_name('delete', model)),
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
    edit_handler = get_snippet_edit_handler(model)
    edit_handler = edit_handler.bind_to(request=request)
    form_class = edit_handler.get_form_class()

    if request.method == 'POST':
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
                        'wagtailsnippets:edit', args=(app_label, model_name, quote(instance.pk))
                    ), _('Edit'))
                ]
            )
            return redirect('wagtailsnippets:list', app_label, model_name)
        else:
            messages.validation_error(
                request, _("The snippet could not be created due to errors."), form
            )
    else:
        form = form_class(instance=instance)

    edit_handler = edit_handler.bind_to(instance=instance, form=form)

    return render(request, 'wagtailsnippets/snippets/create.html', {
        'model_opts': model._meta,
        'edit_handler': edit_handler,
        'form': form,
    })


def edit(request, app_label, model_name, pk):
    model = get_snippet_model_from_url_params(app_label, model_name)

    permission = get_permission_name('change', model)
    if not request.user.has_perm(permission):
        return permission_denied(request)

    instance = get_object_or_404(model, pk=unquote(pk))
    edit_handler = get_snippet_edit_handler(model)
    edit_handler = edit_handler.bind_to(instance=instance, request=request)
    form_class = edit_handler.get_form_class()

    if request.method == 'POST':
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
                        'wagtailsnippets:edit', args=(app_label, model_name, quote(instance.pk))
                    ), _('Edit'))
                ]
            )
            return redirect('wagtailsnippets:list', app_label, model_name)
        else:
            messages.validation_error(
                request, _("The snippet could not be saved due to errors."), form
            )
    else:
        form = form_class(instance=instance)

    edit_handler = edit_handler.bind_to(form=form)

    return render(request, 'wagtailsnippets/snippets/edit.html', {
        'model_opts': model._meta,
        'instance': instance,
        'edit_handler': edit_handler,
        'form': form,
    })


def delete(request, app_label, model_name, pk=None):
    model = get_snippet_model_from_url_params(app_label, model_name)

    permission = get_permission_name('delete', model)
    if not request.user.has_perm(permission):
        return permission_denied(request)

    if pk:
        instances = [get_object_or_404(model, pk=unquote(pk))]
    else:
        ids = request.GET.getlist('id')
        instances = model.objects.filter(pk__in=ids)

    count = len(instances)

    if request.method == 'POST':
        for instance in instances:
            instance.delete()

        if count == 1:
            message_content = _("{snippet_type} '{instance}' deleted.").format(
                snippet_type=capfirst(model._meta.verbose_name_plural),
                instance=instance
            )
        else:
            message_content = _("{count} {snippet_type} deleted.").format(
                snippet_type=capfirst(model._meta.verbose_name_plural),
                count=count
            )

        messages.success(request, message_content)

        return redirect('wagtailsnippets:list', app_label, model_name)

    return render(request, 'wagtailsnippets/snippets/confirm_delete.html', {
        'model_opts': model._meta,
        'count': count,
        'instances': instances,
        'submit_url': (
            reverse('wagtailsnippets:delete-multiple', args=(app_label, model_name))
            + '?' + urlencode([('id', instance.pk) for instance in instances])
        ),
    })


def usage(request, app_label, model_name, pk):
    model = get_snippet_model_from_url_params(app_label, model_name)
    instance = get_object_or_404(model, pk=unquote(pk))

    paginator = Paginator(instance.get_usage(), per_page=20)
    used_by = paginator.get_page(request.GET.get('p'))

    return render(request, "wagtailsnippets/snippets/usage.html", {
        'instance': instance,
        'used_by': used_by
    })
