from django.urls import re_path

from wagtail.images.views.serve import SendFileView, ServeView
from wagtail.tests import dummy_sendfile_backend


urlpatterns = [
    # Format: signature, image_id, filter_spec, filename=None
    re_path(r'^actions/serve/(.*)/(\d*)/(.*)/[^/]*', ServeView.as_view(action='serve'), name='wagtailimages_serve_action_serve'),
    re_path(r'^actions/redirect/(.*)/(\d*)/(.*)/[^/]*', ServeView.as_view(action='redirect'), name='wagtailimages_serve_action_redirect'),
    re_path(r'^custom_key/(.*)/(\d*)/(.*)/[^/]*', ServeView.as_view(key='custom'), name='wagtailimages_serve_custom_key'),
    re_path(r'^custom_view/([^/]*)/(\d*)/([^/]*)/[^/]*$', ServeView.as_view(), name='wagtailimages_serve_custom_view'),
    re_path(r'^sendfile/(.*)/(\d*)/(.*)/[^/]*', SendFileView.as_view(), name='wagtailimages_sendfile'),
    re_path(r'^sendfile-dummy/(.*)/(\d*)/(.*)/[^/]*', SendFileView.as_view(backend=dummy_sendfile_backend.sendfile), name='wagtailimages_sendfile_dummy'),
]
