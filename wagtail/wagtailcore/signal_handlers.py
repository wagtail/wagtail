from __future__ import absolute_import, unicode_literals

import logging

from django.core.cache import cache
from django.db.models.signals import post_delete, post_save, pre_save, pre_delete

from wagtail.wagtailcore.models import Page, Site

logger = logging.getLogger('wagtail.core')


# Clear the wagtail_site_root_paths from the cache whenever Site records are updated.
def post_save_site_signal_handler(sender, instance, **kwargs):
    cache.delete('wagtail_site_root_paths')


def post_delete_site_signal_handler(sender, instance, **kwargs):
    cache.delete('wagtail_site_root_paths')


def pre_delete_page_unpublish(sender, instance, **kwargs):
    # Make sure pages are unpublished before deleting
    if instance.live:
        # Don't bother to save, this page is just about to be deleted!
        instance.unpublish(commit=False)


def post_delete_page_log_deletion(sender, instance, **kwargs):
    logger.info("Page deleted: \"%s\" id=%d", instance.title, instance.id)


def rebuild_site_cache_post_site_save(sender, instance, **kwargs):
    Site.objects.rebuild_site_cache()


def rebuild_site_cache_post_site_delete(sender, instance, **kwargs):
    Site.objects.rebuild_site_cache(deleted_site=instance)


def rebuild_site_cache_post_site_root_update(sender, instance, **kwargs):
    if instance.sites_rooted_here.all().exists():
        Site.objects.rebuild_site_cache()


def clear_site_cache_pre_site_root_delete(sender, instance, **kwargs):
    if instance.sites_rooted_here.all().exists():
        # Cache will be rebuilt next time Site.get_for_request() is used
        Site.objects.clear_site_cache()


def register_signal_handlers():
    post_save.connect(post_save_site_signal_handler, sender=Site)
    post_save.connect(rebuild_site_cache_post_site_save, sender=Site)
    post_delete.connect(rebuild_site_cache_post_site_delete, sender=Site)
    post_delete.connect(post_delete_site_signal_handler, sender=Site)

    post_save.connect(rebuild_site_cache_post_site_root_update, sender=Page)
    pre_delete.connect(pre_delete_page_unpublish, sender=Page)
    post_delete.connect(post_delete_page_log_deletion, sender=Page)
