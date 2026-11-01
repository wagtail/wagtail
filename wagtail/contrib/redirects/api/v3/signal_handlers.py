from django.db.models.signals import post_delete, post_save

from wagtail.api.v3.signal_handlers import purge_api_url_from_cache
from wagtail.contrib.redirects.models import Redirect


def purge_redirect_from_cache(instance, **kwargs):
    if not kwargs.get("created", False):
        purge_api_url_from_cache("detail_redirect", redirect_id=instance.id)


def register_signal_handlers():
    post_save.connect(purge_redirect_from_cache, sender=Redirect)
    post_delete.connect(purge_redirect_from_cache, sender=Redirect)


def unregister_signal_handlers():
    post_save.disconnect(purge_redirect_from_cache, sender=Redirect)
    post_delete.disconnect(purge_redirect_from_cache, sender=Redirect)
