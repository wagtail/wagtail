from django.conf.urls import url

from wagtail.admin.views import reports

app_name = 'wagtailadmin_reports'
urlpatterns = [
    url(r'^locked/$', reports.LockedPagesView.as_view(), name='locked_pages')
]
