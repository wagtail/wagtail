from django.db.models.signals import post_delete, post_save

from wagtail.search import index


def post_save_signal_handler(instance, update_fields=None, **kwargs):
    if update_fields is not None:
        # fetch a fresh copy of instance from the database to ensure
        # that we're not indexing any of the unsaved data contained in
        # the fields that were not passed in update_fields
        instance = type(instance).objects.get(pk=instance.pk)

    index.insert_or_update_object(instance)


def post_delete_signal_handler(instance, **kwargs):
    index.remove_object(instance)


def register_signal_handlers():
    # Loop through list and register signal handlers for each one
    for model in index.get_indexed_models():
        if not getattr(model, 'search_auto_update', True):
            continue

        post_save.connect(post_save_signal_handler, sender=model)
        post_delete.connect(post_delete_signal_handler, sender=model)
