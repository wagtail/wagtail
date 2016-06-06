from __future__ import absolute_import, unicode_literals

from django.conf.urls import url

from wagtail.wagtailcore import views
from wagtail.wagtailcore.utils import WAGTAIL_APPEND_SLASH


if WAGTAIL_APPEND_SLASH:
    # If WAGTAIL_APPEND_SLASH is True (the default value), we match a
    # (possibly empty) list of path segments ending in slashes.
    # CommonMiddleware will redirect requests without a trailing slash to
    # a URL with a trailing slash
    serve_pattern = r'^((?:[\w\-]+/)*)$'
else:
    # If WAGTAIL_APPEND_SLASH is False, allow Wagtail to serve pages on URLs
    # with and without trailing slashes
    serve_pattern = r'^([\w\-/]*)$'


urlpatterns = [
    url(r'^_util/authenticate_with_password/(\d+)/(\d+)/$', views.authenticate_with_password,
        name='wagtailcore_authenticate_with_password'),

    # Front-end page views are handled through Wagtail's core.views.serve
    # mechanism
    url(serve_pattern, views.serve, name='wagtail_serve')
]
