from django.urls import path

from wagtail.admin.views.reports.aging_pages import AgingPagesView
from wagtail.admin.views.reports.audit_logging import LogEntriesView
from wagtail.admin.views.reports.locked_pages import LockedPagesView
from wagtail.admin.views.reports.workflows import WorkflowTasksView, WorkflowView

app_name = "wagtailadmin_reports"
urlpatterns = [
    path("locked/", LockedPagesView.as_view(), name="locked_pages"),
    path("workflow/", WorkflowView.as_view(), name="workflow"),
    path("workflow_tasks/", WorkflowTasksView.as_view(), name="workflow_tasks"),
    path("site-history/", LogEntriesView.as_view(), name="site_history"),
    path("aging-pages/", AgingPagesView.as_view(), name="aging_pages"),
]
