from __future__ import absolute_import, unicode_literals

import logging

from django.db.models.signals import post_delete, post_save

from wagtail.wagtailsearch.backends import get_search_backends_with_name
from wagtail.wagtailsearch.index import get_indexed_models

logger = logging.getLogger('wagtail.search.auto_reindex')


def get_indexed_instance(instance):
    indexed_instance = instance.get_indexed_instance()
    if indexed_instance is None:
        return

    # Make sure that the instance is in its class's indexed objects
    if not type(indexed_instance).get_indexed_objects().filter(pk=indexed_instance.pk).exists():
        return

    return indexed_instance


def post_save_signal_handler(instance, **kwargs):
    indexed_instance = get_indexed_instance(instance)

    if indexed_instance:
        for backend_name, backend in get_search_backends_with_name(with_auto_update=True):
            try:
                backend.add(indexed_instance)
            except:
                # Catch and log all errors
                logger.exception("Exception raised while adding an object into the '%s' search backend", backend_name)


def post_delete_signal_handler(instance, **kwargs):
    indexed_instance = get_indexed_instance(instance)

    if indexed_instance:
        for backend_name, backend in get_search_backends_with_name(with_auto_update=True):
            try:
                backend.delete(indexed_instance)
            except:
                # Catch and log all errors
                logger.exception("Exception raised while deleting an object from the '%s' search backend", backend_name)


def register_signal_handlers():
    # Loop through list and register signal handlers for each one
    for model in get_indexed_models():
        post_save.connect(post_save_signal_handler, sender=model)
        post_delete.connect(post_delete_signal_handler, sender=model)
