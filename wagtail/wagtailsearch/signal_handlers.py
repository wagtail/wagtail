from __future__ import absolute_import, unicode_literals

from django.db.models.signals import post_delete, post_save

from wagtail.wagtailsearch import index


def post_save_signal_handler(instance, **kwargs):
    index.insert_or_update_object(instance)


def post_delete_signal_handler(instance, **kwargs):
    index.remove_object(instance)


def register_signal_handlers():
    # Loop through list and register signal handlers for each one
    for model in index.get_indexed_models():
        post_save.connect(post_save_signal_handler, sender=model)
        post_delete.connect(post_delete_signal_handler, sender=model)
