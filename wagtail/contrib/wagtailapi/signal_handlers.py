from django.core.urlresolvers import reverse
from django.db.models.signals import post_save, post_delete

from wagtail.wagtailcore.signals import page_published, page_unpublished
from wagtail.wagtailcore.models import PAGE_MODEL_CLASSES
from wagtail.wagtailimages.models import get_image_model
from wagtail.wagtaildocs.models import Document

from wagtail.contrib.wagtailfrontendcache.utils import purge_url_from_cache

from .utils import get_base_url


def purge_page_from_cache(instance, **kwargs):
    base_url = get_base_url()
    purge_url_from_cache(base_url + reverse('wagtailapi_v1:pages:detail', args=(instance.id, )))


def purge_image_from_cache(instance, **kwargs):
    if not kwargs.get('created', False):
        base_url = get_base_url()
        purge_url_from_cache(base_url + reverse('wagtailapi_v1:images:detail', args=(instance.id, )))


def purge_document_from_cache(instance, **kwargs):
    if not kwargs.get('created', False):
        base_url = get_base_url()
        purge_url_from_cache(base_url + reverse('wagtailapi_v1:documents:detail', args=(instance.id, )))


def register_signal_handlers():
    Image = get_image_model()

    for model in PAGE_MODEL_CLASSES:
        page_published.connect(purge_page_from_cache, sender=model)
        page_unpublished.connect(purge_page_from_cache, sender=model)

    post_save.connect(purge_image_from_cache, sender=Image)
    post_delete.connect(purge_image_from_cache, sender=Image)
    post_save.connect(purge_document_from_cache, sender=Document)
    post_delete.connect(purge_document_from_cache, sender=Document)


def unregister_signal_handlers():
    Image = get_image_model()

    for model in PAGE_MODEL_CLASSES:
        page_published.disconnect(purge_page_from_cache, sender=model)
        page_unpublished.disconnect(purge_page_from_cache, sender=model)

    post_save.disconnect(purge_image_from_cache, sender=Image)
    post_delete.disconnect(purge_image_from_cache, sender=Image)
    post_save.disconnect(purge_document_from_cache, sender=Document)
    post_delete.disconnect(purge_document_from_cache, sender=Document)
