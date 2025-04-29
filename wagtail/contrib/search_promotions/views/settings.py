from django.core.paginator import InvalidPage, Paginator
from django.db import transaction
from django.db.models import Sum, functions
from django.http import Http404
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy

from wagtail.admin import messages
from wagtail.admin.forms.search import SearchForm
from wagtail.admin.modal_workflow import render_modal_workflow
from wagtail.admin.ui.tables import (
    NumberColumn,
    RelatedObjectsColumn,
    TitleColumn,
)
from wagtail.admin.views import generic
from wagtail.contrib.search_promotions import forms, models
from wagtail.contrib.search_promotions.models import Query, SearchPromotion
from wagtail.log_actions import log
from wagtail.permission_policies.base import ModelPermissionPolicy
from wagtail.search.utils import normalise_query_string


class SearchPromotionColumn(RelatedObjectsColumn):
    cell_template_name = "wagtailsearchpromotions/search_promotion_column.html"


class IndexView(generic.IndexView):
    model = Query
    template_name = "wagtailsearchpromotions/index.html"
    results_template_name = "wagtailsearchpromotions/index_results.html"
    context_object_name = "queries"
    page_title = gettext_lazy("Promoted search results")
    header_icon = "pick"
    paginate_by = 20
    permission_policy = ModelPermissionPolicy(SearchPromotion)
    index_url_name = "wagtailsearchpromotions:index"
    index_results_url_name = "wagtailsearchpromotions:index_results"
    search_fields = ["query_string"]
    default_ordering = "query_string"
    add_url_name = "wagtailsearchpromotions:add"
    add_item_label = gettext_lazy("Add new promoted result")
    columns = [
        TitleColumn(
            "query_string",
            label=gettext_lazy("Search term(s)"),
            width="40%",
            url_name="wagtailsearchpromotions:edit",
            sort_key="query_string",
        ),
        SearchPromotionColumn(
            "editors_picks",
            label=gettext_lazy("Promoted results"),
            width="40%",
        ),
        NumberColumn(
            "views",
            label=gettext_lazy("Views"),
            width="20%",
            sort_key="views",
        ),
    ]

    def get_base_queryset(self):
        # Use a subquery to filter out the Query objects that do not have a
        # SearchPromotion instead of using .filter(editors_picks__isnull=False).
        # The latter would use a JOIN which would result in duplicate rows before
        # the sum is calculated, causing the sum to be incorrect.
        has_promotions = SearchPromotion.objects.values_list("query_id", flat=True)
        queryset = self.model.objects.filter(pk__in=has_promotions)

        # Prevent N+1 queries by annotating the sum instead of using the
        # Query.hits property and prefetching the related editors_picks.
        queryset = queryset.annotate(
            views=functions.Coalesce(Sum("daily_hits__hits"), 0)
        ).prefetch_related("editors_picks", "editors_picks__page")
        return queryset

    def get_breadcrumbs_items(self):
        breadcrumbs = super().get_breadcrumbs_items()
        breadcrumbs[-1]["label"] = self.get_page_title()
        return breadcrumbs


class SearchPromotionCreateEditMixin:
    model = Query
    permission_policy = ModelPermissionPolicy(SearchPromotion)
    index_url_name = "wagtailsearchpromotions:index"
    edit_url_name = "wagtailsearchpromotions:edit"
    form_class = forms.QueryForm
    header_icon = "pick"
    page_subtitle = gettext_lazy("Promoted search result")

    def get_success_message(self, instance=None):
        return self.success_message % {"query": instance}

    def get_error_message(self):
        if formset_errors := self.searchpicks_formset.non_form_errors():
            # formset level error (e.g. no forms submitted)
            return " ".join(error for error in formset_errors)
        return super().get_error_message()

    def get_breadcrumbs_items(self):
        breadcrumbs = super().get_breadcrumbs_items()
        breadcrumbs[-2]["label"] = IndexView.page_title
        return breadcrumbs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["searchpicks_formset"] = self.searchpicks_formset
        context["media"] += self.searchpicks_formset.media
        return context

    def save_searchpicks(self, query, new_query):
        searchpicks_formset = self.searchpicks_formset
        if not searchpicks_formset.is_valid():
            return False

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

    @cached_property
    def searchpicks_formset(self):
        if self.request.method == "POST":
            return forms.SearchPromotionsFormSet(
                self.request.POST, instance=self.object
            )
        return forms.SearchPromotionsFormSet(instance=self.object)

    def form_valid(self, form):
        self.form = form
        new_query = Query.get(form.cleaned_data["query_string"])
        if not self.object:
            self.object = new_query

        if self.save_searchpicks(self.object, new_query):
            messages.success(
                self.request,
                self.get_success_message(self.object),
                buttons=self.get_success_buttons(),
            )
            return redirect(self.index_url_name)

        return super().form_invalid(form)


class CreateView(SearchPromotionCreateEditMixin, generic.CreateView):
    success_message = gettext_lazy("Editor's picks for '%(query)s' created.")
    error_message = gettext_lazy("Recommendations have not been created due to errors")
    template_name = "wagtailsearchpromotions/add.html"
    add_url_name = "wagtailsearchpromotions:add"


class EditView(SearchPromotionCreateEditMixin, generic.EditView):
    pk_url_kwarg = "query_id"
    context_object_name = "query"
    delete_url_name = "wagtailsearchpromotions:delete"
    success_message = gettext_lazy("Editor's picks for '%(query)s' updated.")
    error_message = gettext_lazy("Recommendations have not been saved due to errors")
    template_name = "wagtailsearchpromotions/edit.html"


class DeleteView(generic.DeleteView):
    model = Query
    permission_policy = ModelPermissionPolicy(SearchPromotion)
    pk_url_kwarg = "query_id"
    context_object_name = "query"
    success_message = gettext_lazy("Editor's picks deleted.")
    index_url_name = "wagtailsearchpromotions:index"
    delete_url_name = "wagtailsearchpromotions:delete"
    header_icon = "pick"
    template_name = "wagtailsearchpromotions/confirm_delete.html"

    def delete_action(self):
        editors_picks = self.object.editors_picks.all()
        with transaction.atomic():
            for search_pick in editors_picks:
                log(search_pick, "wagtail.delete")
            editors_picks.delete()


def chooser(request, get_results=False):
    # Get most popular queries
    queries = models.Query.get_most_popular()

    # If searching, filter results by query string
    if "q" in request.GET:
        searchform = SearchForm(request.GET)
        if searchform.is_valid():
            query_string = searchform.cleaned_data["q"]
            queries = queries.filter(
                query_string__icontains=normalise_query_string(query_string)
            )
    else:
        searchform = SearchForm()

    paginator = Paginator(queries, per_page=10)
    try:
        queries = paginator.page(request.GET.get("p", 1))
    except InvalidPage:
        raise Http404

    # Render
    if get_results:
        return TemplateResponse(
            request,
            "wagtailsearchpromotions/queries/chooser/results.html",
            {
                "queries": queries,
            },
        )
    else:
        return render_modal_workflow(
            request,
            "wagtailsearchpromotions/queries/chooser/chooser.html",
            None,
            {
                "queries": queries,
                "searchform": searchform,
            },
            json_data={"step": "chooser"},
        )


def chooserresults(request):
    return chooser(request, get_results=True)
