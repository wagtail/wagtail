import json

from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404, render
from django.utils.six import text_type
from django.utils.translation import ugettext as _

from wagtail.utils.pagination import paginate
from wagtail.wagtailadmin.forms import SearchForm
from wagtail.wagtailadmin.modal_workflow import render_modal_workflow
from wagtail.wagtailsearch.backends import get_search_backend
from wagtail.wagtailsearch.index import class_is_indexed
from wagtail.wagtailsnippets.views.snippets import \
    get_snippet_model_from_url_params


def choose(request, app_label, model_name):
    model = get_snippet_model_from_url_params(app_label, model_name)

    items = model.objects.all()

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
    paginator, paginated_items = paginate(request, items, per_page=25)

    # If paginating or searching, render "results.html"
    if request.GET.get('results', None) == 'true':
        return render(request, "wagtailsnippets/chooser/results.html", {
            'model_opts': model._meta,
            'items': paginated_items,
            'query_string': search_query,
            'is_searching': is_searching,
        })

    return render_modal_workflow(
        request,
        'wagtailsnippets/chooser/choose.html', 'wagtailsnippets/chooser/choose.js',
        {
            'model_opts': model._meta,
            'items': paginated_items,
            'is_searchable': is_searchable,
            'search_form': search_form,
            'query_string': search_query,
            'is_searching': is_searching,
        }
    )


def chosen(request, app_label, model_name, id):
    model = get_snippet_model_from_url_params(app_label, model_name)
    item = get_object_or_404(model, id=id)

    snippet_json = json.dumps({
        'id': item.id,
        'string': text_type(item),
        'edit_link': reverse('wagtailsnippets:edit', args=(
            app_label, model_name, item.id))
    })

    return render_modal_workflow(
        request,
        None, 'wagtailsnippets/chooser/chosen.js',
        {
            'snippet_json': snippet_json,
        }
    )
