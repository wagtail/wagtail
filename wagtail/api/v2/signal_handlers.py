from __future__ import absolute_import, unicode_literals

from django.core.urlresolvers import reverse
from django.db.models.signals import post_delete, post_save

from wagtail.contrib.wagtailfrontendcache.utils import purge_url_from_cache
from wagtail.wagtailcore.models import get_page_models
from wagtail.wagtailcore.signals import page_published, page_unpublished
from wagtail.wagtaildocs.models import get_document_model
from wagtail.wagtailimages.models import get_image_model

from .utils import get_base_url


def purge_page_from_cache(instance, **kwargs):
    base_url = get_base_url()
    purge_url_from_cache(base_url + reverse('wagtailapi_v2:pages:detail', args=(instance.id, )))


def purge_image_from_cache(instance, **kwargs):
    if not kwargs.get('created', False):
        base_url = get_base_url()
        purge_url_from_cache(base_url + reverse('wagtailapi_v2:images:detail', args=(instance.id, )))


def purge_document_from_cache(instance, **kwargs):
    if not kwargs.get('created', False):
        base_url = get_base_url()
        purge_url_from_cache(base_url + reverse('wagtailapi_v2:documents:detail', args=(instance.id, )))


def register_signal_handlers():
    Image = get_image_model()
    Document = get_document_model()

    for model in get_page_models():
        page_published.connect(purge_page_from_cache, sender=model)
        page_unpublished.connect(purge_page_from_cache, sender=model)

    post_save.connect(purge_image_from_cache, sender=Image)
    post_delete.connect(purge_image_from_cache, sender=Image)
    post_save.connect(purge_document_from_cache, sender=Document)
    post_delete.connect(purge_document_from_cache, sender=Document)


def unregister_signal_handlers():
    Image = get_image_model()
    Document = get_document_model()

    for model in get_page_models():
        page_published.disconnect(purge_page_from_cache, sender=model)
        page_unpublished.disconnect(purge_page_from_cache, sender=model)

    post_save.disconnect(purge_image_from_cache, sender=Image)
    post_delete.disconnect(purge_image_from_cache, sender=Image)
    post_save.disconnect(purge_document_from_cache, sender=Document)
    post_delete.disconnect(purge_document_from_cache, sender=Document)
