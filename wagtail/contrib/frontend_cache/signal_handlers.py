from django.apps import apps

from wagtail.contrib.frontend_cache.utils import purge_pages_from_cache
from wagtail.signals import (
    page_published,
    page_slug_changed,
    page_unpublished,
    post_page_move,
)


def page_published_signal_handler(instance, **kwargs):
    purge_pages_from_cache([instance])


def page_unpublished_signal_handler(instance, **kwargs):
    purge_pages_from_cache([instance])


def page_slug_changed_signal_handler(instance, instance_before, **kwargs):
    purge_pages_from_cache([instance, instance_before])


def post_page_move_signal_handler(instance, instance_before, **kwargs):
    # Purge the page's new and old URLs
    purge_pages_from_cache([instance, instance_before])


def register_signal_handlers():
    # Get list of models that are page types
    Page = apps.get_model("wagtailcore", "Page")
    indexed_models = [model for model in apps.get_models() if issubclass(model, Page)]

    # Loop through list and register signal handlers for each one
    for model in indexed_models:
        page_published.connect(page_published_signal_handler, sender=model)
        page_unpublished.connect(page_unpublished_signal_handler, sender=model)
        page_slug_changed.connect(page_slug_changed_signal_handler, sender=model)
        post_page_move.connect(post_page_move_signal_handler, sender=model)
