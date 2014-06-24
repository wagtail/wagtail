from django.db import models
from django.db.models.signals import post_save, post_delete

from wagtail.wagtailcore.models import Page

from wagtail.contrib.wagtailfrontendcache.utils import purge_page_from_cache


def post_save_signal_handler(instance, **kwargs):
    purge_page_from_cache(instance)


def post_delete_signal_handler(instance, **kwargs):
    purge_page_from_cache(instance)


def register_signal_handlers():
    # Get list of models that are page types
    indexed_models = [model for model in models.get_models() if issubclass(model, Page)]

    # Loop through list and register signal handlers for each one
    for model in indexed_models:
        post_save.connect(post_save_signal_handler, sender=model)
        post_delete.connect(post_delete_signal_handler, sender=model)
