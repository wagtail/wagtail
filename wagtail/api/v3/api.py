from ninja import NinjaAPI

from wagtail.api.v3.errors import register_exception_handlers
from wagtail.api.v3.routers.pages import router as pages_router
from wagtail.api.v3.routers.schema import router as schema_router

api = NinjaAPI(
    title="Wagtail API",
    version="3.0.0",
    description="Wagtail v3 read and write API",
    urls_namespace="wagtailapi_v3",
    openapi_url="/openapi.json",
    docs_url="/docs/",
)

register_exception_handlers(api)

api.add_router("/pages/", pages_router)
api.add_router("/schema/", schema_router)
