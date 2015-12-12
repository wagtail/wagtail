.. _jinja2:

=======================
Jinja2 template support
=======================

Wagtail supports Jinja2 templating for all front end features. More information on each of the template tags below can be found in the :ref:`writing_templates` documentation.

Configuring Django
==================

.. versionchanged:: 1.3

    Jinja2 tags were moved from "templatetags" into "jinja2tags" to separate them from Django template tags.

Django needs to be configured to support Jinja2 templates. As the Wagtail admin is written using regular Django templates, Django has to be configured to use both templating engines. Wagtail supports the Jinja2 backend that ships with Django 1.8 and above. Add the following configuration to the ``TEMPLATES`` setting for your app:

.. code-block:: python

    TEMPLATES = [
        # ...
        {
            'BACKEND': 'django.template.backends.jinja2.Jinja2',
            'APP_DIRS': True,
            'OPTIONS': {
                'extensions': [
                    'wagtail.wagtailcore.jinja2tags.core',
                    'wagtail.wagtailadmin.jinja2tags.userbar',
                    'wagtail.wagtailimages.jinja2tags.images',
                ],
            },
        }
    ]

Jinja templates must be placed in a ``jinja2/`` directory in your app. The template for an ``EventPage`` model in an ``events`` app should be created at ``events/jinja2/events/event_page.html``.

By default, the Jinja environment does not have any Django functions or filters. The Django documentation has more information on `configuring Jinja for Django <https://docs.djangoproject.com/en/1.8/topics/templates/#django.template.backends.jinja2.Jinja2>`_.

``self`` in templates
=====================

In Django templates, ``self`` can be used to refer to the current page, stream block, or field panel. In Jinja, ``self`` is reserved for internal use. When writing Jinja templates, use ``page`` to refer to pages, ``value`` for stream blocks, and ``field_panel`` for field panels.

Template functions & filters
============================

``pageurl()``
~~~~~~~~~~~~~

Generate a URL for a Page instance:

.. code-block:: html+jinja

    <a href="{{ pageurl(page.more_information) }}">More information</a>

See :ref:`pageurl_tag` for more information

``slugurl()``
~~~~~~~~~~~~~

Generate a URL for a Page with a slug:

.. code-block:: html+jinja

    <a href="{{ slugurl("about") }}">About us</a>

See :ref:`slugurl_tag` for more information

``image()``
~~~~~~~~~~~

Resize an image, and print an ``<img>`` tag:

.. code-block:: html+jinja

    {# Print an image tag #}
    {{ image(page.header_image, "fill-1024x200", class="header-image") }}

    {# Resize an image #}
    {% set background=image(page.background_image, "max-1024x1024") %}
    <div class="wrapper" style="background-image: url({{ background.url }});">

See :ref:`image_tag` for more information

``|richtext``
~~~~~~~~~~~~~

Transform Wagtail's internal HTML representation, expanding internal references to pages and images.

.. code-block:: html+jinja

    {{ page.body|richtext }}

See :ref:`rich-text-filter` for more information

``wagtailuserbar()``
~~~~~~~~~~~~~~~~~~~~

Output the Wagtail contextual flyout menu for editing pages from the front end

.. code-block:: html+jinja

    {{ wagtailuserbar() }}

See :ref:`wagtailuserbar_tag` for more information
