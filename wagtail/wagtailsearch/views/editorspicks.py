from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import permission_required
from django.contrib import messages

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils.translation import ugettext as _
from django.views.decorators.vary import vary_on_headers

from wagtail.wagtailsearch import models, forms
from wagtail.wagtailadmin.forms import SearchForm


@permission_required('wagtailadmin.access_admin')
@vary_on_headers('X-Requested-With')
def index(request):
    is_searching = False
    page = request.GET.get('p', 1)
    query_string = request.GET.get('q', "")

    queries = models.Query.objects.filter(editors_picks__isnull=False).distinct()

    # Search
    if query_string:
        queries = queries.filter(query_string__icontains=query_string)
        is_searching = True

    # Pagination
    paginator = Paginator(queries, 20)
    try:
        queries = paginator.page(page)
    except PageNotAnInteger:
        queries = paginator.page(1)
    except EmptyPage:
        queries = paginator.page(paginator.num_pages)

    if request.is_ajax():
        return render(request, "wagtailsearch/editorspicks/results.html", {
            'is_searching': is_searching,
            'queries': queries,
            'query_string': query_string,
        })
    else:
        return render(request, 'wagtailsearch/editorspicks/index.html', {
            'is_searching': is_searching,
            'queries': queries,
            'query_string': query_string,
            'search_form': SearchForm(data=dict(q=query_string) if query_string else None, placeholder=_("Search editor's picks")),
        })


def save_editorspicks(query, new_query, editors_pick_formset):
    # Save
    if editors_pick_formset.is_valid():
        # Set sort_order
        for i, form in enumerate(editors_pick_formset.ordered_forms):
            form.instance.sort_order = i

            # Make sure the form is marked as changed so it gets saved with the new order
            form.has_changed = lambda: True

        editors_pick_formset.save()

        # If query was changed, move all editors picks to the new query
        if query != new_query:
            editors_pick_formset.get_queryset().update(query=new_query)

        return True
    else:
        return False


@permission_required('wagtailadmin.access_admin')
def add(request):
    if request.POST:
        # Get query
        query_form = forms.QueryForm(request.POST)
        if query_form.is_valid():
            query = models.Query.get(query_form['query_string'].value())

            # Save editors picks
            editors_pick_formset = forms.EditorsPickFormSet(request.POST, instance=query)
            if save_editorspicks(query, query, editors_pick_formset):
                messages.success(request, _("Editor's picks for '{0}' created.").format(query))
                return redirect('wagtailsearch_editorspicks_index')
            else:
                if len(editors_pick_formset.non_form_errors()):
                    messages.error(request, " ".join(error for error in editors_pick_formset.non_form_errors()))  # formset level error (e.g. no forms submitted)
                else:
                    messages.error(request, _("Recommendations have not been created due to errors"))  # specific errors will be displayed within form fields
        else:
            editors_pick_formset = forms.EditorsPickFormSet()
    else:
        query_form = forms.QueryForm()
        editors_pick_formset = forms.EditorsPickFormSet()

    return render(request, 'wagtailsearch/editorspicks/add.html', {
        'query_form': query_form,
        'editors_pick_formset': editors_pick_formset,
    })


@permission_required('wagtailadmin.access_admin')
def edit(request, query_id):
    query = get_object_or_404(models.Query, id=query_id)

    if request.POST:
        # Get query
        query_form = forms.QueryForm(request.POST)
        # and the recommendations
        editors_pick_formset = forms.EditorsPickFormSet(request.POST, instance=query)

        if query_form.is_valid():
            new_query = models.Query.get(query_form['query_string'].value())

            # Save editors picks
            if save_editorspicks(query, new_query, editors_pick_formset):
                messages.success(request, _("Editor's picks for '{0}' updated.").format(new_query))
                return redirect('wagtailsearch_editorspicks_index')
            else:
                if len(editors_pick_formset.non_form_errors()):
                    messages.error(request, " ".join(error for error in editors_pick_formset.non_form_errors()))  # formset level error (e.g. no forms submitted)
                else:
                    messages.error(request, _("Recommendations have not been saved due to errors"))  # specific errors will be displayed within form fields

    else:
        query_form = forms.QueryForm(initial=dict(query_string=query.query_string))
        editors_pick_formset = forms.EditorsPickFormSet(instance=query)

    return render(request, 'wagtailsearch/editorspicks/edit.html', {
        'query_form': query_form,
        'editors_pick_formset': editors_pick_formset,
        'query': query,
    })


@permission_required('wagtailadmin.access_admin')
def delete(request, query_id):
    query = get_object_or_404(models.Query, id=query_id)

    if request.POST:
        query.editors_picks.all().delete()
        messages.success(request, _("Editor's picks deleted."))
        return redirect('wagtailsearch_editorspicks_index')

    return render(request, 'wagtailsearch/editorspicks/confirm_delete.html', {
        'query': query,
    })
