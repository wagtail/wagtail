Animated GIF support
====================

Pillow (Wagtail's default image library) doesn't support resizing animated
GIFs. If you need animated GIFs in your site, install
`Wand <https://pypi.python.org/pypi/Wand>`_.

When Wand is installed, Wagtail will automatically start using it for resizing
GIF files, and will continue to resize other images with Pillow.
