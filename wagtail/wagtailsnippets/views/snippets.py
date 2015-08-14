from django.http import Http404
from django.shortcuts import get_object_or_404, render, redirect
from django.utils.encoding import force_text
from django.utils.text import capfirst
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from wagtail.wagtailadmin.edit_handlers import ObjectList, extract_panel_definitions_from_model_class

from wagtail.wagtailsnippets.models import get_snippet_content_types
from wagtail.wagtailsnippets.permissions import user_can_edit_snippet_type
from wagtail.wagtailadmin import messages
from wagtail.wagtailadmin.forms import SearchForm
from wagtail.wagtailsearch.index import class_is_indexed
from wagtail.wagtailsearch.backends import get_search_backend


# == Helper functions ==


def get_snippet_type_name(content_type):
    """ e.g. given the 'advert' content type, return ('Advert', 'Adverts') """
    # why oh why is this so convoluted?
    opts = content_type.model_class()._meta
    return (
        force_text(opts.verbose_name),
        force_text(opts.verbose_name_plural)
    )


def get_snippet_type_description(content_type):
    """ return the meta description of the class associated with the given content type """
    opts = content_type.model_class()._meta
    try:
        return force_text(opts.description)
    except:
        return ''


def get_content_type_from_url_params(app_name, model_name):
    """
    retrieve a content type from an app_name / model_name combo.
    Throw Http404 if not a valid snippet type
    """
    try:
        content_type = ContentType.objects.get_by_natural_key(app_name, model_name)
    except ContentType.DoesNotExist:
        raise Http404
    if content_type not in get_snippet_content_types():
        # don't allow people to hack the URL to edit content types that aren't registered as snippets
        raise Http404

    return content_type


SNIPPET_EDIT_HANDLERS = {}


def get_snippet_edit_handler(model):
    if model not in SNIPPET_EDIT_HANDLERS:
        panels = extract_panel_definitions_from_model_class(model)
        edit_handler = ObjectList(panels).bind_to_model(model)

        SNIPPET_EDIT_HANDLERS[model] = edit_handler

    return SNIPPET_EDIT_HANDLERS[model]


# == Views ==


def index(request):
    snippet_types = [
        (
            get_snippet_type_name(content_type)[1],
            get_snippet_type_description(content_type),
            content_type
        )
        for content_type in get_snippet_content_types()
        if user_can_edit_snippet_type(request.user, content_type)
    ]
    return render(request, 'wagtailsnippets/snippets/index.html', {
        'snippet_types': sorted(snippet_types, key=lambda x: x[0].lower()),
    })


def list(request, content_type_app_name, content_type_model_name):
    content_type = get_content_type_from_url_params(content_type_app_name, content_type_model_name)
    if not user_can_edit_snippet_type(request.user, content_type):
        raise PermissionDenied

    model = content_type.model_class()
    snippet_type_name, snippet_type_name_plural = get_snippet_type_name(content_type)

    items = model.objects.all()

    # Search
    is_searchable = class_is_indexed(model)
    is_searching = False
    search_query = None
    if is_searchable and 'q' in request.GET:
        search_form = SearchForm(request.GET, placeholder=_("Search %(snippet_type_name)s") % {
            'snippet_type_name': snippet_type_name_plural
        })

        if search_form.is_valid():
            search_query = search_form.cleaned_data['q']

            search_backend = get_search_backend()
            items = search_backend.search(search_query, items)
            is_searching = True

    else:
        search_form = SearchForm(placeholder=_("Search %(snippet_type_name)s") % {
            'snippet_type_name': snippet_type_name_plural
        })

    # Pagination
    p = request.GET.get('p', 1)
    paginator = Paginator(items, 20)

    try:
        paginated_items = paginator.page(p)
    except PageNotAnInteger:
        paginated_items = paginator.page(1)
    except EmptyPage:
        paginated_items = paginator.page(paginator.num_pages)

    # Template
    if request.is_ajax():
        template = 'wagtailsnippets/snippets/results.html'
    else:
        template = 'wagtailsnippets/snippets/type_index.html'

    return render(request, template, {
        'content_type': content_type,
        'snippet_type_name': snippet_type_name,
        'snippet_type_name_plural': snippet_type_name_plural,
        'items': paginated_items,
        'is_searchable': is_searchable,
        'search_form': search_form,
        'is_searching': is_searching,
        'query_string': search_query,
    })


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
                ),
                buttons=[
                    messages.button(reverse('wagtailsnippets:edit', args=(content_type_app_name, content_type_model_name, instance.id)), _('Edit'))
                ]
            )
            return redirect('wagtailsnippets:list', content_type.app_label, content_type.model)
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
                ),
                buttons=[
                    messages.button(reverse('wagtailsnippets:edit', args=(content_type_app_name, content_type_model_name, instance.id)), _('Edit'))
                ]
            )
            return redirect('wagtailsnippets:list', content_type.app_label, content_type.model)
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
        'edit_handler': edit_handler
    })


def delete(request, content_type_app_name, content_type_model_name, id):
    content_type = get_content_type_from_url_params(content_type_app_name, content_type_model_name)
    if not user_can_edit_snippet_type(request.user, content_type):
        raise PermissionDenied

    model = content_type.model_class()
    snippet_type_name = get_snippet_type_name(content_type)[0]

    instance = get_object_or_404(model, id=id)

    if request.POST:
        instance.delete()
        messages.success(
            request,
            _("{snippet_type} '{instance}' deleted.").format(
                snippet_type=capfirst(snippet_type_name),
                instance=instance
            )
        )
        return redirect('wagtailsnippets:list', content_type.app_label, content_type.model)

    return render(request, 'wagtailsnippets/snippets/confirm_delete.html', {
        'content_type': content_type,
        'snippet_type_name': snippet_type_name,
        'instance': instance,
    })


def usage(request, content_type_app_name, content_type_model_name, id):
    content_type = get_content_type_from_url_params(content_type_app_name, content_type_model_name)
    model = content_type.model_class()
    instance = get_object_or_404(model, id=id)

    # Pagination
    p = request.GET.get('p', 1)
    paginator = Paginator(instance.get_usage(), 20)

    try:
        used_by = paginator.page(p)
    except PageNotAnInteger:
        used_by = paginator.page(1)
    except EmptyPage:
        used_by = paginator.page(paginator.num_pages)

    return render(request, "wagtailsnippets/snippets/usage.html", {
        'instance': instance,
        'used_by': used_by
    })
