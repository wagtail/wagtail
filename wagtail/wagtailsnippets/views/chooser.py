import json

from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.core.urlresolvers import reverse
from django.shortcuts import render, get_object_or_404
from django.utils.six import text_type
from django.utils.translation import ugettext as _

from wagtail.wagtailadmin.modal_workflow import render_modal_workflow
from wagtail.wagtailadmin.forms import SearchForm
from wagtail.wagtailsearch.index import class_is_indexed
from wagtail.wagtailsearch.backends import get_search_backend

from wagtail.wagtailsnippets.views.snippets import get_content_type_from_url_params, get_snippet_type_name


def choose(request, content_type_app_name, content_type_model_name):
    content_type = get_content_type_from_url_params(content_type_app_name, content_type_model_name)
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
    p = request.GET.get("p", 1)
    paginator = Paginator(items, 25)

    try:
        paginated_items = paginator.page(p)
    except PageNotAnInteger:
        paginated_items = paginator.page(1)
    except EmptyPage:
        paginated_items = paginator.page(paginator.num_pages)

    # If paginating or searching, render "results.html"
    if request.GET.get('results', None) == 'true':
        return render(request, "wagtailsnippets/chooser/results.html", {
            'content_type': content_type,
            'snippet_type_name': snippet_type_name,
            'items': paginated_items,
            'query_string': search_query,
            'is_searching': is_searching,
        })

    return render_modal_workflow(
        request,
        'wagtailsnippets/chooser/choose.html', 'wagtailsnippets/chooser/choose.js',
        {
            'content_type': content_type,
            'snippet_type_name': snippet_type_name,
            'items': paginated_items,
            'is_searchable': is_searchable,
            'search_form': search_form,
            'query_string': search_query,
            'is_searching': is_searching,
        }
    )


def chosen(request, content_type_app_name, content_type_model_name, id):
    content_type = get_content_type_from_url_params(content_type_app_name, content_type_model_name)
    model = content_type.model_class()
    item = get_object_or_404(model, id=id)

    snippet_json = json.dumps({
        'id': item.id,
        'string': text_type(item),
        'edit_link': reverse('wagtailsnippets:edit', args=(content_type_app_name, content_type_model_name, item.id,))
    })

    return render_modal_workflow(
        request,
        None, 'wagtailsnippets/chooser/chosen.js',
        {
            'snippet_json': snippet_json,
        }
    )
