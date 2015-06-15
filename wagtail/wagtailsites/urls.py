from django.conf.urls import url
from wagtail.wagtailsites import views

urlpatterns = [

    url(r'^$', views.index, name='wagtailsites_index'),
    url(r'^new/$', views.create, name='wagtailsites_create'),
    url(r'^(\d+)/$', views.edit, name='wagtailsites_edit'),
    url(r'^(\d+)/delete/$', views.delete, name='wagtailsites_delete'),

]
