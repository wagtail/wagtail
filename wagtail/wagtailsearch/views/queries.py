from django.shortcuts import get_object_or_404, render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import login_required

from wagtail.wagtailadmin.modal_workflow import render_modal_workflow
from wagtail.wagtailadmin.forms import SearchForm
from wagtail.wagtailsearch import models


@login_required
def chooser(request, get_results=False):
    # Get most popular queries
    queries = models.Query.get_most_popular()

    # If searching, filter results by query string
    if 'q' in request.GET:
        searchform = SearchForm(request.GET)
        if searchform.is_valid():
            q = searchform.cleaned_data['q']
            queries = queries.filter(query_string__icontains=models.Query.normalise_query_string(q))
            is_searching = True
        else:
            is_searching = False
    else:
        searchform = SearchForm()
        is_searching = False

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
            'is_searching': is_searching,
        })
    else:
        return render_modal_workflow(request, 'wagtailsearch/queries/chooser/chooser.html', 'wagtailsearch/queries/chooser/chooser.js',{
            'queries': queries,
            'searchform': searchform,
            'is_searching': False,
        })

def chooserresults(request):
    return chooser(request, get_results=True)