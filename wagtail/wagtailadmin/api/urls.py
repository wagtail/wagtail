from __future__ import absolute_import, unicode_literals

from django.conf.urls import url

from wagtail.api.v2.router import WagtailAPIRouter

from .endpoints import DocumentsAdminAPIEndpoint, ImagesAdminAPIEndpoint, PagesAdminAPIEndpoint

v1 = WagtailAPIRouter('wagtailadmin_api_v1')
v1.register_endpoint('pages', PagesAdminAPIEndpoint)
v1.register_endpoint('images', ImagesAdminAPIEndpoint)
v1.register_endpoint('documents', DocumentsAdminAPIEndpoint)

urlpatterns = [
    url(r'^v2beta/', v1.urls),
]
