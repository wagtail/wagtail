from __future__ import absolute_import, unicode_literals

from django.apps import apps
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.signals import post_save, pre_save

from wagtail.contrib.wagtailfrontendcache.utils import purge_page_from_cache, purge_url_from_cache
from wagtail.wagtailcore.signals import page_published, page_unpublished


def has_changed(instance, field):
    if not instance.pk:
        return False
    try:
        old_value = instance.__class__._default_manager.filter(pk=instance.pk).values(field).get()[field]
    except ObjectDoesNotExist:
        return False
    return not getattr(instance, field) == old_value


def get_old_instance(instance):
    if not instance.pk:
        return False
    try:
        old_instance = instance.__class__._default_manager.get(pk=instance.pk)
    except ObjectDoesNotExist:
        return False
    return old_instance


def page_published_signal_handler(instance, **kwargs):
    purge_page_from_cache(instance)


def page_unpublished_signal_handler(instance, **kwargs):
    purge_page_from_cache(instance)


def page_pre_saved_signal_handler(instance, **kwargs):
    if has_changed(instance, 'url_path'):
        old_instance = get_old_instance(instance)
        instance.old_url = old_instance.full_url
    else:
        instance.old_url = None


def page_post_saved_signal_handler(instance, **kwargs):
    if not kwargs['update_fields']:
        if instance.old_url:
            purge_url_from_cache(instance.old_url)


def register_signal_handlers():
    # Get list of models that are page types
    Page = apps.get_model('wagtailcore', 'Page')
    indexed_models = [model for model in apps.get_models() if issubclass(model, Page)]

    # Loop through list and register signal handlers for each one
    for model in indexed_models:
        page_published.connect(page_published_signal_handler, sender=model)
        page_unpublished.connect(page_unpublished_signal_handler, sender=model)
        pre_save.connect(page_pre_saved_signal_handler, sender=model)
        post_save.connect(page_post_saved_signal_handler, sender=model)
