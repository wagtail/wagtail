from django.conf.urls import url

from wagtail.api.v2.router import WagtailAPIRouter
from wagtail.core import hooks

from .views import PagesAdminAPIViewSet

admin_api = WagtailAPIRouter('wagtailadmin_api')
admin_api.register_endpoint('pages', PagesAdminAPIViewSet)

for fn in hooks.get_hooks('construct_admin_api'):
    fn(admin_api)

urlpatterns = [
    url(r'^main/', admin_api.urls),
]
