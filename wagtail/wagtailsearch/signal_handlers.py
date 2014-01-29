from django.dispatch import Signal
from django.db.models.signals import post_save, post_delete
from django.db import models
from search import Search
from indexed import Indexed


def post_save_signal_handler(instance, **kwargs):
    Search().add(instance)


def post_delete_signal_handler(instance, **kwargs):
    Search().delete(instance)


def register_signal_handlers():
    # Get list of models that should be indexed
    indexed_models = [model for model in models.get_models() if issubclass(model, Indexed)]

    # Loop through list and register signal handlers for each one
    for model in indexed_models:
        post_save.connect(post_save_signal_handler, sender=model)
        post_delete.connect(post_delete_signal_handler, sender=model)