from __future__ import absolute_import

from django.conf.urls import url

from wagtail.api.shared.router import WagtailAPIRouter

from .endpoints import PagesAdminAPIEndpoint, ImagesAdminAPIEndpoint, DocumentsAdminAPIEndpoint


v1 = WagtailAPIRouter('wagtailadmin_api_v1')
v1.register_endpoint('pages', PagesAdminAPIEndpoint)
v1.register_endpoint('images', ImagesAdminAPIEndpoint)
v1.register_endpoint('documents', DocumentsAdminAPIEndpoint)

urlpatterns = [
    url(r'^v1beta/', v1.urls),
]
