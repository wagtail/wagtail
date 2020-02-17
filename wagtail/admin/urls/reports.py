from django.urls import path

from wagtail.admin.views import reports

app_name = 'wagtailadmin_reports'
urlpatterns = [
    path('locked/', reports.LockedPagesView.as_view(), name='locked_pages')
]
