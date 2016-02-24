.. _writing_templates:

=================
Writing templates
=================

Wagtail uses Django's templating language. For developers new to Django, start with Django's own template documentation: 
https://docs.djangoproject.com/en/dev/topics/templates/

Python programmers new to Django/Wagtail may prefer more technical documentation: 
https://docs.djangoproject.com/en/dev/ref/templates/api/

You should be familiar with Django templating basics before continuing with this documentation.

Templates
=========

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

The data/content entered into each page is accessed/output through Django's ``{{ double-brace }}`` notation. Each field from the model must be accessed by prefixing ``page.``. e.g the page title ``{{ page.title }}`` or another field ``{{ page.author }}``.

Additionally ``request.`` is available and contains Django's request object.

Static assets
=============

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


Template tags & filters
=======================

In addition to Django's standard tags and filters, Wagtail provides some of its own, which can be ``load``-ed `as you would any other <https://docs.djangoproject.com/en/dev/topics/templates/#custom-tag-and-filter-libraries>`_


Images (tag)
~~~~~~~~~~~~

The ``image`` tag inserts an XHTML-compatible ``img`` element into the page, setting its ``src``, ``width``, ``height`` and ``alt``. See also :ref:`image_tag_alt`.

The syntax for the tag is thus::

    {% image [image] [resize-rule] %}

For example:

.. code-block:: html+django

    {% load wagtailimages_tags %}
    ...

    {% image page.photo width-400 %}

    <!-- or a square thumbnail: -->
    {% image page.photo fill-80x80 %}


See :ref:`image_tag` for full documentation.


.. _rich-text-filter:

Rich text (filter)
~~~~~~~~~~~~~~~~~~

This filter takes a chunk of HTML content and renders it as safe HTML in the page. Importantly it also expands internal shorthand references to embedded images and links made in the Wagtail editor into fully-baked HTML ready for display.

Only fields using ``RichTextField`` need this applied in the template.

.. code-block:: html+django

    {% load wagtailcore_tags %}
    ...
    {{ page.body|richtext }}

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

.. _pageurl_tag:

``pageurl``
-----------

Takes a Page object and returns a relative URL (``/foo/bar/``) if within the same site as the current page, or absolute (``http://example.com/foo/bar/``) if not.

.. code-block:: html+django

    {% load wagtailcore_tags %}
    ...
    <a href="{% pageurl page.blog_page %}">

.. _slugurl_tag:

``slugurl``
------------

Takes any ``slug`` as defined in a page's "Promote" tab and returns the URL for the matching Page. Like ``pageurl``, will try to provide a relative link if possible, but will default to an absolute link if on a different site. This is most useful when creating shared page furniture e.g top level navigation or site-wide links.

.. code-block:: html+django

    {% load wagtailcore_tags %}
    ...
    <a href="{% slugurl page.your_slug %}">


.. _static_tag:

Static files (tag)
~~~~~~~~~~~~~~~~~~

Used to load anything from your static files directory. Use of this tag avoids rewriting all static paths if hosting arrangements change, as they might between  local and a live environments.

.. code-block:: html+django

    {% load static %}
    ...
    <img src="{% static "name_of_app/myimage.jpg" %}" alt="My image"/>

Notice that the full path name is not required and the path snippet you enter only need begin with the parent app's directory name.


.. _wagtailuserbar_tag:

Wagtail User Bar
================

This tag provides a contextual flyout menu on the top-right of a page for logged-in users. The menu gives editors the ability to edit the current page or add another at the same level. Moderators are also given the ability to accept or reject a page previewed as part of content moderation.

.. code-block:: html+django

    {% load wagtailuserbar %}
    ...
    {% wagtailuserbar %}

By default the User Bar appears in the top right of the browser window, flush with the edge. If this conflicts with your design it can be moved with a css rule in your own CSS files e.g to move it down from the top:

.. code-block:: css

    #wagtail-userbar{
       top:200px
    }


Varying output between preview and live
=======================================

Sometimes you may wish to vary the template output depending on whether the page is being previewed or viewed live. For example, if you have visitor tracking code such as Google Analytics in place on your site, it's a good idea to leave this out when previewing, so that editor activity doesn't appear in your analytics reports. Wagtail provides a ``request.is_preview`` variable to distinguish between preview and live:

.. code-block:: html+django

    {% if not request.is_preview %}
        <script>
          (function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
          ...
        </script>
    {% endif %}
