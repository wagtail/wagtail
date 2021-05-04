import datetime

import django_filters

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.db.models import Q, Subquery
from django.utils.encoding import force_str
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import TemplateResponseMixin
from django.views.generic.list import BaseListView

from wagtail.admin.filters import DateRangePickerWidget, FilteredModelChoiceFilter, WagtailFilterSet
from wagtail.admin.views.mixins import SpreadsheetExportMixin
from wagtail.admin.widgets import ButtonSelect
from wagtail.core.log_actions import page_log_action_registry
from wagtail.core.models import (
    Page, PageLogEntry, Task, TaskState, UserPagePermissionsProxy, Workflow, WorkflowState)


class LockedPagesReportFilterSet(WagtailFilterSet):
    locked_at = django_filters.DateFromToRangeFilter(widget=DateRangePickerWidget)

    class Meta:
        model = Page
        fields = ['locked_by', 'locked_at', 'live']


def get_requested_by_queryset(request):
    User = get_user_model()
    return User.objects.filter(
        pk__in=set(WorkflowState.objects.values_list('requested_by__pk', flat=True))
    ).order_by(User.USERNAME_FIELD)


class WorkflowReportFilterSet(WagtailFilterSet):
    created_at = django_filters.DateFromToRangeFilter(label=_("Started at"), widget=DateRangePickerWidget)
    reviewable = django_filters.ChoiceFilter(
        label=_("Show"),
        method='filter_reviewable',
        choices=(
            ('true', _("Awaiting my review")),
        ),
        empty_label=_("All"),
        widget=ButtonSelect
    )
    requested_by = django_filters.ModelChoiceFilter(
        field_name='requested_by', queryset=get_requested_by_queryset
    )

    def filter_reviewable(self, queryset, name, value):
        if value and self.request and self.request.user:
            queryset = queryset.filter(current_task_state__in=TaskState.objects.reviewable_by(self.request.user))
        return queryset

    class Meta:
        model = WorkflowState
        fields = ['reviewable', 'workflow', 'status', 'requested_by', 'created_at']


class WorkflowTasksReportFilterSet(WagtailFilterSet):
    started_at = django_filters.DateFromToRangeFilter(label=_("Started at"), widget=DateRangePickerWidget)
    finished_at = django_filters.DateFromToRangeFilter(label=_("Completed at"), widget=DateRangePickerWidget)
    workflow = django_filters.ModelChoiceFilter(
        field_name='workflow_state__workflow', queryset=Workflow.objects.all(), label=_("Workflow")
    )

    # When a workflow is chosen in the 'id_workflow' selector, filter this list of tasks
    # to just the ones whose workflows attribute includes the selected workflow.
    task = FilteredModelChoiceFilter(
        queryset=Task.objects.all(), filter_field='id_workflow', filter_accessor='workflows'
    )

    reviewable = django_filters.ChoiceFilter(
        label=_("Show"),
        method='filter_reviewable',
        choices=(
            ('true', _("Awaiting my review")),
        ),
        empty_label=_("All"),
        widget=ButtonSelect
    )

    def filter_reviewable(self, queryset, name, value):
        if value and self.request and self.request.user:
            queryset = queryset.filter(id__in=TaskState.objects.reviewable_by(self.request.user).values_list('id', flat=True))
        return queryset

    class Meta:
        model = TaskState
        fields = ['reviewable', 'workflow', 'task', 'status', 'started_at', 'finished_at']


def get_audit_log_users_queryset(request):
    User = get_user_model()
    return User.objects.filter(
        pk__in=set(PageLogEntry.objects.values_list('user__pk', flat=True))
    ).order_by(User.USERNAME_FIELD)


class SiteHistoryReportFilterSet(WagtailFilterSet):
    action = django_filters.ChoiceFilter(choices=page_log_action_registry.get_choices)
    timestamp = django_filters.DateFromToRangeFilter(label=_('Date'), widget=DateRangePickerWidget)
    label = django_filters.CharFilter(label=_('Title'), lookup_expr='icontains')
    user = django_filters.ModelChoiceFilter(
        field_name='user', queryset=get_audit_log_users_queryset
    )

    class Meta:
        model = PageLogEntry
        fields = ['label', 'action', 'user', 'timestamp']


class ReportView(SpreadsheetExportMixin, TemplateResponseMixin, BaseListView):
    header_icon = ""
    page_kwarg = "p"
    template_name = "wagtailadmin/reports/base_report.html"
    title = ""
    paginate_by = 50
    filterset_class = None

    def filter_queryset(self, queryset):
        filters = None

        if self.filterset_class:
            filters = self.filterset_class(self.request.GET, queryset=queryset, request=self.request)
            queryset = filters.qs

        return filters, queryset

    def dispatch(self, request, *args, **kwargs):
        self.is_export = self.request.GET.get("export") in self.FORMATS
        if self.is_export:
            self.paginate_by = None
            return self.as_spreadsheet(self.filter_queryset(self.get_queryset())[1], self.request.GET.get("export"))
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, object_list=None, **kwargs):
        queryset = object_list if object_list is not None else self.object_list
        filters, queryset = self.filter_queryset(queryset)

        context = super().get_context_data(*args, object_list=queryset, **kwargs)
        context["title"] = self.title
        context["header_icon"] = self.header_icon
        context["filters"] = filters
        return context


class PageReportView(ReportView):
    template_name = "wagtailadmin/reports/base_page_report.html"
    export_headings = {
        "latest_revision_created_at": _("Updated"),
        "status_string": _("Status"),
        "content_type.model_class._meta.verbose_name.title": _("Type"),
    }
    list_export = [
        "title",
        "latest_revision_created_at",
        "status_string",
        "content_type.model_class._meta.verbose_name.title",
    ]


class LockedPagesView(PageReportView):
    template_name = "wagtailadmin/reports/locked_pages.html"
    title = _("Locked pages")
    header_icon = "lock"
    list_export = PageReportView.list_export + [
        "locked_at",
        "locked_by",
    ]
    filterset_class = LockedPagesReportFilterSet

    def get_filename(self):
        return "locked-pages-report-{}".format(
            datetime.datetime.today().strftime("%Y-%m-%d")
        )

    def get_queryset(self):
        pages = (
            UserPagePermissionsProxy(self.request.user).editable_pages()
            | Page.objects.filter(locked_by=self.request.user)
        ).filter(locked=True).specific(defer=True)
        self.queryset = pages
        return super().get_queryset()

    def dispatch(self, request, *args, **kwargs):
        if not UserPagePermissionsProxy(request.user).can_remove_locks():
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class WorkflowView(ReportView):
    template_name = 'wagtailadmin/reports/workflow.html'
    title = _('Workflows')
    header_icon = 'tasks'
    filterset_class = WorkflowReportFilterSet

    export_headings = {
        "page.id": _("Page ID"),
        "page.content_type.model_class._meta.verbose_name.title": _("Page Type"),
        "page.title": _("Page Title"),
        "get_status_display": _("Status"),
        "created_at": _("Started at")
    }
    list_export = [
        "workflow",
        "page.id",
        "page.content_type.model_class._meta.verbose_name.title",
        "page.title",
        "get_status_display",
        "requested_by",
        "created_at",
    ]

    def get_filename(self):
        return "workflow-report-{}".format(
            datetime.datetime.today().strftime("%Y-%m-%d")
        )

    def get_queryset(self):
        pages = UserPagePermissionsProxy(self.request.user).editable_pages()
        return WorkflowState.objects.filter(page__in=pages).order_by('-created_at')


class WorkflowTasksView(ReportView):
    template_name = 'wagtailadmin/reports/workflow_tasks.html'
    title = _('Workflow tasks')
    header_icon = 'thumbtack'
    filterset_class = WorkflowTasksReportFilterSet

    export_headings = {
        "workflow_state.page.id": _("Page ID"),
        "workflow_state.page.content_type.model_class._meta.verbose_name.title": _("Page Type"),
        "workflow_state.page.title": _("Page Title"),
        "get_status_display": _("Status"),
        "workflow_state.requested_by": _("Requested By")
    }
    list_export = [
        "task",
        "workflow_state.page.id",
        "workflow_state.page.content_type.model_class._meta.verbose_name.title",
        "workflow_state.page.title",
        "get_status_display",
        "workflow_state.requested_by",
        "started_at",
        "finished_at",
        "finished_by",
    ]

    def get_filename(self):
        return "workflow-tasks-{}".format(
            datetime.datetime.today().strftime("%Y-%m-%d")
        )

    def get_queryset(self):
        pages = UserPagePermissionsProxy(self.request.user).editable_pages()
        return TaskState.objects.filter(workflow_state__page__in=pages).order_by('-started_at')


class LogEntriesView(ReportView):
    template_name = 'wagtailadmin/reports/site_history.html'
    title = _('Site history')
    header_icon = 'history'
    filterset_class = SiteHistoryReportFilterSet

    export_headings = {
        "object_id": _("ID"),
        "title": _("Title"),
        "object_verbose_name": _("Type"),
        "action": _("Action type"),
        "timestamp": _("Date/Time")
    }
    list_export = [
        "object_id",
        "label",
        "object_verbose_name",
        "action",
        "timestamp"
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.custom_field_preprocess['action'] = {
            self.FORMAT_CSV: self.get_action_label,
            self.FORMAT_XLSX: self.get_action_label
        }

    def get_filename(self):
        return "audit-log-{}".format(
            datetime.datetime.today().strftime("%Y-%m-%d")
        )

    def get_queryset(self):
        q = Q(
            page__in=UserPagePermissionsProxy(self.request.user).explorable_pages().values_list('pk', flat=True)
        )

        root_page_permissions = Page.get_first_root_node().permissions_for_user(self.request.user)
        if (
            self.request.user.is_superuser
            or root_page_permissions.can_add_subpage() or root_page_permissions.can_edit()
        ):
            # Include deleted entries
            q = q | Q(page_id__in=Subquery(
                PageLogEntry.objects.filter(deleted=True).values('page_id')
            ))

        return PageLogEntry.objects.filter(q)

    def get_action_label(self, action):
        from wagtail.core.log_actions import page_log_action_registry
        return force_str(page_log_action_registry.get_action_label(action))
