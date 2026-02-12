from django.urls import path

from wagtail.admin.views.reports.aging_pages import AgingPagesView
from wagtail.admin.views.reports.audit_logging import LogEntriesView
from wagtail.admin.views.reports.locked_pages import LockedPagesView
from wagtail.admin.views.reports.page_types_usage import (
    PageTypesUsageReportView,
)
from wagtail.admin.views.reports.workflows import WorkflowTasksView, WorkflowView

app_name = "wagtailadmin_reports"
urlpatterns = [
    path("locked/", LockedPagesView.as_view(), name="locked_pages"),
    path(
        "locked/results/",
        LockedPagesView.as_view(results_only=True),
        name="locked_pages_results",
    ),
    path("workflow/", WorkflowView.as_view(), name="workflow"),
    path(
        "workflow/results/",
        WorkflowView.as_view(results_only=True),
        name="workflow_results",
    ),
    path("workflow_tasks/", WorkflowTasksView.as_view(), name="workflow_tasks"),
    path(
        "workflow_tasks/results/",
        WorkflowTasksView.as_view(results_only=True),
        name="workflow_tasks_results",
    ),
    path("site-history/", LogEntriesView.as_view(), name="site_history"),
    path(
        "site-history/results/",
        LogEntriesView.as_view(results_only=True),
        name="site_history_results",
    ),
    path("aging-pages/", AgingPagesView.as_view(), name="aging_pages"),
    path(
        "aging-pages/results/",
        AgingPagesView.as_view(results_only=True),
        name="aging_pages_results",
    ),
    path(
        "page-types-usage/",
        PageTypesUsageReportView.as_view(),
        name="page_types_usage",
    ),
    path(
        "page-types-usage/results/",
        PageTypesUsageReportView.as_view(results_only=True),
        name="page_types_usage_results",
    ),
]
