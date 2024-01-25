from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import F
from django.forms import CheckboxSelectMultiple, RadioSelect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django_filters.filters import (
    ChoiceFilter,
    DateFromToRangeFilter,
    ModelMultipleChoiceFilter,
)

from wagtail import hooks
from wagtail.admin.filters import (
    DateRangePickerWidget,
    MultipleContentTypeFilter,
    MultipleUserFilter,
    WagtailFilterSet,
)
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
from wagtail.admin.views import generic
from wagtail.models import Page, PageLogEntry, Site, get_page_content_types
from wagtail.permissions import page_permission_policy


class SiteFilter(ModelMultipleChoiceFilter):
    def get_filter_predicate(self, v):
        return {"path__startswith": v.root_page.path}


class HasChildPagesFilter(ChoiceFilter):
    def filter(self, qs, value):
        if value == "true":
            return qs.filter(numchild__gt=0)
        elif value == "false":
            return qs.filter(numchild=0)
        else:  # None / empty string
            return qs


class EditedByFilter(MultipleUserFilter):
    def filter(self, qs, value):
        if value:
            qs = qs.filter(
                pk__in=PageLogEntry.objects.filter(
                    action="wagtail.edit", user__in=value
                )
                .order_by()
                .values_list("page_id", flat=True)
                .distinct()
            )
        return qs


class PageFilterSet(WagtailFilterSet):
    content_type = MultipleContentTypeFilter(
        label=_("Page type"),
        queryset=lambda request: get_page_content_types(include_base_page_type=False),
        widget=CheckboxSelectMultiple,
    )
    latest_revision_created_at = DateFromToRangeFilter(
        label=_("Date updated"),
        widget=DateRangePickerWidget,
    )
    owner = MultipleUserFilter(
        label=_("Owner"),
        queryset=(
            lambda request: get_user_model().objects.filter(
                pk__in=Page.objects.order_by()
                .values_list("owner_id", flat=True)
                .distinct()
            )
        ),
        widget=CheckboxSelectMultiple,
    )
    edited_by = EditedByFilter(
        label=_("Edited by"),
        queryset=(
            lambda request: get_user_model().objects.filter(
                pk__in=PageLogEntry.objects.filter(action="wagtail.edit")
                .order_by()
                .values_list("user_id", flat=True)
                .distinct()
            )
        ),
        widget=CheckboxSelectMultiple,
    )
    site = SiteFilter(
        label=_("Site"),
        queryset=Site.objects.all(),
        widget=CheckboxSelectMultiple,
    )
    has_child_pages = HasChildPagesFilter(
        label=_("Has child pages"),
        empty_label=_("Any"),
        choices=[
            ("true", _("Yes")),
            ("false", _("No")),
        ],
        widget=RadioSelect,
    )

    class Meta:
        model = Page
        fields = []  # only needed for filters being generated automatically


class IndexView(generic.IndexView):
    template_name = "wagtailadmin/pages/index.html"
    results_template_name = "wagtailadmin/pages/index_results.html"
    permission_policy = page_permission_policy
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
    filterset_class = PageFilterSet
    page_title = _("Exploring")

    columns = [
        BulkActionsColumn("bulk_actions"),
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
        if "q" in self.request.GET:
            self.search_form = SearchForm(self.request.GET)
            if self.search_form.is_valid():
                self.query_string = self.search_form.cleaned_data["q"]
        else:
            self.search_form = SearchForm()

        if self.query_string:
            self.is_searching = True

        self.is_searching_whole_tree = bool(self.request.GET.get("search_all")) and (
            self.is_searching or self.is_filtering
        )

        return super().get(request)

    def get_valid_orderings(self):
        valid_orderings = [
            "title",
            "-title",
            "live",
            "-live",
            "latest_revision_created_at",
            "-latest_revision_created_at",
        ]

        if not self.is_searching:
            # ordering by page order is only available when not searching
            valid_orderings.append("ord")

            # ordering by content type not currently available when searching, due to
            # https://github.com/wagtail/wagtail/issues/6616
            valid_orderings.append("content_type")
            valid_orderings.append("-content_type")

        return valid_orderings

    def get_ordering(self):
        if self.is_searching and not self.is_explicitly_ordered:
            # default to ordering by relevance
            default_ordering = None
        else:
            default_ordering = self.parent_page.get_admin_default_ordering()

        ordering = self.request.GET.get("ordering", default_ordering)
        if ordering not in self.get_valid_orderings():
            ordering = default_ordering

        return ordering

    def get_base_queryset(self):
        if self.is_searching or self.is_filtering:
            if self.is_searching_whole_tree:
                pages = Page.objects.all()
            else:
                pages = self.parent_page.get_descendants()
        else:
            pages = self.parent_page.get_children()

        pages = pages.prefetch_related(
            "content_type", "sites_rooted_here"
        ) & self.permission_policy.explorable_instances(self.request.user)

        # We want specific page instances, but do not need streamfield values here
        pages = pages.defer_streamfields().specific()

        # Annotate queryset with various states to be used later for performance optimisations
        if getattr(settings, "WAGTAIL_WORKFLOW_ENABLED", True):
            pages = pages.prefetch_workflow_states()

        pages = pages.annotate_site_root_state().annotate_approved_schedule()

        return pages

    def order_queryset(self, queryset):
        if self.is_searching and not self.is_explicitly_ordered:
            # search backend will order by relevance in this case, so don't bother to
            # apply an ordering on the queryset
            return queryset

        if self.ordering == "ord":
            # preserve the native ordering from get_children()
            pass
        elif self.ordering == "latest_revision_created_at" and not self.is_searching:
            # order by oldest revision first.
            # Special case NULL entries - these should go at the top of the list.
            # Skip this special case when searching (and fall through to plain field ordering
            # instead) as search backends do not support F objects in order_by
            queryset = queryset.order_by(
                F("latest_revision_created_at").asc(nulls_first=True)
            )
        elif self.ordering == "-latest_revision_created_at" and not self.is_searching:
            # order by oldest revision first.
            # Special case NULL entries - these should go at the end of the list.
            # Skip this special case when searching (and fall through to plain field ordering
            # instead) as search backends do not support F objects in order_by
            queryset = queryset.order_by(
                F("latest_revision_created_at").desc(nulls_last=True)
            )
        else:
            queryset = super().order_queryset(queryset)

        return queryset

    def search_queryset(self, queryset):
        # allow hooks to modify queryset. This should happen as close as possible to the
        # final queryset, but (for backward compatibility) needs to be passed an actual queryset
        # rather than a search result object
        for hook in hooks.get_hooks("construct_explorer_page_queryset"):
            queryset = hook(self.parent_page, queryset, self.request)

        if self.is_searching:
            queryset = queryset.autocomplete(
                self.query_string, order_by_relevance=(not self.is_explicitly_ordered)
            )

        return queryset

    def get_paginate_by(self, queryset):
        if self.ordering == "ord":
            # Don't paginate if sorting by page order - all pages must be shown to
            # allow drag-and-drop reordering
            return None
        else:
            return self.paginate_by

    def get_index_url(self):
        return reverse("wagtailadmin_explore", args=[self.parent_page.id])

    def get_index_results_url(self):
        return reverse("wagtailadmin_explore_results", args=[self.parent_page.id])

    def get_history_url(self):
        permissions = self.parent_page.permissions_for_user(self.request.user)
        if permissions.can_view_revisions():
            return reverse("wagtailadmin_pages:history", args=[self.parent_page.id])

    def get_table_kwargs(self):
        kwargs = super().get_table_kwargs()
        kwargs["use_row_ordering_attributes"] = self.show_ordering_column
        kwargs["parent_page"] = self.parent_page
        kwargs["show_locale_labels"] = self.i18n_enabled and self.parent_page.is_root()
        kwargs["actions_next_url"] = self.index_url

        if self.show_ordering_column:
            kwargs["caption"] = _(
                "Focus on the drag button and press up or down arrows to move the item, then press enter to submit the change."
            )
            kwargs["attrs"] = {
                "data-controller": "w-orderable",
                "data-w-orderable-active-class": "w-orderable--active",
                "data-w-orderable-chosen-class": "w-orderable__item--active",
                "data-w-orderable-container-value": "tbody",
                "data-w-orderable-message-value": _(
                    "'%(page_title)s' has been moved successfully."
                )
                % {"page_title": "__LABEL__"},
                "data-w-orderable-url-value": reverse(
                    "wagtailadmin_pages:set_page_position", args=[999999]
                ),
            }
        return kwargs

    def get_page_subtitle(self):
        return self.parent_page.get_admin_display_title()

    def get_context_data(self, **kwargs):
        self.show_ordering_column = self.ordering == "ord"
        if self.show_ordering_column:
            self.columns = self.columns.copy()
            self.columns[0] = OrderingColumn("ordering", width="80px", sort_key="ord")
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
                "history_url": self.get_history_url(),
                "search_form": self.search_form,
                "is_searching": self.is_searching,
                "is_searching_whole_tree": self.is_searching_whole_tree,
            }
        )

        if not self.results_only:
            side_panels = self.get_side_panels()
            context["side_panels"] = side_panels
            context["media"] += side_panels.media

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

    def get_side_panels(self):
        # Don't show side panels on the root page
        if self.parent_page.is_root():
            return MediaContainer()

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
