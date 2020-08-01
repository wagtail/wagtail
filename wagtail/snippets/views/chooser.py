from django.contrib.admin.utils import quote, unquote
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.translation import gettext as _

from wagtail.admin.forms.search import SearchForm
from wagtail.admin.modal_workflow import render_modal_workflow
from wagtail.search.backends import get_search_backend
from wagtail.search.index import class_is_indexed
from wagtail.snippets.views.snippets import get_snippet_model_from_url_params


def choose(request, app_label, model_name):
    model = get_snippet_model_from_url_params(app_label, model_name)

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
            'snippet_type_name': model._meta.verbose_name
        })

        if search_form.is_valid():
            search_query = search_form.cleaned_data['q']

            search_backend = get_search_backend()
            items = search_backend.search(search_query, items)
            is_searching = True

    else:
        search_form = SearchForm(placeholder=_("Search %(snippet_type_name)s") % {
            'snippet_type_name': model._meta.verbose_name
        })

    # Pagination
    paginator = Paginator(items, per_page=25)
    paginated_items = paginator.get_page(request.GET.get('p'))

    # If paginating or searching, render "results.html"
    if request.GET.get('results', None) == 'true':
        return TemplateResponse(request, "wagtailsnippets/chooser/results.html", {
            'model_opts': model._meta,
            'items': paginated_items,
            'query_string': search_query,
            'is_searching': is_searching,
        })

    return render_modal_workflow(
        request,
        'wagtailsnippets/chooser/choose.html', None,
        {
            'model_opts': model._meta,
            'items': paginated_items,
            'is_searchable': is_searchable,
            'search_form': search_form,
            'query_string': search_query,
            'is_searching': is_searching,
        }, json_data={'step': 'choose'}
    )


def chosen(request, app_label, model_name, pk):
    model = get_snippet_model_from_url_params(app_label, model_name)
    item = get_object_or_404(model, pk=unquote(pk))

    snippet_data = {
        'id': str(item.pk),
        'string': str(item),
        'edit_link': reverse('wagtailsnippets:edit', args=(
            app_label, model_name, quote(item.pk)))
    }

    return render_modal_workflow(
        request,
        None, None,
        None, json_data={'step': 'chosen', 'result': snippet_data}
    )
