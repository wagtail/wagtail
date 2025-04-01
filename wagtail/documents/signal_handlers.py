from django.db import transaction
from django.db.models.signals import post_delete

from wagtail.documents import get_document_model
from wagtail.tasks import delete_file_from_storage_task


def post_delete_file_cleanup(instance, **kwargs):
    transaction.on_commit(
        lambda: delete_file_from_storage_task.enqueue(
            instance.file.storage.deconstruct(), instance.file.name
        )
    )


def register_signal_handlers():
    Document = get_document_model()
    post_delete.connect(post_delete_file_cleanup, sender=Document)
