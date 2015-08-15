from django.conf.urls import url
from wagtail.wagtailsites import views

urlpatterns = [
    url(r'^$', views.Index.as_view(), name='index'),
    url(r'^add/$', views.create, name='add'),
    url(r'^(\d+)/$', views.edit, name='edit'),
    url(r'^(\d+)/delete/$', views.delete, name='delete'),
]
