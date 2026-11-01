from django.apps import apps
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.urls import NoReverseMatch, reverse

from wagtail.api.utils import get_base_url
from wagtail.models import get_page_models
from wagtail.signals import page_published, page_unpublished


def use_frontend_cache():
    if not (
        getattr(settings, "WAGTAILAPI_USE_FRONTENDCACHE", False)
        and apps.is_installed("wagtail.api.v3")
    ):
        return False
    if not apps.is_installed("wagtail.contrib.frontend_cache"):
        raise ImproperlyConfigured(
            "The setting 'WAGTAILAPI_USE_FRONTENDCACHE' is True but "
            "'wagtail.contrib.frontend_cache' is not in INSTALLED_APPS."
        )
    return True


def purge_api_url_from_cache(url_name, **kwargs):
    from wagtail.contrib.frontend_cache.utils import purge_url_from_cache

    try:
        path = reverse(f"wagtailapi_v3:{url_name}", kwargs=kwargs)
    except NoReverseMatch:
        # The v3 API URLs are not mounted in this project
        return
    purge_url_from_cache(get_base_url() + path)


def purge_page_from_cache(instance, **kwargs):
    purge_api_url_from_cache("detail_page", page_id=instance.id)


def register_signal_handlers():
    for model in get_page_models():
        page_published.connect(purge_page_from_cache, sender=model)
        page_unpublished.connect(purge_page_from_cache, sender=model)


def unregister_signal_handlers():
    for model in get_page_models():
        page_published.disconnect(purge_page_from_cache, sender=model)
        page_unpublished.disconnect(purge_page_from_cache, sender=model)
