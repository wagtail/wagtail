from django.urls import path

from wagtail import hooks
from wagtail.api.v2.router import WagtailAPIRouter

from .v2.views import PagesAdminAPIViewSet
from .v3.api import api

admin_api = WagtailAPIRouter("wagtailadmin_api")
admin_api.register_endpoint("pages", PagesAdminAPIViewSet)

for fn in hooks.get_hooks("construct_admin_api"):
    fn(admin_api)

urlpatterns = [
    path("main/", admin_api.urls),
    path("", api.urls),
]
