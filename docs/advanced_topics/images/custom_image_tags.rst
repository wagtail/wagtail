Custom Image Template Tags
==========================

Sometimes Wagtail’s built-in ``{% image %}`` template tag isn’t enough for specific use-cases.
This guide shows how to create custom image template tags to:

* Resize images dynamically from template variables
* Add object-fit styles
* Apply CSS classes based on image dimensions

Rendition API
-------------

### img_tag

Renders an HTML ``<img>`` tag for a given image rendition. You can pass extra attributes like ``class`` or ``style`` to customize output.

Example::

    {{ page.header_image.get_rendition('max-800x600').img_tag(class="rounded") }}

See the :ref:`Rendition API <reference/models/rendition>` for more details.

### get_renditions_or_not_found

Returns a list of renditions that match a given filter. Raises an error if no matching renditions are found.

Example::

    {% set renditions = page.header_image.get_renditions_or_not_found("max-800x600") %}
    {% for r in renditions %}
        {{ r.img_tag }}
    {% endfor %}

See the :ref:`Rendition API <reference/models/rendition>` for more details.

Filter Class
------------

The ``Filter`` class lets you create reusable custom image transformations. You can define a set of operations (resize, crop, etc.) and apply them in templates or code.

Example::

    from wagtail.images import Filter

    # Create a custom filter
    my_filter = Filter('max-400x400', auto_orient=True)

    # Apply it in a template
    {{ page.header_image.get_rendition(my_filter).img_tag }}

See the :ref:`Image Filter documentation <reference/images/filters>` for full options.

ResponsiveImage and Picture
---------------------------

``ResponsiveImage`` and ``Picture`` help you create responsive layouts that adapt to different screen sizes.

Example using ``ResponsiveImage``::

    {% set responsive = page.header_image.get_rendition('max-1024x1024') %}
    {{ responsive|responsive_image }}

.. image:: /_static/images/responsive_example.jpg
   :alt: Example of a responsive image
   :class: responsive

Example using ``Picture``::

    {% picture page.header_image "max-800x800" "max-400x400" alt="Header image" class="responsive" %}

.. image:: /_static/images/picture_example.jpg
   :alt: Example of a picture element
   :class: responsive

See the :ref:`ResponsiveImage and Picture reference docs <reference/images/responsive>` for more details.

Tips
----

* Always check available renditions with ``get_renditions_or_not_found``.
* Use ``Filter`` for reusable transformations.
* Use ``img_tag`` for quick ``<img>`` output with extra attributes.
* Reference the :ref:`Rendition API <reference/models/rendition>` for advanced options and additional parameters.