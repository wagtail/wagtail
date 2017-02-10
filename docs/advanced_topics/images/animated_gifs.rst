Animated GIF support
====================

Pillow, Wagtail's default image library, doesn't support animated
GIFs.

To get animated GIF support, you will have to
`install Wand <http://docs.wand-py.org/en/0.4.2/guide/install.html>`_.
Wand is a binding to ImageMagick so make sure that has been installed as well.

When installed, Wagtail will automatically use Wand for resizing GIF
files but continue to resize other images with Pillow.
