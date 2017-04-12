from __future__ import absolute_import, unicode_literals

from django import VERSION as DJANGO_VERSION
from django.db import transaction
from django.db.models.signals import post_delete

from wagtail.wagtaildocs.models import get_document_model


TRANSACTION_ON_COMMIT_AVAILABLE = (1, 8) < DJANGO_VERSION[:2]
if TRANSACTION_ON_COMMIT_AVAILABLE:
    def on_commit_handler(f):
        return transaction.on_commit(f)
else:
    def on_commit_handler(f):
        return f()


def post_delete_file_cleanup(instance, **kwargs):
    # Pass false so FileField doesn't save the model.
    on_commit_handler(lambda: instance.file.delete(False))


def register_signal_handlers():
    Document = get_document_model()
    post_delete.connect(post_delete_file_cleanup, sender=Document)
