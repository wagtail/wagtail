import django_filters
from django import forms
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _

from wagtail.admin.auth import user_has_any_page_permission, user_passes_test
from wagtail.admin.filters import DateRangePickerWidget, WagtailFilterSet
from wagtail.admin.views.generic import history
from wagtail.admin.views.reports import ReportView
from wagtail.log_actions import registry as log_action_registry
from wagtail.models import Page, PageLogEntry


def get_actions_for_filter():
    # Only return those actions used by page log entries.
    actions = set(PageLogEntry.objects.all().get_actions())
    return [
        action for action in log_action_registry.get_choices() if action[0] in actions
    ]


class PageHistoryReportFilterSet(WagtailFilterSet):
    action = django_filters.ChoiceFilter(
        label=_("Action"),
        # choices are set dynamically in __init__()
    )
    hide_commenting_actions = django_filters.BooleanFilter(
        label=_("Hide commenting actions"),
        method="filter_hide_commenting_actions",
        widget=forms.CheckboxInput,
    )
    user = django_filters.ModelChoiceFilter(
        label=_("User"),
        field_name="user",
        queryset=lambda request: PageLogEntry.objects.all().get_users(),
    )
    timestamp = django_filters.DateFromToRangeFilter(
        label=_("Date"), widget=DateRangePickerWidget
    )

    def filter_hide_commenting_actions(self, queryset, name, value):
        if value:
            queryset = queryset.exclude(action__startswith="wagtail.comments")
        return queryset

    class Meta:
        model = PageLogEntry
        fields = ["action", "user", "timestamp", "hide_commenting_actions"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filters["action"].extra["choices"] = get_actions_for_filter()


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


class PageHistoryView(ReportView):
    template_name = "wagtailadmin/pages/history.html"
    title = _("Page history")
    header_icon = "history"
    paginate_by = 20
    filterset_class = PageHistoryReportFilterSet

    @method_decorator(user_passes_test(user_has_any_page_permission))
    def dispatch(self, request, *args, **kwargs):
        self.page = get_object_or_404(Page, id=kwargs.pop("page_id")).specific

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, object_list=None, **kwargs):
        context = super().get_context_data(*args, object_list=object_list, **kwargs)
        context["page"] = self.page
        context["subtitle"] = self.page.get_admin_display_title()
        context["page_latest_revision"] = self.page.get_latest_revision()

        return context

    def get_queryset(self):
        return PageLogEntry.objects.filter(page=self.page).select_related(
            "revision", "user", "user__wagtail_userprofile"
        )
