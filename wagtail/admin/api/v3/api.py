from ninja import NinjaAPI

from wagtail.api.v3.errors import register_exception_handlers

from .routers import router as pages_router

api = NinjaAPI(
    title="Wagtail Admin API",
    version="3.0.0",
    description="Wagtail Admin v3 read and write API",
    urls_namespace="wagtailadmin_api_v3",
    openapi_url="/openapi.json",
    docs_url="/docs/",
)

register_exception_handlers(api)

api.add_router("/pages/", pages_router)
