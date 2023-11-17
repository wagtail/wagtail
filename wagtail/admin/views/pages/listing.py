from django.conf import settings
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _

from wagtail import hooks
from wagtail.admin.forms.search import SearchForm
from wagtail.admin.ui.components import MediaContainer
from wagtail.admin.ui.side_panels import (
    PageStatusSidePanel,
)
from wagtail.admin.ui.tables import Column, DateColumn
from wagtail.admin.ui.tables.pages import (
    BulkActionsColumn,
    NavigateToChildrenColumn,
    OrderingColumn,
    PageStatusColumn,
    PageTable,
    PageTitleColumn,
)
from wagtail.admin.views.generic.base import BaseListingView
from wagtail.admin.views.generic.permissions import PermissionCheckedMixin
from wagtail.permission_policies.pages import Page, PagePermissionPolicy


class BaseIndexView(PermissionCheckedMixin, BaseListingView):
    permission_policy = PagePermissionPolicy()
    any_permission_required = {
        "add",
        "change",
        "publish",
        "bulk_delete",
        "lock",
        "unlock",
    }
    context_object_name = "pages"
    page_kwarg = "p"
    paginate_by = 50
    table_class = PageTable
    table_classname = "listing full-width"

    columns = [
        BulkActionsColumn("bulk_actions", width="10px"),
        PageTitleColumn(
            "title",
            label=_("Title"),
            sort_key="title",
            classname="title",
        ),
        DateColumn(
            "latest_revision_created_at",
            label=_("Updated"),
            sort_key="latest_revision_created_at",
            width="12%",
        ),
        Column(
            "type",
            label=_("Type"),
            accessor="page_type_display_name",
            sort_key="content_type",
            width="12%",
        ),
        PageStatusColumn(
            "status",
            label=_("Status"),
            sort_key="live",
            width="12%",
        ),
        NavigateToChildrenColumn("navigate", width="10%"),
    ]

    def get(self, request, parent_page_id=None):
        if parent_page_id:
            self.parent_page = get_object_or_404(
                Page.objects.all().prefetch_workflow_states(), id=parent_page_id
            )
        else:
            self.parent_page = Page.get_first_root_node()

        # This will always succeed because of the check performed by PermissionCheckedMixin.
        root_page = self.permission_policy.explorable_root_instance(request.user)

        # If this page isn't a descendant of the user's explorable root page,
        # then redirect to that explorable root page instead.
        if not (
            self.parent_page.pk == root_page.pk
            or self.parent_page.is_descendant_of(root_page)
        ):
            return redirect("wagtailadmin_explore", root_page.pk)

        self.parent_page = self.parent_page.specific
        self.scheduled_page = self.parent_page.get_scheduled_revision_as_object()

        if (
            getattr(settings, "WAGTAIL_I18N_ENABLED", False)
            and not self.parent_page.is_root()
        ):
            self.locale = self.parent_page.locale
            self.translations = self.get_translations()
        else:
            self.locale = None
            self.translations = []

        # Search
        self.query_string = None
        self.is_searching = False
        self.is_searching_whole_tree = False
        if "q" in self.request.GET:
            self.search_form = SearchForm(
                self.request.GET, placeholder=_("Search pages…")
            )
            if self.search_form.is_valid():
                self.query_string = self.search_form.cleaned_data["q"]
        else:
            self.search_form = SearchForm(placeholder=_("Search pages…"))

        if self.query_string:
            self.is_searching = True
            self.is_searching_whole_tree = bool(self.request.GET.get("search_all"))

        return super().get(request)

    def get_ordering(self):
        valid_orderings = [
            "title",
            "-title",
            "live",
            "-live",
            "latest_revision_created_at",
            "-latest_revision_created_at",
        ]

        if self.query_string:
            # default to ordering by relevance
            default_ordering = None
        else:
            default_ordering = "-latest_revision_created_at"
            # ordering by page order is only available when not searching
            valid_orderings.append("ord")

            # ordering by content type not currently available when searching, due to
            # https://github.com/wagtail/wagtail/issues/6616
            valid_orderings.append("content_type")
            valid_orderings.append("-content_type")

        ordering = self.request.GET.get("ordering", default_ordering)
        if ordering not in valid_orderings:
            ordering = default_ordering

        return ordering

    def get_queryset(self):
        if self.is_searching:
            if self.is_searching_whole_tree:
                pages = Page.objects.all()
            else:
                pages = self.parent_page.get_descendants()
        else:
            pages = self.parent_page.get_children()

        pages = pages.prefetch_related(
            "content_type", "sites_rooted_here"
        ) & self.permission_policy.explorable_instances(self.request.user)

        self.ordering = self.get_ordering()

        if not self.is_searching:
            if self.ordering == "ord":
                # preserve the native ordering from get_children()
                pass
            elif self.ordering == "latest_revision_created_at":
                # order by oldest revision first.
                # Special case NULL entries - these should go at the top of the list.
                # Do this by annotating with Count('latest_revision_created_at'),
                # which returns 0 for these
                pages = pages.annotate(
                    null_position=Count("latest_revision_created_at")
                ).order_by("null_position", "latest_revision_created_at")
            elif self.ordering == "-latest_revision_created_at":
                # order by oldest revision first.
                # Special case NULL entries - these should go at the end of the list.
                pages = pages.annotate(
                    null_position=Count("latest_revision_created_at")
                ).order_by("-null_position", "-latest_revision_created_at")
            else:
                pages = pages.order_by(self.ordering)

        # We want specific page instances, but do not need streamfield values here
        pages = pages.defer_streamfields().specific()

        # allow hooks defer_streamfieldsyset
        for hook in hooks.get_hooks("construct_explorer_page_queryset"):
            pages = hook(self.parent_page, pages, self.request)

        # Annotate queryset with various states to be used later for performance optimisations
        if getattr(settings, "WAGTAIL_WORKFLOW_ENABLED", True):
            pages = pages.prefetch_workflow_states()

        pages = pages.annotate_site_root_state().annotate_approved_schedule()

        if self.is_searching:
            if self.ordering:
                pages = pages.order_by(self.ordering).autocomplete(
                    self.query_string, order_by_relevance=False
                )
            else:
                pages = pages.autocomplete(self.query_string)

        return pages

    def get_paginate_by(self, queryset):
        if self.ordering == "ord":
            # Don't paginate if sorting by page order - all pages must be shown to
            # allow drag-and-drop reordering
            return None
        else:
            return self.paginate_by

    def paginate_queryset(self, queryset, page_size):
        return super().paginate_queryset(queryset, page_size)

    def get_index_url(self):
        return reverse("wagtailadmin_explore", args=[self.parent_page.id])

    def get_results_url(self):
        return reverse("wagtailadmin_explore_results", args=[self.parent_page.id])

    def get_table_kwargs(self):
        kwargs = super().get_table_kwargs()
        kwargs["use_row_ordering_attributes"] = self.show_ordering_column
        kwargs["parent_page"] = self.parent_page
        kwargs["show_locale_labels"] = self.i18n_enabled and self.parent_page.is_root()
        kwargs["actions_next_url"] = self.get_index_url()

        if self.show_ordering_column:
            kwargs["attrs"] = {
                "aria-description": gettext(
                    "Press enter to select an item, use up and down arrows to move the item, press enter to complete the move or escape to cancel the current move."
                )
            }
        return kwargs

    def get_context_data(self, **kwargs):
        self.show_ordering_column = self.ordering == "ord"
        if self.show_ordering_column:
            self.columns = self.columns.copy()
            self.columns[0] = OrderingColumn("ordering", width="10px", sort_key="ord")
        self.i18n_enabled = getattr(settings, "WAGTAIL_I18N_ENABLED", False)

        context = super().get_context_data(**kwargs)

        if self.is_searching:
            # postprocess this page of results to annotate each result with its parent page
            parent_page_paths = {
                page.path[: -page.steplen] for page in context["object_list"]
            }
            parent_pages_by_path = {
                page.path: page
                for page in Page.objects.filter(path__in=parent_page_paths).specific()
            }
            for page in context["object_list"]:
                parent_page = parent_pages_by_path.get(page.path[: -page.steplen])
                # add annotation if parent page is found and is not the currently viewed parent
                if parent_page and parent_page != self.parent_page:
                    page.annotated_parent_page = parent_page

        context.update(
            {
                "parent_page": self.parent_page,
                "ordering": self.ordering,
                "index_url": self.get_index_url(),
                "results_url": self.get_results_url(),
                "search_form": self.search_form,
                "is_searching": self.is_searching,
                "is_searching_whole_tree": self.is_searching_whole_tree,
            }
        )

        return context

    def get_translations(self):
        return [
            {
                "locale": translation.locale,
                "url": reverse("wagtailadmin_explore", args=[translation.id]),
            }
            for translation in self.parent_page.get_translations()
            .only("id", "locale")
            .select_related("locale")
        ]


class IndexView(BaseIndexView):
    template_name = "wagtailadmin/pages/index.html"

    def get_side_panels(self):
        side_panels = [
            PageStatusSidePanel(
                self.parent_page.get_latest_revision_as_object(),
                self.request,
                show_schedule_publishing_toggle=False,
                live_object=self.parent_page,
                scheduled_object=self.scheduled_page,
                locale=self.locale,
                translations=self.translations,
            ),
        ]
        return MediaContainer(side_panels)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        side_panels = self.get_side_panels()
        context.update(
            {
                "side_panels": side_panels,
                "media": side_panels.media,
            }
        )
        return context


class IndexResultsView(BaseIndexView):
    template_name = "wagtailadmin/pages/index_results.html"
