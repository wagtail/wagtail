.. _legacy_richtext:

=====================
Legacy richtext
=====================

.. module:: wagtail.contrib.legacy.richtext

Provides the legacy richtext wrapper.

Place ``wagtail.contrib.legacy.richtext`` before ``wagtail.core`` in  ``INSTALLED_APPS``.

 .. code-block:: python

    INSTALLED_APPS = [
        ...
        "wagtail.contrib.legacy.richtext",
        "wagtail.core",
        ...
    ]

The ``{{ page.body|richtext }}`` template filter will now render:

 .. code-block:: html+django

    <div class="rich-text">...</div>
