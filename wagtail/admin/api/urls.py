from django.conf.urls import url

from wagtail.api.v2.router import WagtailAPIRouter
from wagtail.core import hooks

from .endpoints import PagesAdminAPIEndpoint

admin_api = WagtailAPIRouter('wagtailadmin_api_v1')
admin_api.register_endpoint('pages', PagesAdminAPIEndpoint)

for fn in hooks.get_hooks('construct_admin_api'):
    fn(admin_api)

urlpatterns = [
    url(r'^v2beta/', admin_api.urls),
]
