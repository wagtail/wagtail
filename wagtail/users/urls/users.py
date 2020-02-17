from django.urls import path, re_path

from wagtail.users.views import users

app_name = 'wagtailusers_users'
urlpatterns = [
    path('', users.index, name='index'),
    path('add/', users.create, name='add'),
    re_path(r'^([^\/]+)/$', users.edit, name='edit'),
    re_path(r'^([^\/]+)/delete/$', users.delete, name='delete'),
]
