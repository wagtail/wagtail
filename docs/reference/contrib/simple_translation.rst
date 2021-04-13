.. _simple_translation:

Simple translation
==================

The simple_translation module provides a user interface that allows users to copy pages and translatable snippets into another language.

- Copies are created in the source language (not translated)
- Copies of pages are in draft status

Content editors need to translate the content and publish the pages.

.. note::
   Simple Translation is optional. It can be switched out by third-party packages. Like the more advanced `wagtail-localize <https://github.com/wagtail/wagtail-localize>`_.


Basic configuration
~~~~~~~~~~~~~~~~~~~

Add ``"wagtail.contrib.simple_translation"`` to INSTALLED_APPS in your settings file:

.. code-block:: python

  INSTALLED_APPS = [
      ...
      "wagtail.contrib.simple_translation",
  ]

Run ``python manage.py migrate`` to create the necessary permissions.

In the Wagtail admin, go to settings and give some users or groups the "Can submit translations" permission.
