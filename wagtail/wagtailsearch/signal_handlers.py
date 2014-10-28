from django.db.models.signals import post_save, post_delete
from django.db import models

from wagtail.wagtailsearch.index import Indexed
from wagtail.wagtailsearch.backends import get_search_backends


def post_save_signal_handler(instance, **kwargs):
    if not type(instance).get_indexed_objects().filter(id=instance.id).exists():
        return


    for backend in get_search_backends():
        backend.add(instance)


def post_delete_signal_handler(instance, **kwargs):
    if not type(instance).get_indexed_objects().filter(id=instance.id).exists():
        return

    for backend in get_search_backends():
        backend.delete(instance)


def register_signal_handlers():
    # Get list of models that should be indexed
    indexed_models = [model for model in models.get_models() if issubclass(model, Indexed)]

    # Loop through list and register signal handlers for each one
    for model in indexed_models:
        post_save.connect(post_save_signal_handler, sender=model)
        post_delete.connect(post_delete_signal_handler, sender=model)
