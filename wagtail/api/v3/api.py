from functools import wraps

from django.conf import settings
from django.http import Http404
from ninja import NinjaAPI

from wagtail.api.v3.errors import register_exception_handlers
from wagtail.api.v3.routers.pages import router as pages_router
from wagtail.api.v3.routers.schema import router as schema_router
from wagtail.api.v3.routers.sites import router as sites_router
from wagtail.api.v3.routers.whoami import router as whoami_router


def _gate_docs(view):
    """
    Uses ``WAGTAILAPI_DOCS_ENABLED`` to 404 the OpenAPI schema / interactive docs.
    """

    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not getattr(settings, "WAGTAILAPI_DOCS_ENABLED", True):
            raise Http404
        return view(request, *args, **kwargs)

    return wrapper


api = NinjaAPI(
    title="Wagtail API",
    version="3.0.0",
    description="Wagtail v3 read and write API",
    urls_namespace="wagtailapi_v3",
    docs_decorator=_gate_docs,
    openapi_url="/openapi.json",
    docs_url="/docs/",
)

register_exception_handlers(api)

api.add_router("/pages/", pages_router)
api.add_router("/schema/", schema_router)
api.add_router("/sites/", sites_router)
api.add_router("/", whoami_router)
