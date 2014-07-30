.. _using_images_outside_wagtail:

============================
Using images outside Wagtail
============================

Wagtail provides a way for you to generate external URLs for images in your image library which you can use to display your images on external sites.


Setup
=====

Add an entry in your URLs configuration for ``wagtail.wagtailimages.urls``:

 .. code-block:: python

    from wagtail.wagtailimages import urls as wagtailimages_urls


    urlpatterns = patterns('',
        ...

        url(r'^images/', include(wagtailimages_urls)),

        ...
    )


Generating URLs for images
==========================

Once the above setup is done, a button should appear under the image preview on the image edit page. Clicking this button will take you to an interface where you can specify the size you want the image to be, and it will generate a URL and a preview of what the image is going to look like.

The filter box lets you choose how you would like the image to be resized:


.. glossary::
    ``Original`` 

        Leaves the image at its original size - no resizing is performed.

    ``Resize to max`` 

        Fit **within** the given dimensions. 

        The longest edge will be reduced to the equivalent dimension size defined. e.g A portrait image of width 1000, height 2000, treated with the ``max`` dimensions ``1000x500`` (landscape) would result in the image shrunk so the *height* was 500 pixels and the width 250.

    ``Resize to min`` 

        **Cover** the given dimensions.

        This may result in an image slightly **larger** than the dimensions you specify. e.g A square image of width 2000, height 2000, treated with the ``min`` dimensions ``500x200`` (landscape) would have it's height and width changed to 500, i.e matching the width required, but greater than the height.

    ``Resize to width`` 

        Reduces the width of the image to the dimension specified.

    ``Resize to height`` 

        Resize the height of the image to the dimension specified.. 

    ``Resize to fill`` 

        Resize and **crop** to fill the **exact** dimensions. 

        This can be particularly useful for websites requiring square thumbnails of arbitrary images. For example, a landscape image of width 2000, height 1000, treated with ``fill`` dimensions ``200x200`` would have its height reduced to 200, then its width (ordinarily 400) cropped to 200. 


Using the URLs on your website or blog
======================================

Once you have generated a URL, you can put it straight into the ``src`` attribute of an ``<img>`` tag:

..code-block:: html

    <img src="(image url here)">


Performance
===========

Currently, Wagtail will regenerate the image every time it is requested. For high volume sites, it is recommended to use a frontend cache to reduce load on the backend servers.
