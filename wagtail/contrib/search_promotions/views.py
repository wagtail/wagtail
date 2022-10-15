from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Sum, functions
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.vary import vary_on_headers

from wagtail.admin import messages
from wagtail.admin.auth import any_permission_required, permission_required
from wagtail.admin.forms.search import SearchForm
from wagtail.contrib.search_promotions import forms
from wagtail.log_actions import log
from wagtail.search import forms as search_forms
from wagtail.search.models import Query


@any_permission_required(
    "wagtailsearchpromotions.add_searchpromotion",
    "wagtailsearchpromotions.change_searchpromotion",
    "wagtailsearchpromotions.delete_searchpromotion",
)
@vary_on_headers("X-Requested-With")
def index(request):
    # Ordering
    valid_ordering = ["query_string", "-query_string", "views", "-views"]
    ordering = valid_ordering[0]

    if "ordering" in request.GET and request.GET["ordering"] in valid_ordering:
        ordering = request.GET["ordering"]

    # Query
    queries = Query.objects.filter(editors_picks__isnull=False).distinct()

    if "views" in ordering:
        queries = queries.annotate(views=functions.Coalesce(Sum("daily_hits__hits"), 0))

    queries = queries.order_by(ordering)

    # Search
    is_searching = False
    query_string = request.GET.get("q", "")

    if query_string:
        queries = queries.filter(query_string__icontains=query_string)
        is_searching = True

    # Paginate
    paginator = Paginator(queries, per_page=20)
    queries = paginator.get_page(request.GET.get("p"))

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return TemplateResponse(
            request,
            "wagtailsearchpromotions/results.html",
            {
                "is_searching": is_searching,
                "ordering": ordering,
                "queries": queries,
                "query_string": query_string,
            },
        )
    else:
        return TemplateResponse(
            request,
            "wagtailsearchpromotions/index.html",
            {
                "is_searching": is_searching,
                "ordering": ordering,
                "queries": queries,
                "query_string": query_string,
                "search_form": SearchForm(
                    data={"q": query_string} if query_string else None,
                    placeholder=_("Search promoted results"),
                ),
            },
        )


def save_searchpicks(query, new_query, searchpicks_formset):
    # Save
    if searchpicks_formset.is_valid():
        # Set sort_order
        for i, form in enumerate(searchpicks_formset.ordered_forms):
            form.instance.sort_order = i

            # Make sure the form is marked as changed so it gets saved with the new order
            form.has_changed = lambda: True

        # log deleted items before saving, otherwise we lose their IDs
        items_for_deletion = [
            form.instance
            for form in searchpicks_formset.deleted_forms
            if form.instance.pk
        ]
        with transaction.atomic():
            for search_pick in items_for_deletion:
                log(search_pick, "wagtail.delete")

            searchpicks_formset.save()

            for search_pick in searchpicks_formset.new_objects:
                log(search_pick, "wagtail.create")

            # If query was changed, move all search picks to the new query
            if query != new_query:
                searchpicks_formset.get_queryset().update(query=new_query)
                # log all items in the formset as having changed
                for search_pick, changed_fields in searchpicks_formset.changed_objects:
                    log(search_pick, "wagtail.edit")
            else:
                # only log objects with actual changes
                for search_pick, changed_fields in searchpicks_formset.changed_objects:
                    if changed_fields:
                        log(search_pick, "wagtail.edit")

        return True
    else:
        return False


@permission_required("wagtailsearchpromotions.add_searchpromotion")
def add(request):
    if request.method == "POST":
        # Get query
        query_form = search_forms.QueryForm(request.POST)
        if query_form.is_valid():
            query = Query.get(query_form["query_string"].value())

            # Save search picks
            searchpicks_formset = forms.SearchPromotionsFormSet(
                request.POST, instance=query
            )
            if save_searchpicks(query, query, searchpicks_formset):
                for search_pick in searchpicks_formset.new_objects:
                    log(search_pick, "wagtail.create")
                messages.success(
                    request,
                    _("Editor's picks for '%(query)s' created.") % {"query": query},
                    buttons=[
                        messages.button(
                            reverse("wagtailsearchpromotions:edit", args=(query.id,)),
                            _("Edit"),
                        )
                    ],
                )
                return redirect("wagtailsearchpromotions:index")
            else:
                if len(searchpicks_formset.non_form_errors()):
                    # formset level error (e.g. no forms submitted)
                    messages.error(
                        request,
                        " ".join(
                            error for error in searchpicks_formset.non_form_errors()
                        ),
                    )
                else:
                    # specific errors will be displayed within form fields
                    messages.error(
                        request,
                        _("Recommendations have not been created due to errors"),
                    )
        else:
            searchpicks_formset = forms.SearchPromotionsFormSet()
    else:
        query_form = search_forms.QueryForm()
        searchpicks_formset = forms.SearchPromotionsFormSet()

    return TemplateResponse(
        request,
        "wagtailsearchpromotions/add.html",
        {
            "query_form": query_form,
            "searchpicks_formset": searchpicks_formset,
            "form_media": query_form.media + searchpicks_formset.media,
        },
    )


@permission_required("wagtailsearchpromotions.change_searchpromotion")
def edit(request, query_id):
    query = get_object_or_404(Query, id=query_id)

    if request.method == "POST":
        # Get query
        query_form = search_forms.QueryForm(request.POST)
        # and the recommendations
        searchpicks_formset = forms.SearchPromotionsFormSet(
            request.POST, instance=query
        )

        if query_form.is_valid():
            new_query = Query.get(query_form["query_string"].value())

            # Save search picks
            if save_searchpicks(query, new_query, searchpicks_formset):
                messages.success(
                    request,
                    _("Editor's picks for '%(query)s' updated.") % {"query": new_query},
                    buttons=[
                        messages.button(
                            reverse("wagtailsearchpromotions:edit", args=(query.id,)),
                            _("Edit"),
                        )
                    ],
                )
                return redirect("wagtailsearchpromotions:index")
            else:
                if len(searchpicks_formset.non_form_errors()):
                    messages.error(
                        request,
                        " ".join(
                            error for error in searchpicks_formset.non_form_errors()
                        ),
                    )
                    # formset level error (e.g. no forms submitted)
                else:
                    messages.error(
                        request, _("Recommendations have not been saved due to errors")
                    )
                    # specific errors will be displayed within form fields

    else:
        query_form = search_forms.QueryForm(
            initial={"query_string": query.query_string}
        )
        searchpicks_formset = forms.SearchPromotionsFormSet(instance=query)

    return TemplateResponse(
        request,
        "wagtailsearchpromotions/edit.html",
        {
            "query_form": query_form,
            "searchpicks_formset": searchpicks_formset,
            "query": query,
            "form_media": query_form.media + searchpicks_formset.media,
        },
    )


@permission_required("wagtailsearchpromotions.delete_searchpromotion")
def delete(request, query_id):
    query = get_object_or_404(Query, id=query_id)

    if request.method == "POST":
        editors_picks = query.editors_picks.all()
        with transaction.atomic():
            for search_pick in editors_picks:
                log(search_pick, "wagtail.delete")
            editors_picks.delete()
        messages.success(request, _("Editor's picks deleted."))
        return redirect("wagtailsearchpromotions:index")

    return TemplateResponse(
        request,
        "wagtailsearchpromotions/confirm_delete.html",
        {
            "query": query,
        },
    )
