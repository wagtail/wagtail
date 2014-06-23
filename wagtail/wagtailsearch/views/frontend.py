import json

from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from django.views.generic.base import View, TemplateResponseMixin
from django.views.generic.list import MultipleObjectMixin


from wagtail.wagtailcore import models
from wagtail.wagtailsearch.models import Query
from wagtail.wagtailsearch.backends import get_search_backend


def search(
        request,
        template=None,
        template_ajax=None,
        results_per_page=10,
        use_json=False,
        json_attrs=['title', 'url'],
        show_unpublished=False,
        search_title_only=False,
        extra_filters={},
        path=None,
    ):

    # Get default templates
    if template is None:
        if hasattr(settings, 'WAGTAILSEARCH_RESULTS_TEMPLATE'):
            template = settings.WAGTAILSEARCH_RESULTS_TEMPLATE
        else:
            template = 'wagtailsearch/search_results.html'

    if template_ajax is None:
        if hasattr(settings, 'WAGTAILSEARCH_RESULTS_TEMPLATE_AJAX'):
            template_ajax = settings.WAGTAILSEARCH_RESULTS_TEMPLATE_AJAX
        else:
            template_ajax = template

    # Get query string and page from GET paramters
    query_string = request.GET.get('q', '')
    page = request.GET.get('p', 1)

    # Search
    if query_string != '':
        search_results = models.Page.search(
            query_string,
            show_unpublished=show_unpublished,
            search_title_only=search_title_only,
            extra_filters=extra_filters,
            path=path if path else request.site.root_page.path
        )

        # Get query object
        query = Query.get(query_string)

        # Add hit
        query.add_hit()

        # Pagination
        paginator = Paginator(search_results, results_per_page)
        try:
            search_results = paginator.page(page)
        except PageNotAnInteger:
            search_results = paginator.page(1)
        except EmptyPage:
            search_results = paginator.page(paginator.num_pages)
    else:
        query = None
        search_results = None

    if use_json: # Return a json response
        if search_results:
            search_results_json = []
            for result in search_results:
                result_specific = result.specific

                search_results_json.append(dict(
                    (attr, getattr(result_specific, attr))
                    for attr in json_attrs
                    if hasattr(result_specific, attr)
                ))

            return HttpResponse(json.dumps(search_results_json))
        else:
            return HttpResponse('[]')
    else: # Render a template
        if request.is_ajax() and template_ajax:
            template = template_ajax

        return render(request, template, dict(
            query_string=query_string,
            search_results=search_results,
            is_ajax=request.is_ajax(),
            query=query
        ))


class SearchView(MultipleObjectMixin, TemplateResponseMixin, View):
    search_backend = 'default'
    fields = None
    template_name = 'wagtailsearch/search_results.html'

    def get_search_backend(self):
        return get_search_backend(self.search_backend)

    def get_fields(self):
        return self.fields

    def get_results(self, query_string):
        backend = self.get_search_backend()
        queryset = self.get_queryset()
        fields = self.get_fields()

        return backend.search(query_string, queryset, fields=fields)

    def get(self, request, *args, **kwargs):
        # Get query string
        self.query_string = request.GET.get('q', None)

        if self.query_string:
            # Get results
            self.object_list = self.get_results(self.query_string)

            # Get query object
            self.query = Query.get(self.query_string)

            # Add hit
            self.query.add_hit()
        else:
            self.object_list = []
            self.query = None

        allow_empty = self.get_allow_empty()

        if not allow_empty:
            # When pagination is enabled and object_list is a queryset,
            # it's better to do a cheap query than to load the unpaginated
            # queryset in memory.
            if (self.get_paginate_by(self.object_list) is not None
                    and hasattr(self.object_list, 'exists')):
                is_empty = not self.object_list.exists()
            else:
                is_empty = len(self.object_list) == 0
            if is_empty:
                raise Http404(_("Empty list and '%(class_name)s.allow_empty' is False.")
                        % {'class_name': self.__class__.__name__})
        context = self.get_context_data()
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super(SearchView, self).get_context_data(**kwargs)
        context.update({
            'query_string': self.query_string,
            'query': self.query,
            'search_results': self.object_list,
        })
        return context
