from django.conf.urls import url

from wagtail.images.views.serve import SendFileView, ServeView
from wagtail.tests import dummy_sendfile_backend

urlpatterns = [
    url(r'^actions/serve/(.*)/(\d*)/(.*)/[^/]*', ServeView.as_view(action='serve'), name='wagtailimages_serve_action_serve'),
    url(r'^actions/redirect/(.*)/(\d*)/(.*)/[^/]*', ServeView.as_view(action='redirect'), name='wagtailimages_serve_action_redirect'),
    url(r'^custom_key/(.*)/(\d*)/(.*)/[^/]*', ServeView.as_view(key='custom'), name='wagtailimages_serve_custom_key'),
    url(r'^sendfile/(.*)/(\d*)/(.*)/[^/]*', SendFileView.as_view(), name='wagtailimages_sendfile'),
    url(r'^sendfile-dummy/(.*)/(\d*)/(.*)/[^/]*', SendFileView.as_view(backend=dummy_sendfile_backend.sendfile), name='wagtailimages_sendfile_dummy'),
]
