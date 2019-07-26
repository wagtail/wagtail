=====================
Custom site model
=====================

An alternate ``Site`` model can be used to add custom behaviour and
additional fields.

You need to complete the following steps in your project to do this:

 - Create a new document model that inherits from
   ``wagtail.core.models.AbstractSite``. This is where you would
   add additional fields.
 - Point ``WAGTAILCORE_SITE_MODEL`` to the new model.

Here's an example:

.. code-block:: python

    # models.py
    from wagtail.core.models import AbstractSite

    class CustomSite(AbstractSite):
        # Custom field example:
        registrar = models.CharField(
            max_length=255,
        )

        admin_form_fields = Site.admin_form_fields + (
            # Add all custom fields names to make them appear in the form:
            'registrar',
        )


Then in your settings module:

.. code-block:: python

    # Ensure that you replace app_label with the app you placed your custom
    # model in.
    WAGTAILCORE_SITE_MODEL = 'app_label.CustomSite'

.. topic:: Migrating from the builtin site model

    When changing an existing site to use a custom site model, no site
    will be copied to the new model automatically. Copying old sites to the
    new model would need to be done manually with a
    :ref:`data migration <django:data-migrations>`.

    Any templates that reference the builtin site model will still continue
    to work as before.

Referring to the site model
===============================

.. module:: wagtail.core.models

.. autofunction:: get_site_model
