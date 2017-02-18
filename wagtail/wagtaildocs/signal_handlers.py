from __future__ import absolute_import, unicode_literals

from django.db.models.signals import post_delete

from wagtail.wagtaildocs.models import Document


# Receive the post_delete signal and delete the file associated with the model instance.
def post_delete_document_file_cleanup(sender, instance, **kwargs):
    # Pass false so FileField doesn't save the model.
    instance.file.delete(False)


def register_signal_handlers():
    post_delete.connect(post_delete_document_file_cleanup, sender=Document)
