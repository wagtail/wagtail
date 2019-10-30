from django.conf.urls import url

from wagtail.admin.views import reports

app_name = 'wagtailadmin_reports'
urlpatterns = [
    url(r'^locked/$', reports.locked_pages, name='locked_pages')
]
