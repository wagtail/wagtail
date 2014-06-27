from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import permission_required

from wagtail.wagtailadmin.modal_workflow import render_modal_workflow
from wagtail.wagtailadmin.forms import SearchForm

from wagtail.wagtailsearch import models
from wagtail.wagtailsearch.utils import normalise_query_string


@permission_required('wagtailadmin.access_admin')
def chooser(request, get_results=False):
    # Get most popular queries
    queries = models.Query.get_most_popular()

    # If searching, filter results by query string
    query_string = None
    if 'q' in request.GET:
        searchform = SearchForm(request.GET)
        if searchform.is_valid():
            query_string = searchform.cleaned_data['q']
            queries = queries.filter(query_string__icontains=normalise_query_string(query_string))
    else:
        searchform = SearchForm()

    # Pagination
    p = request.GET.get('p', 1)

    paginator = Paginator(queries, 10)
    try:
        queries = paginator.page(p)
    except PageNotAnInteger:
        queries = paginator.page(1)
    except EmptyPage:
        queries = paginator.page(paginator.num_pages)

    # Render
    if get_results:
        return render(request, "wagtailsearch/queries/chooser/results.html", {
            'queries': queries,
            'query_string': query_string,
        })
    else:
        return render_modal_workflow(request, 'wagtailsearch/queries/chooser/chooser.html', 'wagtailsearch/queries/chooser/chooser.js', {
            'queries': queries,
            'searchform': searchform,
            'query_string': query_string,
        })


def chooserresults(request):
    return chooser(request, get_results=True)
