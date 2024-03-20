import django_filters
from django import forms
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy

from wagtail.admin.auth import user_has_any_page_permission, user_passes_test
from wagtail.admin.views.generic import history
from wagtail.models import Page, PageLogEntry


class PageHistoryFilterSet(history.HistoryFilterSet):
    hide_commenting_actions = django_filters.BooleanFilter(
        label=gettext_lazy("Hide commenting actions"),
        method="filter_hide_commenting_actions",
        widget=forms.CheckboxInput,
    )

    def filter_hide_commenting_actions(self, queryset, name, value):
        if value:
            queryset = queryset.exclude(action__startswith="wagtail.comments")
        return queryset


class PageWorkflowHistoryViewMixin:
    model = Page
    pk_url_kwarg = "page_id"

    def dispatch(self, request, *args, **kwargs):
        if not self.object.permissions_for_user(request.user).can_edit():
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs, page=self.object)


class WorkflowHistoryView(PageWorkflowHistoryViewMixin, history.WorkflowHistoryView):
    header_icon = "doc-empty-inverse"
    workflow_history_url_name = "wagtailadmin_pages:workflow_history"
    workflow_history_detail_url_name = "wagtailadmin_pages:workflow_history_detail"


class WorkflowHistoryDetailView(
    PageWorkflowHistoryViewMixin, history.WorkflowHistoryDetailView
):
    object_icon = "doc-empty-inverse"
    workflow_history_url_name = "wagtailadmin_pages:workflow_history"


@method_decorator(user_passes_test(user_has_any_page_permission), name="dispatch")
class PageHistoryView(history.HistoryView):
    template_name = "wagtailadmin/pages/history.html"
    page_title = gettext_lazy("Page history")
    filterset_class = PageHistoryFilterSet
    model = Page
    pk_url_kwarg = "page_id"

    def get_object(self):
        self.page = get_object_or_404(Page, id=self.pk).specific
        return self.page

    def get_context_data(self, *args, object_list=None, **kwargs):
        context = super().get_context_data(*args, object_list=object_list, **kwargs)
        context["page"] = self.page
        context["subtitle"] = self.page.get_admin_display_title()
        context["page_latest_revision"] = self.page.get_latest_revision()

        return context

    def user_can_unschedule(self):
        return self.object.permissions_for_user(self.request.user).can_unschedule()

    def get_base_queryset(self):
        return PageLogEntry.objects.filter(page=self.page).select_related(
            "revision", "user", "user__wagtail_userprofile"
        )
