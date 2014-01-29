from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from wagtail.wagtailcore import models
from wagtail.wagtailsearch import Search
from wagtail.wagtailsearch.models import Query
import json


def search(request):
    query_string = request.GET.get("q", "")
    page = request.GET.get("p", 1)

    # Search
    if query_string != "":
        search_results = models.Page.search_frontend(query_string)

        # Get query object
        query = Query.get(query_string)

        # Add hit
        query.add_hit()

        # Pagination
        paginator = Paginator(search_results, 10)
        if paginator is not None:
            try:
                search_results = paginator.page(page)
            except PageNotAnInteger:
                search_results = paginator.page(1)
            except EmptyPage:
                search_results = paginator.page(paginator.num_pages)
        else:
            search_results = None
    else:
        query = None
        search_results = None

    # Render
    if request.is_ajax():
        template_name = getattr(settings, "WAGTAILSEARCH_RESULTS_TEMPLATE_AJAX", "wagtailsearch/search_results.html")
    else:
        template_name = getattr(settings, "WAGTAILSEARCH_RESULTS_TEMPLATE", "wagtailsearch/search_results.html")
    return render(request, template_name, dict(query_string=query_string, search_results=search_results, is_ajax=request.is_ajax(), query=query))


def suggest(request):
    query_string = request.GET.get("q", "")

    # Search
    if query_string != "":
        search_results = models.Page.title_search_frontend(query_string)[:5]

        # Get list of suggestions
        suggestions = []
        for result in search_results:
            search_name = result.specific.search_name

            suggestions.append({
                "label": result.title,
                "type": search_name if search_name else '',
                "url": result.url,
            })

        return HttpResponse(json.dumps(suggestions))
    else:
        return HttpResponse("[]")