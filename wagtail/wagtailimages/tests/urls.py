from __future__ import absolute_import, unicode_literals

from django.conf.urls import url

from wagtail.wagtailimages.views.serve import ServeView


urlpatterns = [
    url(r'^actions/serve/(.*)/(\d*)/(.*)/[^/]*', ServeView.as_view(action='serve'), name='wagtailimages_serve_action_serve'),
    url(r'^actions/redirect/(.*)/(\d*)/(.*)/[^/]*', ServeView.as_view(action='redirect'), name='wagtailimages_serve_action_redirect'),
    url(r'^actions/unknown/(.*)/(\d*)/(.*)/[^/]*', ServeView.as_view(action='unknown'), name='wagtailimages_serve_action_unknown'),
]
