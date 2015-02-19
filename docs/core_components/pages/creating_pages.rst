====================
Creating page models
====================

Each page type (a.k.a Content type) in Wagtail is represented by a Django model. All page models must inherit from the ``wagtail.wagtailcore.models.Page`` class.

As all page types are Django models, you can use any field type that Django provides. See `Model field reference <https://docs.djangoproject.com/en/1.7/ref/models/fields/>`_ for a complete list of field types you can use. Wagtail also provides ``RichTextField`` which provides a WYSIWYG editor for editing rich-text content.


.. topic:: Django models

    If you're not yet familiar with Django models, have a quick look at the following links to get you started:
    `Creating models <https://docs.djangoproject.com/en/1.7/intro/tutorial01/#creating-models>`_
    `Model syntax <https://docs.djangoproject.com/en/1.7/topics/db/models/>`_


An example Wagtail Page Model
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This example represents a typical blog post:

.. code-block:: python

    from django.db import models

    from wagtail.wagtailcore.models import Page
    from wagtail.wagtailcore.fields import RichTextField
    from wagtail.wagtailadmin.edit_handlers import FieldPanel
    from wagtail.wagtailimages.edit_handlers import ImageChooserPanel


    class BlogPage(Page):
        body = RichTextField()
        date = models.DateField("Post date")
        feed_image = models.ForeignKey(
            'wagtailimages.Image',
            null=True,
            blank=True,
            on_delete=models.SET_NULL,
            related_name='+'
        )

    BlogPage.content_panels = [
        FieldPanel('title', classname="full title"),
        FieldPanel('date'),
        FieldPanel('body', classname="full"),
    ]

    BlogPage.promote_panels = [
        FieldPanel('slug'),
        FieldPanel('seo_title'),
        FieldPanel('show_in_menus'),
        FieldPanel('search_description'),
        ImageChooserPanel('feed_image'),
    ]

.. tip::
    To keep track of ``Page`` models and avoid class name clashes, it can be helpful to suffix model class names with "Page" e.g BlogPage, ListingIndexPage. 

In the example above the ``BlogPage`` class defines three properties: ``body``, ``date``, and ``feed_image``. These are a mix of basic Django models (``DateField``), Wagtail fields (``RichTextField``), and a pointer to a Wagtail model (``Image``).

Below that the ``content_panels`` and ``promote_panels`` lists define the capabilities and layout of the page editing interface in the Wagtail admin. The lists are filled with "panels" and "choosers", which will provide a fine-grain interface for inputting the model's content. The ``ImageChooserPanel``, for instance, lets one browse the image library, upload new images and input image metadata. The ``RichTextField`` is the basic field for creating web-ready website rich text, including text formatting and embedded media like images and video. The Wagtail admin offers other choices for fields, Panels, and Choosers, with the option of creating your own to precisely fit your content without workarounds or other compromises.

Your models may be even more complex, with methods overriding the built-in functionality of the ``Page`` to achieve webdev magic. Or, you can keep your models simple and let Wagtail's built-in functionality do the work.


``Page`` Class Reference
~~~~~~~~~~~~~~~~~~~~~~~~

Default fields
--------------

Wagtail provides some fields for the ``Page`` class by default, which will be common to all your pages. You don't need to add these fields to your own page models however you do need to allocate them to ``content_panels``, ``promote_panels`` or ``settings_panels``. See above example and for further information on the panels see :ref:`editing-api`.

    ``title`` (string, required)
        Human-readable title of the page - what you'd probably use as your ``<h1>`` tag.

    ``slug`` (string, required)
        Machine-readable URL component for this page. The name of the page as it will appear in URLs e.g ``http://domain.com/blog/[my-slug]/``

    ``seo_title`` (string)
        Alternate SEO-crafted title, mainly for use in the page ``<title>`` tag.

    ``search_description`` (string)
        SEO-crafted description of the content, used for internal search indexing, suitable for your page's ``<meta name="description">`` tag.

    ``show_in_menus`` (boolean)
        Toggles whether the page should be considered for inclusion in any site-wide menus you create.


Page Attributes, Properties and Methods Reference
-------------------------------------------------

In addition to the model fields provided, ``Page`` has many properties and methods that you may wish to reference, use, or override in creating your own models. Those listed here are relatively straightforward to use, but consult the Wagtail source code for a full view of what's possible.

.. automodule:: wagtail.wagtailcore.models
.. autoclass:: Page

    .. autoattribute:: specific

    .. autoattribute:: specific_class

    .. autoattribute:: url

    .. autoattribute:: full_url
    
    .. automethod:: get_verbose_name

    .. automethod:: relative_url

    .. automethod:: is_navigable

    .. automethod:: route

    .. automethod:: serve

    .. automethod:: get_context

    .. automethod:: get_template

    .. autoattribute:: preview_modes

    .. automethod:: serve_preview

    .. automethod:: get_ancestors

    .. automethod:: get_descendants

    .. automethod:: get_siblings

    .. automethod:: search

    .. attribute:: search_fields
        
        A list of fields to be indexed by the search engine. See Search docs :ref:`wagtailsearch_indexing_fields`

    .. attribute:: subpage_types

        A whitelist of page models which can be created as children of this page type e.g a ``BlogIndex`` page might allow ``BlogPage``, but not ``JobPage`` e.g

        .. code-block:: python

            class BlogIndex(Page):
                subpage_types = ['mysite.BlogPage', 'mysite.BlogArchivePage']

    .. attribute:: password_required_template

        Defines which template file should be used to render the login form for Protected pages using this model. This overrides the default, defined using ``PASSWORD_REQUIRED_TEMPLATE`` in your settings. See :ref:`private_pages`


Tips
~~~~

Friendly model names
--------------------

Make your model names more friendly to users of Wagtail using Django's internal ``Meta`` class with a ``verbose_name`` e.g

.. code-block:: python
    
    class HomePage(Page):
        ...

        class Meta:
            verbose_name = "Homepage"

When users are given a choice of pages to create, the list of page types is generated by splitting your model names on each of their capital letters. Thus a ``HomePage`` model would be named "Home Page" which is a little clumsy. ``verbose_name`` as in the example above, would change this to read "Homepage" which is slightly more conventional.


Helpful model descriptions
--------------------------

As your site becomes more complex users may require some prompting in deciding which content type to use when creating a new page. Developers can add a description to their Models by extending Django's internal model ``Meta`` class.

Insert the following once at the top of your ``models.py``:

.. code-block:: python

    import django.db.models.options as options
    options.DEFAULT_NAMES = options.DEFAULT_NAMES + ('description',)
     

Then for each model as necessary, add a description option to the model ``Meta`` class


.. code-block:: python

    class HomePage(Page):
        ...
        
        class Meta:
            description = "The top level homepage for your site"
            verbose_name = "Homepage"


(This method can be used to extend the Model Meta class in various ways however Wagtail only supports the addition of a ``description`` option).
