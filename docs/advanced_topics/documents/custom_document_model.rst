=====================
Custom document model
=====================

An alternate ``Document`` model can be used to add custom behaviour and
additional fields.

You need to complete the following steps in your project to do this:

 - Create a new document model that inherits from
   ``wagtail.wagtaildocs.models.AbstractDocument``. This is where you would
   add additional fields.
 - Add a signal handler to duplicate the post-delete behaviour from
   ``wagtaildocs.signal_handlers.post_delete_document_file_cleanup```.
   This ensures the uploaded file is cleaned up when a document is deleted.
 - Point ``WAGTAILDOCS_DOCUMENT_MODEL`` to the new model.

Here's an example:

.. code-block:: python

    # models.py
    from django.db.models.signals import post_delete
    from django.dispatch import receiver

    from wagtail.wagtaildocs.models import Document, AbstractDocument

    class CustomDocument(AbstractDocument):
        # Custom field example:
        source = models.CharField(
            max_length=255,
            # This must be set to allow Wagtail to create a document instance
            # on upload.
            blank=True,
            null=True
        )

        admin_form_fields = Document.admin_form_fields + (
            # Add all custom fields names to make them appear in the form:
            'source',
        )

    # Add the signal handler.
    # The sender kwarg should match up with your custom document model name.
    @receiver(post_delete, sender=CustomDocument)
    def post_delete_document_file_cleanup(sender, instance, **kwargs):
        # See wagtaildocs.signal_handlers.post_delete_document_file_cleanup
        instance.file.delete(False)

.. note::

    Fields defined on a custom document model must either be set as non-required
    (``blank=True``), or specify a default value. This is because uploading the
    document and entering custom data happens as two separate actions. Wagtail
    needs to be able to create a document record immediately on upload.

Then in your settings module:

.. code-block:: python

    # Ensure that you replace app_label with the app you placed your custom
    # model in.
    WAGTAILDOCS_DOCUMENT_MODEL = 'app_label.CustomDocument'

.. topic:: Migrating from the builtin document model

    When changing an existing site to use a custom document model, no documents
    will be copied to the new model automatically. Copying old documents to the
    new model would need to be done manually with a
    `data migration <https://docs.djangoproject.com/en/1.8/topics/migrations/#data-migrations>`_.

    Any templates that reference the builtin document model will still continue
    to work as before.

Referring to the document model
===============================

.. module:: wagtail.wagtaildocs.models

.. autofunction:: get_document_model
