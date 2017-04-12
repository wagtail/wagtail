from __future__ import absolute_import, unicode_literals

from django import VERSION as DJANGO_VERSION
from django.db import transaction
from django.db.models.signals import post_delete

from wagtail.wagtaildocs.models import Document


TRANSACTION_ON_COMMIT_AVAILABLE = (1, 8) < DJANGO_VERSION
if TRANSACTION_ON_COMMIT_AVAILABLE:
    on_commit_handler = lambda f: transaction.on_commit(f)
else:
    on_commit_handler = lambda f: f()

def post_delete_file_cleanup(instance, **kwargs):
    # Pass false so FileField doesn't save the model.
    on_commit_handler(lambda: instance.file.delete(False))


def register_signal_handlers():
    post_delete.connect(post_delete_file_cleanup, sender=Document)
