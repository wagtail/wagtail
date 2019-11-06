from django.conf.urls import url

from wagtail.admin.views import workflows

app_name = 'wagtailadmin_workflows'
urlpatterns = [
    url(r'^$', workflows.Index.as_view(), name='index'),
    url(r'^add/$', workflows.Create.as_view(), name='add'),
    url(r'^edit/$', workflows.Index.as_view(), name='edit'),
]
