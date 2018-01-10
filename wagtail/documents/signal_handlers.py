from django.db import transaction
from django.db.models.signals import post_delete

from wagtail.documents.models import get_document_model


def post_delete_file_cleanup(instance, **kwargs):
    # Pass false so FileField doesn't save the model.
    transaction.on_commit(lambda: instance.file.delete(False))


def register_signal_handlers():
    Document = get_document_model()
    post_delete.connect(post_delete_file_cleanup, sender=Document)
