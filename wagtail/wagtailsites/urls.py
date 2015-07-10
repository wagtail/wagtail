from django.conf.urls import url
from wagtail.wagtailsites import views

urlpatterns = [

    url(r'^$', views.index, name='index'),
    url(r'^new/$', views.create, name='create'),
    url(r'^(\d+)/$', views.edit, name='edit'),
    url(r'^(\d+)/delete/$', views.delete, name='delete'),

]
