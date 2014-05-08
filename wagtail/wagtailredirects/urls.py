from django.conf.urls import url
from wagtail.wagtailredirects import views


urlpatterns = [
    url(r'^$', views.index, name='wagtailredirects_index'),
    url(r'^(\d+)/$', views.edit, name='wagtailredirects_edit_redirect'),
    url(r'^(\d+)/delete/$', views.delete, name='wagtailredirects_delete_redirect'),
    url(r'^add/$', views.add, name='wagtailredirects_add_redirect'),
]
