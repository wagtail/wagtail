from django.db.models.signals import post_delete, post_save

from wagtail.api.v3.signal_handlers import purge_api_url_from_cache
from wagtail.images import get_image_model


def purge_image_from_cache(instance, **kwargs):
    if not kwargs.get("created", False):
        purge_api_url_from_cache("detail_image", image_id=instance.id)


def register_signal_handlers():
    Image = get_image_model()
    post_save.connect(purge_image_from_cache, sender=Image)
    post_delete.connect(purge_image_from_cache, sender=Image)


def unregister_signal_handlers():
    Image = get_image_model()
    post_save.disconnect(purge_image_from_cache, sender=Image)
    post_delete.disconnect(purge_image_from_cache, sender=Image)
