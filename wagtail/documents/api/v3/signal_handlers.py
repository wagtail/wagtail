from django.db.models.signals import post_delete, post_save

from wagtail.api.v3.signal_handlers import purge_api_url_from_cache
from wagtail.documents import get_document_model


def purge_document_from_cache(instance, **kwargs):
    if not kwargs.get("created", False):
        purge_api_url_from_cache("detail_document", document_id=instance.id)


def register_signal_handlers():
    Document = get_document_model()
    post_save.connect(purge_document_from_cache, sender=Document)
    post_delete.connect(purge_document_from_cache, sender=Document)


def unregister_signal_handlers():
    Document = get_document_model()
    post_save.disconnect(purge_document_from_cache, sender=Document)
    post_delete.disconnect(purge_document_from_cache, sender=Document)
