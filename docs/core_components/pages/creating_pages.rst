====================
Creating page models
====================


The Page Class
~~~~~~~~~~~~~~

``Page`` uses Django's model interface, so you can include any field type and field options that Django allows. Wagtail provides some fields and editing handlers that simplify data entry in the Wagtail admin interface, so you may want to keep those in mind when deciding what properties to add to your models in addition to those already provided by ``Page``.


Built-in Properties of the Page Class
-------------------------------------

Wagtail provides some properties in the ``Page`` class which are common to most webpages. Since you'll be subclassing ``Page``, you don't have to worry about implementing them.

Public Properties
`````````````````

    ``title`` (string, required)
        Human-readable title for the content

    ``slug`` (string, required)
        Machine-readable URL component for this piece of content. The name of the page as it will appear in URLs e.g ``http://domain.com/blog/[my-slug]/``

    ``seo_title`` (string)
        Alternate SEO-crafted title which overrides the normal title for use in the ``<head>`` of a page

    ``search_description`` (string)
        A SEO-crafted description of the content, used in both internal search indexing and for the meta description read by search engines

The ``Page`` class actually has alot more to it, but these are probably the only built-in properties you'll need to worry about when creating templates for your models.


Anatomy of a Wagtail Model
~~~~~~~~~~~~~~~~~~~~~~~~~~

So what does a Wagtail model definition look like? Here's a model representing a typical blog post:

.. code-block:: python

    from django.db import models

    from wagtail.wagtailcore.models import Page
    from wagtail.wagtailcore.fields import RichTextField
    from wagtail.wagtailadmin.edit_handlers import FieldPanel
    from wagtail.wagtailimages.edit_handlers import ImageChooserPanel
    from wagtail.wagtailimages.models import Image

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

To keep track of your ``Page``-derived models, it might be helpful to include "Page" as the last part of your class name. ``BlogPage`` defines three properties: ``body``, ``date``, and ``feed_image``. These are a mix of basic Django models (``DateField``), Wagtail fields (``RichTextField``), and a pointer to a Wagtail model (``Image``).

Next, the ``content_panels`` and ``promote_panels`` lists define the capabilities and layout of the Wagtail admin page edit interface. The lists are filled with "panels" and "choosers", which will provide a fine-grain interface for inputting the model's content. The ``ImageChooserPanel``, for instance, lets one browse the image library, upload new images, and input image metadata. The ``RichTextField`` is the basic field for creating web-ready website rich text, including text formatting and embedded media like images and video. The Wagtail admin offers other choices for fields, Panels, and Choosers, with the option of creating your own to precisely fit your content without workarounds or other compromises.

Your models may be even more complex, with methods overriding the built-in functionality of the ``Page`` to achieve webdev magic. Or, you can keep your models simple and let Wagtail's built-in functionality do the work.

Now that we have a basic idea of how our content is defined, lets look at relationships between pieces of content.


Page Properties and Methods Reference
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In addition to the model fields provided, ``Page`` has many properties and methods that you may wish to reference, use, or override in creating your own models. Those listed here are relatively straightforward to use, but consult the Wagtail source code for a full view of what's possible.

.. automodule:: wagtail.wagtailcore.models
.. autoclass:: Page

    .. autoattribute:: specific

    .. autoattribute:: specific_class

    .. autoattribute:: url

    .. autoattribute:: full_url

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


.. _wagtail_site_admin:

Site
~~~~

Django's built-in admin interface provides the way to map a "site" (hostname or domain) to any node in the wagtail tree, using that node as the site's root.

Access this by going to ``/django-admin/`` and then "Home › Wagtailcore › Sites." To try out a development site, add a single site with the hostname ``localhost`` at port ``8000`` and map it to one of the pieces of content you have created.

Wagtail's developers plan to move the site settings into the Wagtail admin interface.
