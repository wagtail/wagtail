======
Images
======


.. _image_tag:

Using images in templates
=========================

.. versionchanged:: 0.4
    The 'image_tags' tags library was renamed to 'wagtailimages_tags'

The ``image`` tag inserts an XHTML-compatible ``img`` element into the page, setting its ``src``, ``width``, ``height`` and ``alt``. See also :ref:`image_tag_alt`.

The syntax for the tag is thus::

    {% image [image] [resize-rule] %}

For example:

.. code-block:: django

    {% load wagtailimages_tags %}
    ...

    {% image self.photo width-400 %}

    <!-- or a square thumbnail: -->
    {% image self.photo fill-80x80 %}

In the above syntax example ``[image]`` is the Django object refering to the image. If your page model defined a field called "photo" then ``[image]`` would probably be ``self.photo``. The ``[resize-rule]`` defines how the image is to be resized when inserted into the page; various resizing methods are supported, to cater for different usage cases (e.g. lead images that span the whole width of the page, or thumbnails to be cropped to a fixed size).

Note that a space separates ``[image]`` and ``[resize-rule]``, but the resize rule must not contain spaces.


The available resizing methods are:


.. glossary::

    ``max`` 
        (takes two dimensions)

        .. code-block:: django

            {% image self.photo max-1000x500 %}

        Fit **within** the given dimensions. 

        The longest edge will be reduced to the equivalent dimension size defined. e.g A portrait image of width 1000, height 2000, treated with the ``max`` dimensions ``1000x500`` (landscape) would result in the image shrunk so the *height* was 500 pixels and the width 250.

    ``min`` 
        (takes two dimensions)

        .. code-block:: django

            {% image self.photo min-500x200 %}

        **Cover** the given dimensions.

        This may result in an image slightly **larger** than the dimensions you specify. e.g A square image of width 2000, height 2000, treated with the ``min`` dimensions ``500x200`` (landscape) would have it's height and width changed to 500, i.e matching the width required, but greater than the height.

    ``width`` 
        (takes one dimension)

        .. code-block:: django

            {% image self.photo width-640 %}

        Reduces the width of the image to the dimension specified.

    ``height`` 
        (takes one dimension)

        .. code-block:: django

            {% image self.photo height-480 %}

        Resize the height of the image to the dimension specified.. 

    ``fill`` 
        (takes two dimensions and an optional ``-c`` parameter)

        .. code-block:: django

            {% image self.photo fill-200x200 %}

        Resize and **crop** to fill the **exact** dimensions. 

        This can be particularly useful for websites requiring square thumbnails of arbitrary images. For example, a landscape image of width 2000, height 1000, treated with ``fill`` dimensions ``200x200`` would have its height reduced to 200, then its width (ordinarily 400) cropped to 200.

        This filter will crop to the image's focal point if it has been set. If not, it will crop to the centre of the image.

        **Cropping closer to the focal point**

        By default, Wagtail will only crop to change the aspect ratio of the image.

        In some cases (thumbnails, for example) it may be nice to crop closer to the focal point so the subject of the image is easier to see.

        You can do this by appending ``-c<percentage>`` at the end of the method. For example, if you would like the image to be cropped as closely as possible to its focal point, add ``-c100`` to the end of the method.

        .. code-block:: django

            {% image self.photo fill-200x200-c100 %}

        This will crop the image as much as it an but will never crop into the focal point.

        If you find that ``-c100`` is too close, you can try ``-c75`` or ``-c50`` (any whole number from 0 to 100 is accepted).

    ``original`` 
        (takes no dimensions)

        .. code-block:: django

            {% image self.photo original %}

        Leaves the image at its original size - no resizing is performed.



.. Note::
    Wagtail does not allow deforming or stretching images. Image dimension ratios will always be kept. Wagtail also *does not support upscaling*. Small images forced to appear at larger sizes will "max out" at their their native dimensions.


.. _image_tag_alt:

More control over the ``img`` tag
---------------------------------

Wagtail provides two shortcuts to give greater control over the ``img`` element:

**1. Adding attributes to the  {% image %} tag**

.. versionadded:: 0.4

Extra attributes can be specified with the syntax ``attribute="value"``:

.. code-block:: django

    {% image self.photo width-400 class="foo" id="bar" %}

No validation is performed on attributes added in this way so it's possible to add `src`, `width`, `height` and `alt` of your own that might conflict with those generated by the tag itself.


**2. Generating the image "as foo" to access individual properties**

Wagtail can assign the image data to another variable using Django's ``as`` syntax:

.. code-block:: django

    {% image self.photo width-400 as tmp_photo %}

    <img src="{{ tmp_photo.url }}" width="{{ tmp_photo.width }}" 
        height="{{ tmp_photo.height }}" alt="{{ tmp_photo.alt }}" class="my-custom-class" />
        

This syntax exposes the underlying image "Rendition" (``tmp_photo``) to the developer. A "Rendition" contains just the information specific to the way you've requested to format the image i.e dimensions and source URL.

If your site defines a custom image model using ``AbstractImage``, then any additional fields you add to an image e.g a copyright holder, are **not** part of the image *rendition*, they're part of the image *model*. 

Therefore in the above example, if you'd added the field ``foo`` to your AbstractImage you'd access it using ``{{ self.photo.foo }}`` not ``{{ tmp_photo.foo }}``. 

(Due to the links in the database between renditions and their parent image, you could also access it as ``{{ tmp_photo.image.foo }}`` but this is clearly confusing.)


.. Note::      
    The image property used for the ``src`` attribute is actually ``image.url``, not ``image.src``.


The ``attrs`` shortcut
-----------------------

.. versionadded:: 0.4

You can also use the ``attrs`` property as a shorthand to output the attributes ``src``, ``width``, ``height`` and ``alt`` in one go:

.. code-block:: django

    <img {{ tmp_photo.attrs }} class="my-custom-class" />



Advanced topics
===============

.. toctree::
    :maxdepth: 2

    using_images_outside_wagtail
    feature_detection

