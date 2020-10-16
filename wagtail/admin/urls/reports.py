from django.urls import path

from wagtail.admin.views import reports


app_name = 'wagtailadmin_reports'
urlpatterns = [
    path('locked/', reports.LockedPagesView.as_view(), name='locked_pages'),
    path('workflow/', reports.WorkflowView.as_view(), name='workflow'),
    path('workflow_tasks/', reports.WorkflowTasksView.as_view(), name='workflow_tasks'),
    path('site-history/', reports.LogEntriesView.as_view(), name='site_history'),
]
