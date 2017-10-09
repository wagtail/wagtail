.. _custom_image_model:

===================
Custom image models
===================

The ``Image`` model can be customised, allowing additional fields to be added
to images.

To do this, you need to add two models to your project:

 - The image model itself that inherits from
   ``wagtail.wagtailimages.models.AbstractImage``. This is where you would add
   your additional fields
 - The renditions model that inherits from
   ``wagtail.wagtailimages.models.AbstractRendition``. This is used to store
   renditions for the new model.

Here's an example:

.. code-block:: python

    # models.py
    from django.db import models

    from wagtail.wagtailimages.models import Image, AbstractImage, AbstractRendition


    class CustomImage(AbstractImage):
        # Add any extra fields to image here

        # eg. To add a caption field:
        # caption = models.CharField(max_length=255, blank=True)

        admin_form_fields = Image.admin_form_fields + (
            # Then add the field names here to make them appear in the form:
            # 'caption',
        )


    class CustomRendition(AbstractRendition):
        image = models.ForeignKey(CustomImage, related_name='renditions')

        class Meta:
            unique_together = (
                ('image', 'filter_spec', 'focal_point_key'),
            )


.. versionchanged:: 1.10

    In previous versions of Wagtail it was necessary to connect signal handlers to handle deletion of image files. As of Wagtail 1.10 this is now handled automatically.

.. note::

    Fields defined on a custom image model must either be set as non-required
    (``blank=True``), or specify a default value - this is because uploading
    the image and entering custom data happen as two separate actions, and
    Wagtail needs to be able to create an image record immediately on upload.

Then set the ``WAGTAILIMAGES_IMAGE_MODEL`` setting to point to it:

.. code-block:: python

    WAGTAILIMAGES_IMAGE_MODEL = 'images.CustomImage'


.. topic:: Migrating from the builtin image model

    When changing an existing site to use a custom image model, no images will
    be copied to the new model automatically. Copying old images to the new
    model would need to be done manually with a
    `data migration <https://docs.djangoproject.com/en/1.8/topics/migrations/#data-migrations>`_.

    Any templates that reference the builtin image model will still continue to
    work as before but would need to be updated in order to see any new images.

.. _custom_image_model_referring_to_image_model:

Referring to the image model
============================

.. module:: wagtail.wagtailimages

.. autofunction:: get_image_model

.. autofunction:: get_image_model_string
