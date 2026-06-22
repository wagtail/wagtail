"""
URL mounting helper for the Wagtail v3 API, to match v2 ergonomics.

Projects mount the API with::

    from wagtail.api.v3.urls import api

    urlpatterns = [
        path("api/v3/", api.urls),
    ]

Routers must be registered on the ``api`` instance before ``api.urls`` is
accessed (Django Ninja raises ``ConfigError`` otherwise).
"""

from wagtail.api.v3.api import api

__all__ = ["api"]
