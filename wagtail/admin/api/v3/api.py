from ninja import NinjaAPI

from wagtail.admin.api.v3.explorer import router as explorer_router
from wagtail.api.v3.errors import register_exception_handlers

# An internal API for the admin interface, e.g. the page explorer in the
# sidebar. Access is handled by the admin's own authentication, as all admin
# URLs are decorated with ``require_admin_access``.
api = NinjaAPI(
    title="Wagtail admin API",
    urls_namespace="wagtailadmin_api",
    openapi_url=None,
    docs_url=None,
)

register_exception_handlers(api)

api.add_router("/explorer/", explorer_router)
