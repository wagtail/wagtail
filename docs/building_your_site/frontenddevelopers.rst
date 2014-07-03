For Front End developers
========================

.. contents:: Contents
    :local:

========================
Overview
========================

Wagtail uses Django's templating language. For developers new to Django, start with Django's own template documentation: 
https://docs.djangoproject.com/en/dev/topics/templates/

Python programmers new to Django/Wagtail may prefer more technical documentation: 
https://docs.djangoproject.com/en/dev/ref/templates/api/

You should be familiar with Django templating basics before continuing with this documentation.

==========================
Templates
==========================

Every type of page or "content type" in Wagtail is defined as a "model" in a file called ``models.py``. If your site has a blog, you might have a ``BlogPage``  model and another called ``BlogPageListing``. The names of the models are up to the Django developer.

For each page model in ``models.py``, Wagtail assumes an HTML template file exists of (almost) the same name. The Front End developer may need to create these templates themselves by refering to ``models.py`` to infer template names from the models defined therein.

To find a suitable template, Wagtail converts CamelCase names to underscore_case. So for a ``BlogPage``, a template ``blog_page.html`` will be expected. The name of the template file can be overridden per model if necessary.

Template files are assumed to exist here::

    name_of_project/
        name_of_app/
            templates/
                name_of_app/
                    blog_page.html
            models.py


For more information, see the Django documentation for the `application directories template loader`_.

.. _application directories template loader: https://docs.djangoproject.com/en/dev/ref/templates/api/


Page content
~~~~~~~~~~~~

The data/content entered into each page is accessed/output through Django's ``{{ double-brace }}`` notation. Each field from the model must be accessed by prefixing ``self.``. e.g the page title ``{{ self.title }}`` or another field ``{{ self.author }}``.

Additionally ``request.`` is available and contains Django's request object.

==============
Static assets
==============

Static files e.g CSS, JS and images are typically stored here::
    
    name_of_project/
        name_of_app/
            static/
                name_of_app/
                    css/
                    js/
                    images/
            models.py

(The names "css", "js" etc aren't important, only their position within the tree.)    

Any file within the static folder should be inserted into your HTML using the ``{% static %}`` tag. More about it: :ref:`static_tag`.

User images
~~~~~~~~~~~

Images uploaded to Wagtail by its users (as opposed to a developer's static files, above) go into the image library and from there are added to pages via the :doc:`page editor interface </editor_manual/new_pages/inserting_images>`.

Unlike other CMS, adding images to a page does not involve choosing a "version" of the image to use. Wagtail has no predefined image "formats" or "sizes". Instead the template developer defines image manipulation to occur *on the fly* when the image is requested, via a special syntax within the template.

Images from the library must be requested using this syntax, but a developer's static images can be added via conventional means e.g ``img`` tags. Only images from the library can be manipulated on the fly.

Read more about the image manipulation syntax here :ref:`image_tag`.


========================
Template tags & filters
========================

In addition to Django's standard tags and filters, Wagtail provides some of its own, which can be ``load``-ed `as you would any other <https://docs.djangoproject.com/en/dev/topics/templates/#custom-tag-and-filter-libraries>`_


.. _image_tag:

Images (tag)
~~~~~~~~~~~~

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

In the above syntax ``[image]`` is the Django object refering to the image. If your page model defined a field called "photo" then ``[image]`` would probably be ``self.photo``. The ``[resize-rule]`` defines how the image is to be resized when inserted into the page; various resizing methods are supported, to cater for different usage cases (e.g. lead images that span the whole width of the page, or thumbnails to be cropped to a fixed size).

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
        (takes two dimensions)

        .. code-block:: django

            {% image self.photo fill-200x200 %}

        Resize and **crop** to fill the **exact** dimensions. 

        This can be particularly useful for websites requiring square thumbnails of arbitrary images. For example, a landscape image of width 2000, height 1000, treated with ``fill`` dimensions ``200x200`` would have its height reduced to 200, then its width (ordinarily 400) cropped to 200. 

        **The crop always aligns on the centre of the image.**

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

Wagtail provides two shorcuts to give greater control over the ``img`` element:

.. versionadded:: 0.4
**Adding attributes to the  {% image %} tag**

Extra attributes can be specified with the syntax ``attribute="value"``:

.. code-block:: django

    {% image self.photo width-400 class="foo" id="bar" %}

No validation is performed on attributes add in this way by the developer. It's possible to add `src`, `width`, `height` and `alt` of your own that might conflict with those generated by the tag itself.


**Generating the image "as"**

Wagtail can assign the image data to another object using Django's ``as`` syntax:

.. code-block:: django

    {% image self.photo width-400 as tmp_photo %}

    <img src="{{ tmp_photo.src }}" width="{{ tmp_photo.width }}" 
        height="{{ tmp_photo.height }}" alt="{{ tmp_photo.alt }}" class="my-custom-class" />

.. versionadded:: 0.4
The ``attrs`` shortcut
-----------------------

You can also use the ``attrs`` property as a shorthand to output the ``src``, ``width``, ``height`` and ``alt`` attributes in one go:

.. code-block:: django

    <img {{ tmp_photo.attrs }} class="my-custom-class" />


.. _rich-text-filter:

Rich text (filter)
~~~~~~~~~~~~~~~~~~

.. versionchanged:: 0.4
    The 'rich_text' tags library was renamed to 'wagtailcore_tags'

This filter takes a chunk of HTML content and renders it as safe HTML in the page. Importantly it also expands internal shorthand references to embedded images and links made in the Wagtail editor into fully-baked HTML ready for display.

Only fields using ``RichTextField`` need this applied in the template.

.. code-block:: django

    {% load wagtailcore_tags %}
    ...
    {{ self.body|richtext }}

.. Note::
    Note that the template tag loaded differs from the name of the filter.

Responsive Embeds
-----------------

Wagtail embeds and images are included at their full width, which may overflow the bounds of the content container you've defined in your templates. To make images and embeds responsive -- meaning they'll resize to fit their container -- include the following CSS.

.. code-block:: css

    .rich-text img {
        max-width: 100%;
        height: auto;
    }

    .responsive-object {
        position: relative;
    }
        .responsive-object iframe,
        .responsive-object object,
        .responsive-object embed {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
        }


Internal links (tag)
~~~~~~~~~~~~~~~~~~~~

.. versionchanged:: 0.4
    The 'pageurl' tags library was renamed to 'wagtailcore_tags'

pageurl
--------

Takes a Page object and returns a relative URL (``/foo/bar/``) if within the same site as the current page, or absolute (``http://example.com/foo/bar/``) if not.

.. code-block:: django

    {% load wagtailcore_tags %}
    ...
    <a href="{% pageurl self.blog_page %}">

slugurl
--------

Takes any ``slug`` as defined in a page's "Promote" tab and returns the URL for the matching Page. Like ``pageurl``, will try to provide a relative link if possible, but will default to an absolute link if on a different site. This is most useful when creating shared page furniture e.g top level navigation or site-wide links.

.. code-block:: django

    {% load wagtailcore_tags %}
    ...
    <a href="{% slugurl self.your_slug %}">


.. _static_tag:

Static files (tag)
~~~~~~~~~~~~~~~~~~

Used to load anything from your static files directory. Use of this tag avoids rewriting all static paths if hosting arrangements change, as they might between  local and a live environments.

.. code-block:: django

    {% load static %}
    ...
    <img src="{% static "name_of_app/myimage.jpg" %}" alt="My image"/>

Notice that the full path name is not required and the path snippet you enter only need begin with the parent app's directory name.



========================
Wagtail User Bar
========================

This tag provides a contextual flyout menu on the top-right of a page for logged-in users. The menu gives editors the ability to edit the current page or add another at the same level. Moderators are also given the ability to accept or reject a page previewed as part of content moderation.

.. code-block:: django

    {% load wagtailuserbar %}
    ...
    {% wagtailuserbar %}

By default the User Bar appears in the top right of the browser window, flush with the edge. If this conflicts with your design it can be moved with a css rule in your own CSS files e.g to move it down from the top:

.. code-block:: css

    #wagtail-userbar{
       top:200px
    }

