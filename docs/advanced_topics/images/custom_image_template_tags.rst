Custom image template tags
==========================

Wagtail provides built-in image template tags such as ``{% image %}`` for most common use cases.
However, there are situations where projects require more control over how images are rendered.

This page explains how to create custom image template tags using Wagtail’s image APIs.

When to use a custom image tag
------------------------------

You may want to create a custom image template tag if you need to:

- Apply dynamic resize rules from template variables
- Add custom CSS styles or attributes (for example, supporting ``object-fit``)
- Change the output based on image dimensions
- Integrate image rendering into a design system

Using ``img_tag`` on a Rendition
--------------------------------

Each image rendition provides an ``img_tag`` method that returns a complete ``<img>`` HTML tag.

Example::

    rendition = image.get_rendition("fill-400x300")
    html = rendition.img_tag()

This can be useful when building custom template tags that need full control over the output.

Creating a simple custom image template tag
--------------------------------------------

A basic custom image template tag can be implemented by creating a Django template tag
and using Wagtail’s rendition APIs.

Example::

    @register.simple_tag
    def custom_image(image, filter_spec):
        rendition = image.get_rendition(filter_spec)
        return rendition.img_tag()

This approach allows you to extend Wagtail’s image rendering while reusing its core logic.

Further APIs
------------

Advanced image rendering can also make use of:

- ``get_renditions_or_not_found``
- The ``Filter`` class
- ``ResponsiveImage`` and ``Picture`` helpers

Refer to the image API reference documentation for more details.
