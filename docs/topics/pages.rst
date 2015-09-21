===========
Page models
===========

Each page type (a.k.a Content type) in Wagtail is represented by a Django model. All page models must inherit from the :class:`wagtail.wagtailcore.models.Page` class.

As all page types are Django models, you can use any field type that Django provides. See `Model field reference <https://docs.djangoproject.com/en/1.7/ref/models/fields/>`_ for a complete list of field types you can use. Wagtail also provides :class:`~wagtail.wagtailcore.fields.RichTextField` which provides a WYSIWYG editor for editing rich-text content.


.. topic:: Django models

    If you're not yet familiar with Django models, have a quick look at the following links to get you started:
    `Creating models <https://docs.djangoproject.com/en/1.7/intro/tutorial01/#creating-models>`_
    `Model syntax <https://docs.djangoproject.com/en/1.7/topics/db/models/>`_


An example Wagtail page model
=============================

This example represents a typical blog post:

.. code-block:: python

    from django.db import models

    from modelcluster.fields import ParentalKey

    from wagtail.wagtailcore.models import Page, Orderable
    from wagtail.wagtailcore.fields import RichTextField
    from wagtail.wagtailadmin.edit_handlers import FieldPanel, MultiFieldPanel, InlinePanel
    from wagtail.wagtailimages.edit_handlers import ImageChooserPanel
    from wagtail.wagtailsearch import index


    class BlogPage(Page):

        # Database fields

        body = RichTextField()
        date = models.DateField("Post date")
        feed_image = models.ForeignKey(
            'wagtailimages.Image',
            null=True,
            blank=True,
            on_delete=models.SET_NULL,
            related_name='+'
        )


        # Search index configuraiton

        search_fields = Page.search_fields + (
            index.SearchField('body'),
            index.FilterField('date'),
        )


        # Editor panels configuration

        content_panels = Page.content_panels + [
            FieldPanel('date'),
            FieldPanel('body', classname="full"),
            InlinePanel('related_links', label="Related links"),
        ]

        promote_panels = [
            MultiFieldPanel(Page.promote_panels, "Common page configuration"),
            ImageChooserPanel('feed_image'),
        ]


        # Parent/sub page type rules

        parent_page_types = ['blog.BlogIndex']
        subpage_types = []


    class BlogPageRelatedLink(Orderable):
        page = ParentalKey(BlogPage, related_name='related_links')
        name = models.CharField(max_length=255)
        url = models.URLField()

        panels = [
            FieldPanel('name'),
            FieldPanel('url'),
        ]

.. tip::

    To keep track of ``Page`` models and avoid class name clashes, it can be helpful to suffix model class names with "Page" e.g BlogPage, ListingIndexPage. 


Writing page models
===================

Here we'll describe each section of the above example to help you create your own page models.


Database fields
---------------

Each Wagtail page type is a Django model, which are each represented in the database as a table.

Each page type can have its own set of fields. For example, a news article may have body text and a published date whereas an event page may need separate fields for venue and start/finish times.

In Wagtail, you can use any Django field class. Most field classes provided by `third party apps <https://code.djangoproject.com/wiki/DjangoResources#Djangoapplicationcomponents>`_ should work as well.

Wagtail provides a couple of field classes of its own as well:

 - ``RichTextField`` - For rich text content
 - ``StreamField`` - A block-based content field (see: :doc:`/topics/streamfield`)

For tagging, Wagtail fully supports `django-taggit <https://django-taggit.readthedocs.org/en/latest/>`_ so we recommend using that.


Search
------

The ``search_fields`` attribute defines which fields are added to the search index and how they are indexed.

This should be set to a tuple, of ``SearchField`` and ``FilterField`` objects. ``SearchField`` adds a field for full-text search. ``FilterField`` adds a field for filtering the results. A field can be indexed with both ``SearchField`` and ``FilterField`` at the same time (but only one instance of each).

In the above example, we've indexed ``body`` for full-text search and ``date`` for filtering.

The arguments that these field types accept are documented `here <wagtailsearch_indexing_fields>`_.


Editor panels
-------------

There are a few attributes for defining edit panels on a page model. Each represents the list of panels on their respective tabs in the page editor interface.

 - ``content_panels`` - For content, such as main body text
 - ``promote_panels`` - For metadata, such as tags, thumbnail image and SEO title
 - ``settings_panels`` - For settings, such as publish date

Each of these attributes is set a list of ``EditHandler`` objects which defines which fields appear on which tabs and how they are structured on each tab.

Here's a summary of the ``EditHandler`` classes that Wagtail provides out of the box. See :doc:`/reference/pages/panels` for full descriptions.

**Basic**

These allow editing of model fields, the ``FieldPanel`` class will choose the correct widget based on the type of the field. ``StreamField`` fields need to use a specialised panel class.

 - :class:`~wagtail.wagtailadmin.edit_handlers.FieldPanel`
 - :class:`~wagtail.wagtailadmin.edit_handlers.StreamFieldPanel`

**Structural**

These are used for structuring fields in the interface.

 - :class:`~wagtail.wagtailadmin.edit_handlers.MultiFieldPanel` - For grouping similar fields together
 - :class:`~wagtail.wagtailadmin.edit_handlers.InlinePanel` - For inlining child models
 - :class:`~wagtail.wagtailadmin.edit_handlers.FieldRowPanel` - For organising multiple fields into a single row

**Chooser**

``ForeignKey`` fields to certain models can use one of the below ``ChooserPanel`` classes. These add a nice modal-based chooser interface (and the image/document choosers also allow uploading new files without leaving the page editor).

 - :class:`~wagtail.wagtailadmin.edit_handlers.PageChooserPanel`
 - :class:`~wagtail.wagtailimages.edit_handlers.ImageChooserPanel`
 - :class:`~wagtail.wagtaildocs.edit_handlers.DocumentChooserPanel`
 - :class:`~wagtail.wagtailsnippets.edit_handlers.SnippetChooserPanel`

.. note::

    In order to use one of these choosers, the model being linked to must either be a page, image, document or snippet.

    Linking to any other model type is currently unsupported, you will need to use ``FieldPanel`` which will create a dropdown box.


TODO: We probably should link to "customising the editor interface" here

Parent/sub page type rules
--------------------------

These two attributes allow you to control where page types may be used in your site. It allows you to define rules like "blog entries may only be created under a blog index".

Both take a list of model classes or model names. Model names are of the format ``app_label.ModelName``. If the ``app_label`` is omitted, the same app is assumed.

- ``parent_page_types`` limits which page types this types can be created under
- ``subpage_types`` limits which page types that can be created under this type

By default, any page type can be created under any page type and it is not necessary to set these attributes if that's the desired behaviour.

Setting ``parent_page_types`` to an empty list is a good way of preventing a particular page type from being created in the editor interface.


Template rendering
==================

Lots to cover here.

Template naming convention
How templates are called (what is the default context)
How to override behaviour
 - get_context
 - serve not as important, but mention them anyway


Child models
============

TODO: https://pypi.python.org/pypi/django-modelcluster


Database representation
=======================

Querying pages
==============

TODO: In these two sections, we must describe multi-table inheritance...

NOTE: The reason I renamed this to "page models" is because I think it would be a good place to also describe "general usage" of pages, such as finding the specific object, the url or overriding the template/template context. I think that things like creating pages programmatically probably should be documented elsewhere but linked to from here.

Tips
====

Friendly model names
--------------------

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
