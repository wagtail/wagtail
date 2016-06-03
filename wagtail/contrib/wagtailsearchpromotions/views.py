from __future__ import absolute_import, unicode_literals

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.db.models.aggregates import Sum
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import ugettext as _
from django.views.decorators.vary import vary_on_headers

from wagtail.contrib.wagtailsearchpromotions import forms
from wagtail.utils.pagination import paginate
from wagtail.wagtailadmin import messages
from wagtail.wagtailadmin.forms import SearchForm
from wagtail.wagtailadmin.utils import any_permission_required, permission_required
from wagtail.wagtailsearch import forms as search_forms
from wagtail.wagtailsearch.models import Query


query_editor_setting = 'WAGTAILSEARCHPROMOTIONS_QUERY_EDITOR'

# If acting as query editor, allow saving a query with no promotions
if getattr(settings, query_editor_setting, False):
    forms.SearchPromotionsFormSet.minimum_forms = 0


# Factored out for reuse as public-facing "top searches"
def get_hit_queryset():
    queryset = Query.objects.filter(
        Q(daily_hits__isnull=False) | Q(editors_picks__isnull=False))
    queryset = Query.objects.filter(pk__in=queryset).annotate(_hits=Coalesce(Sum('daily_hits__hits'), 0))
    return queryset.order_by('-_hits', 'query_string')


def get_promoted_queryset():
    return Query.objects.filter(editors_picks__isnull=False).distinct()


@any_permission_required(
    'wagtailsearchpromotions.add_searchpromotion',
    'wagtailsearchpromotions.change_searchpromotion',
    'wagtailsearchpromotions.delete_searchpromotion'
)
@vary_on_headers('X-Requested-With')
def index(request):
    is_editor = getattr(settings, query_editor_setting, False)
    is_searching = False
    queries_count = None
    query_string = request.GET.get('q', "")

    if is_editor:
        queries = get_hit_queryset()
    else:
        queries = get_promoted_queryset()

    # Search
    if query_string:
        queries = queries.filter(query_string__icontains=query_string)
        is_searching = True
        queries_count = queries.count()

    paginator, queries = paginate(request, queries)

    if request.is_ajax():
        return render(request, "wagtailsearchpromotions/results.html", {
            'is_editor': is_editor,
            'is_searching': is_searching,
            'queries': queries,
            'queries_count': queries_count,
            'query_string': query_string,
        })
    else:
        return render(request, 'wagtailsearchpromotions/index.html', {
            'is_editor': is_editor,
            'is_searching': is_searching,
            'queries': queries,
            'query_string': query_string,
            'search_form': SearchForm(
                data=dict(q=query_string) if query_string else None,
                placeholder=_("Search all terms" if is_editor else "Search promoted results")
            ),
        })


def save_searchpicks(query, new_query, searchpicks_formset):
    # Save
    if searchpicks_formset.is_valid():
        # Set sort_order
        for i, form in enumerate(searchpicks_formset.ordered_forms):
            form.instance.sort_order = i

            # Make sure the form is marked as changed so it gets saved with the new order
            form.has_changed = lambda: True

        searchpicks_formset.save()

        # If query was changed, move all search picks to the new query
        if query != new_query:
            searchpicks_formset.get_queryset().update(query=new_query)

        return True
    else:
        return False


@permission_required('wagtailsearchpromotions.add_searchpromotion')
def add(request):
    if request.method == 'POST':
        # Get query
        query_form = search_forms.QueryForm(request.POST)
        if query_form.is_valid():
            query = Query.get(query_form['query_string'].value())

            # Save search picks
            searchpicks_formset = forms.SearchPromotionsFormSet(request.POST, instance=query)
            if save_searchpicks(query, query, searchpicks_formset):
                messages.success(request, _("Editor's picks for '{0}' created.").format(query), buttons=[
                    messages.button(reverse('wagtailsearchpromotions:edit', args=(query.id,)), _('Edit'))
                ])
                return redirect('wagtailsearchpromotions:index')
            else:
                if len(searchpicks_formset.non_form_errors()):
                    # formset level error (e.g. no forms submitted)
                    messages.error(request, " ".join(error for error in searchpicks_formset.non_form_errors()))
                else:
                    # specific errors will be displayed within form fields
                    messages.error(request, _("Recommendations have not been created due to errors"))
        else:
            searchpicks_formset = forms.SearchPromotionsFormSet()
    else:
        query_form = search_forms.QueryForm()
        searchpicks_formset = forms.SearchPromotionsFormSet()

    return render(request, 'wagtailsearchpromotions/add.html', {
        'query_form': query_form,
        'searchpicks_formset': searchpicks_formset,
    })


@permission_required('wagtailsearchpromotions.change_searchpromotion')
def edit(request, query_id):
    query = get_object_or_404(Query, id=query_id)

    if request.method == 'POST':
        # Get query
        query_form = search_forms.QueryForm(request.POST)
        # and the recommendations
        searchpicks_formset = forms.SearchPromotionsFormSet(request.POST, instance=query)

        if query_form.is_valid():
            new_query = Query.get(query_form['query_string'].value())

            # Save search picks
            if save_searchpicks(query, new_query, searchpicks_formset):
                messages.success(request, _("Editor's picks for '{0}' updated.").format(new_query), buttons=[
                    messages.button(reverse('wagtailsearchpromotions:edit', args=(query.id,)), _('Edit'))
                ])
                return redirect('wagtailsearchpromotions:index')
            else:
                if len(searchpicks_formset.non_form_errors()):
                    messages.error(request, " ".join(error for error in searchpicks_formset.non_form_errors()))
                    # formset level error (e.g. no forms submitted)
                else:
                    messages.error(request, _("Recommendations have not been saved due to errors"))
                    # specific errors will be displayed within form fields

    else:
        query_form = search_forms.QueryForm(initial=dict(query_string=query.query_string))
        searchpicks_formset = forms.SearchPromotionsFormSet(instance=query)

    return render(request, 'wagtailsearchpromotions/edit.html', {
        'query_form': query_form,
        'searchpicks_formset': searchpicks_formset,
        'query': query,
    })


@permission_required('wagtailsearchpromotions.delete_searchpromotion')
def delete(request, query_id):
    is_editor = getattr(settings, query_editor_setting, False)
    query = get_object_or_404(Query, id=query_id)

    if request.method == 'POST':
        if is_editor:
            query.delete()
        else:
            query.editors_picks.all().delete()
        messages.success(request, _("Editor's picks deleted."))
        return redirect('wagtailsearchpromotions:index')

    return render(request, 'wagtailsearchpromotions/confirm_delete.html', {
        'is_editor': is_editor,
        'query': query,
    })
