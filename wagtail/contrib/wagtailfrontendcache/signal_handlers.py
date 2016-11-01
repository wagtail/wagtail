from __future__ import absolute_import, unicode_literals

from django.apps import apps
from django.db.models.signals import post_save
from django.db.models.signals import post_delete

from wagtail.contrib.wagtailfrontendcache.utils import purge_page_from_cache
from wagtail.contrib.wagtailfrontendcache.utils import purge_url_from_cache
from wagtail.contrib.wagtailfrontendcache.utils import get_sites
from wagtail.wagtailcore.signals import page_published, page_unpublished


def page_published_signal_handler(instance, **kwargs):
    purge_page_from_cache(instance)


def page_unpublished_signal_handler(instance, **kwargs):
    purge_page_from_cache(instance)


def redirect_signal_handler(sender, instance, **kwargs):
    sites = get_sites(instance.site_id)
    for site in sites:
        purge_url = site.root_url + instance.old_path + '/'
        purge_url_from_cache(purge_url)


def register_signal_handlers():
    # Get list of models that are page types
    Page = apps.get_model('wagtailcore', 'Page')
    indexed_models = [model for model in apps.get_models() if issubclass(model, Page)]

    # Loop through list and register signal handlers for each one
    for model in indexed_models:
        page_published.connect(page_published_signal_handler, sender=model)
        page_unpublished.connect(page_unpublished_signal_handler, sender=model)

    # Get redirect model
    Redirect = apps.get_model('wagtailredirects', 'Redirect')

    # Register signal handlers for redirect model
    post_save.connect(redirect_signal_handler, sender=Redirect)
    post_delete.connect(redirect_signal_handler, sender=Redirect)
