====================
Creating page models
====================

Each page type (a.k.a Content type) in Wagtail is represented by a Django model. All page models must inherit from the :class:`wagtail.wagtailcore.models.Page` class.

As all page types are Django models, you can use any field type that Django provides. See `Model field reference <https://docs.djangoproject.com/en/1.7/ref/models/fields/>`_ for a complete list of field types you can use. Wagtail also provides :class:`~wagtail.wagtailcore.fields.RichTextField` which provides a WYSIWYG editor for editing rich-text content.


.. topic:: Django models

    If you're not yet familiar with Django models, have a quick look at the following links to get you started:
    `Creating models <https://docs.djangoproject.com/en/1.7/intro/tutorial01/#creating-models>`_
    `Model syntax <https://docs.djangoproject.com/en/1.7/topics/db/models/>`_


An example Wagtail Page Model
=============================

This example represents a typical blog post:

.. code-block:: python

    from django.db import models

    from wagtail.wagtailcore.models import Page
    from wagtail.wagtailcore.fields import RichTextField
    from wagtail.wagtailadmin.edit_handlers import FieldPanel, MultiFieldPanel
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

        content_panels = Page.content_panels + [
            FieldPanel('date'),
            FieldPanel('body', classname="full"),
        ]

        promote_panels = [
            MultiFieldPanel(Page.promote_panels, "Common page configuration"),
            ImageChooserPanel('feed_image'),
        ]

.. tip::
    To keep track of ``Page`` models and avoid class name clashes, it can be helpful to suffix model class names with "Page" e.g BlogPage, ListingIndexPage. 

In the example above the ``BlogPage`` class defines three properties: ``body``, ``date``, and ``feed_image``. These are a mix of basic Django models (``DateField``), Wagtail fields (:class:`~wagtail.wagtailcore.fields.RichTextField`), and a pointer to a Wagtail model (:class:`~wagtail.wagtailimages.models.Image`).

Below that the ``content_panels`` and ``promote_panels`` lists define the capabilities and layout of the page editing interface in the Wagtail admin. The lists are filled with "panels" and "choosers", which will provide a fine-grain interface for inputting the model's content. The :class:`~wagtail.wagtailimages.edit_handlers.ImageChooserPanel`, for instance, lets one browse the image library, upload new images and input image metadata. The :class:`~wagtail.wagtailcore.fields.RichTextField` is the basic field for creating web-ready website rich text, including text formatting and embedded media like images and video. The Wagtail admin offers other choices for fields, Panels, and Choosers, with the option of creating your own to precisely fit your content without workarounds or other compromises.

Your models may be even more complex, with methods overriding the built-in functionality of the :class:`~wagtail.wagtailcore.models.Page` to achieve webdev magic. Or, you can keep your models simple and let Wagtail's built-in functionality do the work.

Setting up the page editor interface
====================================

Wagtail provides a highly-customisable editing interface consisting of several components:

  * **Fields** — built-in content types to augment the basic types provided by Django
  * **Panels** — the basic editing blocks for fields, groups of fields, and related object clusters
  * **Choosers** — interfaces for finding related objects in a ForeignKey relationship

Configuring your models to use these components will shape the Wagtail editor to your needs. Wagtail also provides an API for injecting custom CSS and JavaScript for further customisation, including extending the ``hallo.js`` rich text editor.

There is also an Edit Handler API for creating your own Wagtail editor components.

Defining Panels
~~~~~~~~~~~~~~~

A "panel" is the basic editing block in Wagtail. Wagtail will automatically pick the appropriate editing widget for most Django field types; implementers just need to add a panel for each field they want to show in the Wagtail page editor, in the order they want them to appear.

Wagtail provides a tabbed interface to help organise panels. Three such tabs are provided:

* ``content_panels`` is the main tab, used for the bulk of your model's fields.
* ``promote_panels`` is suggested for organising fields regarding the promotion of the page around the site and the Internet. For example, a field to dictate whether the page should show in site-wide menus, descriptive text that should appear in site search results, SEO-friendly titles, OpenGraph meta tag content and other machine-readable information.
* ``settings_panels`` is essentially for non-copy fields. By default it contains the page's scheduled publishing fields. Other suggested fields could include a field to switch between one layout/style and another.

Let's look at an example of a panel definition:

.. code-block:: python

  class ExamplePage(Page):
    # field definitions omitted
    ...

    content_panels = Page.content_panels + [
      FieldPanel('body', classname="full"),
      FieldRowPanel([
        FieldPanel('start_date', classname="col3"),
        FieldPanel('end_date', classname="col3"),
      ]),
      ImageChooserPanel('splash_image'),
      DocumentChooserPanel('free_download'),
      PageChooserPanel('related_page'),
    ]

    promote_panels = [
      MultiFieldPanel(Page.promote_panels, "Common page configuration"),
    ]

After the :class:`~wagtail.wagtailcore.models.Page`-derived class definition, just add lists of panel definitions to order and organise the Wagtail page editing interface for your model.

Tips
====

Friendly model names
~~~~~~~~~~~~~~~~~~~~

Make your model names more friendly to users of Wagtail using Django's internal ``Meta`` class with a ``verbose_name`` e.g

.. code-block:: python
    
    class HomePage(Page):
        ...

        class Meta:
            verbose_name = "homepage"

When users are given a choice of pages to create, the list of page types is generated by splitting your model names on each of their capital letters. Thus a ``HomePage`` model would be named "Home Page" which is a little clumsy. ``verbose_name`` as in the example above, would change this to read "Homepage" which is slightly more conventional.


Page QuerySet ordering
----------------------

``Page``-derived models *cannot* be given a default ordering by using the standard Django approach of adding an ``ordering`` attribute to the internal ``Meta`` class.

.. code-block:: python

    class NewsItemPage(Page):
        publication_date = models.DateField()
        ...

        class Meta:
            ordering = ('-publication_date', )  # will not work

This is because ``Page`` enforces ordering QuerySets by path. Instead you must apply the ordering explicitly when you construct a QuerySet:

.. code-block:: python

    news_items = NewsItemPage.objects.live().order_by('-publication_date')

Page custom managers
--------------------

``Page`` enforces its own 'objects' manager in its ``__init__`` method, so you cannot add a custom manager at the 'objects' attribute.

.. code-block:: python

    class EventPageQuerySet(PageQuerySet):

        def future(self):
            return self.filter(
                start_date__gte=timezone.localtime(timezone.now()).date()
            )

    class EventPage(Page):
        start_date = models.DateField()

        objects = EventPageQuerySet.as_manager()  # will not work

To use a custom manager you must choose a different attribute name. Make sure to subclass ``wagtail.wagtailcore.models.PageManager``.

.. code-block:: python

    from django.db import models
    from django.utils import timezone
    from wagtail.wagtailcore.models import Page, PageManager


    class FutureEventPageManager(PageManager):

        def get_queryset(self):
            return super().get_queryset().filter(
                start_date__gte=timezone.localtime(timezone.now()).date()
            )


    class EventPage(Page):
        start_date = models.DateField()

        future_events = FutureEventPageManager()

Then you can use ``EventPage.future_events`` in the manner you might expect.
