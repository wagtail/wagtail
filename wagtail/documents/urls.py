from django.urls import re_path

from wagtail.documents.views import serve

urlpatterns = [
    re_path(r'^(\d+)/(.*)$', serve.serve, name='wagtaildocs_serve'),
    re_path(
        r'^authenticate_with_password/(\d+)/$',
        serve.authenticate_with_password,
        name='wagtaildocs_authenticate_with_password'),
]
