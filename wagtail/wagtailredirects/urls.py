from django.conf.urls import url
from wagtail.wagtailredirects import views


urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^(\d+)/$', views.edit, name='edit_redirect'),
    url(r'^(\d+)/delete/$', views.delete, name='delete_redirect'),
    url(r'^add/$', views.add, name='add_redirect'),
]
