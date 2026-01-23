import django_filters
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy

from wagtail.admin.views.generic import history
from wagtail.admin.views.pages.utils import (
    GenericPageBreadcrumbsMixin,
)
from wagtail.admin.widgets import BooleanRadioSelect
from wagtail.models import Page, PageLogEntry
from wagtail.permissions import page_permission_policy


class PageHistoryFilterSet(history.HistoryFilterSet):
    is_commenting_action = django_filters.BooleanFilter(
        label=gettext_lazy("Is commenting action"),
        method="filter_is_commenting_action",
        widget=BooleanRadioSelect,
    )

    def filter_is_commenting_action(self, queryset, name, value):
        if value is None:
            return queryset

        q = Q(action__startswith="wagtail.comments")
        if value is False:
            q = ~q

        return queryset.filter(q)


class PageWorkflowHistoryViewMixin:
    model = Page
    pk_url_kwarg = "page_id"
    edit_url_name = "wagtailadmin_pages:edit"

    def dispatch(self, request, *args, **kwargs):
        if not self.object.permissions_for_user(request.user).can_edit():
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs, page=self.object)


class WorkflowHistoryView(
    PageWorkflowHistoryViewMixin,
    GenericPageBreadcrumbsMixin,
    history.WorkflowHistoryView,
):
    header_icon = "doc-empty-inverse"
    workflow_history_detail_url_name = "wagtailadmin_pages:workflow_history_detail"


class WorkflowHistoryDetailView(
    PageWorkflowHistoryViewMixin,
    GenericPageBreadcrumbsMixin,
    history.WorkflowHistoryDetailView,
):
    header_icon = "doc-empty-inverse"
    workflow_history_url_name = "wagtailadmin_pages:workflow_history"
    breadcrumbs_items_to_take = 2


class PageHistoryView(GenericPageBreadcrumbsMixin, history.HistoryView):
    template_name = "wagtailadmin/pages/history.html"
    filterset_class = PageHistoryFilterSet
    model = Page
    pk_url_kwarg = "page_id"
    permission_policy = page_permission_policy
    any_permission_required = {
        "add",
        "change",
        "publish",
        "bulk_delete",
        "lock",
        "unlock",
    }
    history_url_name = "wagtailadmin_pages:history"
    history_results_url_name = "wagtailadmin_pages:history_results"
    edit_url_name = "wagtailadmin_pages:edit"
    revisions_view_url_name = "wagtailadmin_pages:revisions_view"
    revisions_revert_url_name = "wagtailadmin_pages:revisions_revert"
    revisions_compare_url_name = "wagtailadmin_pages:revisions_compare"
    revisions_unschedule_url_name = "wagtailadmin_pages:revisions_unschedule"

    def get_object(self):
        return get_object_or_404(Page, id=self.pk).specific

    def get_page_subtitle(self):
        return self.object.get_admin_display_title()

    def user_can_unschedule(self):
        return self.object.permissions_for_user(self.request.user).can_unschedule()

    def get_base_queryset(self):
        return self._annotate_queryset(PageLogEntry.objects.filter(page=self.object))

    def _annotate_queryset(self, queryset):
        return super()._annotate_queryset(queryset).select_related("page")
