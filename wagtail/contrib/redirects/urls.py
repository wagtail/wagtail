from django.conf.urls import url

from wagtail.contrib.redirects import views

app_name = 'wagtailredirects'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^add/$', views.add, name='add'),
    url(r'^(\d+)/$', views.edit, name='edit'),
    url(r'^(\d+)/delete/$', views.delete, name='delete'),
    url(r"^import/$", views.start_import, name="start_import"),
    url(r"^import/process/$", views.process_import, name="process_import"),
]
