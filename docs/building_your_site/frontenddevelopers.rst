For Front End developers
========================

.. note::
    This documentation is currently being written.

========================
Overview
========================

Wagtail uses Django's templating language. For developers new to Django, start with Django's own template documentation: 
https://docs.djangoproject.com/en/dev/topics/templates/

Python programmers new to Django/Wagtail may prefer more technical documentation: 
https://docs.djangoproject.com/en/dev/ref/templates/api/

========================
Page content and variables
========================


========================
Static files (css, js, images)
========================



Images
~~~~~~~~~~

Images uploaded to Wagtail go into the image library and from there are added to pages via the :doc:`page editor interface </editor_manual/new_pages/inserting_images>`.

Unlike other CMS, adding images to a page does not involve choosing a "version" of the image to use. Wagtail has no predefined image "formats" or "sizes". Instead the template developer defines image manipulation to occur *on the fly* when the image is requested, via a special syntax within the template.

Images from the library **must** be requested using this syntax, but images in your codebase can be added via conventional means e.g ``img`` tags. Only images from the library can be manipulated on the fly.

Read more about the image manipulation syntax here :ref:`Images tag <image-tag>`.


========================
Template tags & filters
========================

In addition to Django's standard tags and filters, Wagtail provides some of it's own, which can be ``load``-ed `as you would any other <https://docs.djangoproject.com/en/dev/topics/templates/#custom-tag-and-filter-libraries>`_

.. _image-tag:
Images (tag)
~~~~~~~~~~~~

The syntax for displaying/manipulating an image is thus::

    {% image [image] [method]-[dimension(s)] %}

The ``image`` is the Django object refering to the image. If your page model defined a field called "photo" then ``image`` would probably be ``self.photo``. The ``method`` defines which resizing algorithm to use and ``dimension(s)`` provides height and/or width values (as ``[height]`` or ``[width]x[height]``) to refine that algorithm.

Note that a space separates ``image`` and ``method``, but not ``method`` and ``dimensions``. A hyphen between ``width`` and ``dimensions`` is mandatory.

The available ``method`` s are:

.. glossary::
    ``max`` 
        (takes two dimensions)

        Fit **within** the given dimensions. 

        The longest edge will be reduced to the equivalent dimension size defined. e.g A portrait image of width 1000, height 2000, treated with the ``max`` dimensions ``1000x500`` (landscape) would result in the image shrunk so the *height* was 500 pixels and the width 250.

    ``min`` 
        (takes two dimensions)

        **Cover** the given dimensions.

        This may result in an image slightly **larger** than the dimensions you specify. e.g A square image of width 2000, height 2000, treated with the ``min`` dimensions ``500x200`` (landscape) would have it's height and width changed to 500, i.e matching the width required, but greater than the height.

    ``width`` 
        (takes one dimension)

        Reduces the width of the image to the dimension specified.

    ``height`` 
        (takes one dimension)

        Resize the height of the image to the dimension specified.. 

    ``fill`` 
        (takes two dimensions)

        Resize and **crop** to fill the **exact** dimensions. 

        This can be particularly useful for websites requiring square thumbnails of arbitrary images. e.g A landscape image of width 2000, height 1000, treated with ``fill`` dimensions ``200x200`` would have it's height reduced to 200, then it's width (ordinarily 400) cropped to 200. 

        **The crop always aligns on the centre of the image.**

.. Note::
    Wagtail *does not allow deforming or stretching images*. Image dimension ratios will always be kept. Wagtail also *does not support upscaling*. Small images forced to appear at larger sizes will "max out" at their their native dimensions.


Rich text (filter)
~~~~~~~~~~~~~~~~~~


Internal links (tag)
~~~~~~~~~~~~~~~~~~~~


Static files (tag)
~~~~~~~~~~~~~~


Misc
~~~~~~~~~~


========================
Wagtail User Bar
========================

