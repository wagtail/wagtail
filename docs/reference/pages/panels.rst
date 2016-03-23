.. _editing-api:

Available panel types
=====================

.. module:: wagtail.wagtailadmin.edit_handlers

FieldPanel
----------

.. class:: FieldPanel(field_name, classname=None, widget=None)

    This is the panel used for basic Django field types.

    .. attribute:: FieldPanel.field_name

        This is the name of the class property used in your model definition.

    .. attribute:: FieldPanel.classname

        This is a string of optional CSS classes given to the panel which are used in formatting and scripted interactivity. By default, panels are formatted as inset fields.

        The CSS class ``full`` can be used to format the panel so it covers the full width of the Wagtail page editor.

        The CSS class ``title`` can be used to mark a field as the source for auto-generated slug strings.

    .. attribute:: FieldPanel.widget (optional)

        This parameter allows you to specify a `Django form widget`_ to use instead of the default widget for this field type.

.. _django form widget: https://docs.djangoproject.com/en/dev/ref/forms/widgets/

MultiFieldPanel
---------------

.. class:: MultiFieldPanel(children, heading="", classname=None)

    This panel condenses several :class:`~wagtail.wagtailadmin.edit_handlers.FieldPanel` s or choosers, from a ``list`` or ``tuple``, under a single ``heading`` string.

    .. attribute:: MultiFieldPanel.children

        A ``list`` or ``tuple`` of child panels

    .. attribute:: MultiFieldPanel.heading

        A heading for the fields

.. topic:: Collapsing MultiFieldPanels to save space

    By default, ``MultiFieldPanel`` s are expanded and not collapsible. Adding ``collapsible`` to ``classname`` will enable the collapse control. Adding both ``collapsible`` and ``collapsed`` to the ``classname`` parameter will load the editor page with the ``MultiFieldPanel`` collapsed under its heading.

    .. code-block:: python

        content_panels = [
            MultiFieldPanel(
                [
                    ImageChooserPanel('cover'),
                    DocumentChooserPanel('book_file'),
                    PageChooserPanel('publisher'),
                ],
                heading="Collection of Book Fields",
                classname="collapsible collapsed"
            ),
        ]

InlinePanel
-----------

.. class:: InlinePanel(relation_name, panels=None, classname=None, label='', help_text='', min_num=None, max_num=None)

    This panel allows for the creation of a "cluster" of related objects over a join to a separate model, such as a list of related links or slides to an image carousel.

    This is a poweful but complex feature which will take some space to cover, so we'll skip over it for now. For a full explanation on the usage of ``InlinePanel``, see :ref:`inline_panels`.

FieldRowPanel
-------------

.. class:: FieldRowPanel(children, classname=None)

    This panel creates a columnar layout in the editing interface, where each of the child Panels appears alongside each other rather than below.

    Use of FieldRowPanel particularly helps reduce the "snow-blindness" effect of seeing so many fields on the page, for complex models. It also improves the perceived association between fields of a similar nature. For example if you created a model representing an "Event" which had a starting date and ending date, it may be intuitive to find the start and end date on the same "row".

    FieldRowPanel should be used in combination with ``col*`` class names added to each of the child Panels of the FieldRowPanel. The Wagtail editing interface is laid out using a grid system, in which the maximum width of the editor is 12 columns. Classes ``col1``-``col12`` can be applied to each child of a FieldRowPanel. The class ``col3`` will ensure that field appears 3 columns wide or a quarter the width. ``col4`` would cause the field to be 4 columns wide, or a third the width.

    .. attribute:: FieldRowPanel.children

        A ``list`` or ``tuple`` of child panels to display on the row

    .. attribute:: FieldRowPanel.classname

        A class to apply to the FieldRowPanel as a whole

PageChooserPanel
----------------

.. class:: PageChooserPanel(field_name, page_type=None, can_choose_root=False)

    You can explicitly link :class:`~wagtail.wagtailcore.models.Page`-derived models together using the :class:`~wagtail.wagtailcore.models.Page` model and ``PageChooserPanel``.

    .. code-block:: python

        from wagtail.wagtailcore.models import Page
        from wagtail.wagtailadmin.edit_handlers import PageChooserPanel


        class BookPage(Page):
            publisher = models.ForeignKey(
                'wagtailcore.Page',
                null=True,
                blank=True,
                on_delete=models.SET_NULL,
                related_name='+',
            )

            content_panels = Page.content_panels + [
                PageChooserPanel('related_page', 'demo.PublisherPage'),
            ]

    ``PageChooserPanel`` takes one required argument, the field name. Optionally, specifying a page type (in the form of an ``"appname.modelname"`` string) will filter the chooser to display only pages of that type. A list or tuple of page types can also be passed in, to allow choosing a page that matches any of those page types::

        PageChooserPanel('related_page', ['demo.PublisherPage', 'demo.AuthorPage'])

    Passing ``can_choose_root=True`` will allow the editor to choose the tree root as a page. Normally this would be undesirable, since the tree root is never a usable page, but in some specialised cases it may be appropriate; for example, a page with an automatic "related articles" feed could use a PageChooserPanel to select which subsection articles will be taken from, with the root corresponding to 'everywhere'.


ImageChooserPanel
-----------------

.. module:: wagtail.wagtailimages.edit_handlers

.. class:: ImageChooserPanel(field_name)

    Wagtail includes a unified image library, which you can access in your models through the :class:`~wagtail.wagtailimages.models.Image` model and the ``ImageChooserPanel`` chooser. Here's how:

    .. code-block:: python

      from wagtail.wagtailimages.models import Image
      from wagtail.wagtailimages.edit_handlers import ImageChooserPanel


      class BookPage(Page):
          cover = models.ForeignKey(
              'wagtailimages.Image',
              null=True,
              blank=True,
              on_delete=models.SET_NULL,
              related_name='+'
          )

          content_panels = Page.content_panels + [
              ImageChooserPanel('cover'),
          ]

    Django's default behaviour is to "cascade" deletions through a ForeignKey relationship, which may not be what you want. This is why the ``null``, ``blank``, and ``on_delete`` parameters should be set to allow for an empty field. (See `Django model field reference (on_delete)`_ ). ``ImageChooserPanel`` takes only one argument: the name of the field.

    .. _Django model field reference (on_delete): https://docs.djangoproject.com/en/dev/ref/models/fields/#django.db.models.ForeignKey.on_delete

    Displaying ``Image`` objects in a template requires the use of a template tag. See :ref:`image_tag`.

DocumentChooserPanel
--------------------

.. module:: wagtail.wagtaildocs.edit_handlers

.. class:: DocumentChooserPanel(field_name)

    For files in other formats, Wagtail provides a generic file store through the :class:`~wagtail.wagtaildocs.models.Document` model:

    .. code-block:: python

      from wagtail.wagtaildocs.models import Document
      from wagtail.wagtaildocs.edit_handlers import DocumentChooserPanel


      class BookPage(Page):
          book_file = models.ForeignKey(
              'wagtaildocs.Document',
              null=True,
              blank=True,
              on_delete=models.SET_NULL,
              related_name='+'
          )

          content_panels = Page.content_panels + [
              DocumentChooserPanel('book_file'),
          ]

    As with images, Wagtail documents should also have the appropriate extra parameters to prevent cascade deletions across a ForeignKey relationship. ``DocumentChooserPanel`` takes only one argument: the name of the field.

SnippetChooserPanel
-------------------

.. versionchanged:: 1.1

    Before Wagtail 1.1, it was necessary to pass the snippet model class as a second parameter to ``SnippetChooserPanel``. This is now automatically picked up from the field.

.. module:: wagtail.wagtailsnippets.edit_handlers

.. class:: SnippetChooserPanel(field_name, snippet_type=None)

    Snippets are vanilla Django models you create yourself without a Wagtail-provided base class. A chooser, ``SnippetChooserPanel``, is provided which takes the field name as an argument.

    .. code-block:: python

      from wagtail.wagtailsnippets.edit_handlers import SnippetChooserPanel

      class BookPage(Page):
          advert = models.ForeignKey(
              'demo.Advert',
              null=True,
              blank=True,
              on_delete=models.SET_NULL,
              related_name='+'
          )

          content_panels = Page.content_panels + [
              SnippetChooserPanel('advert'),
          ]

    See :ref:`snippets` for more information.


Built-in Fields and Choosers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Django's field types are automatically recognised and provided with an appropriate widget for input. Just define that field the normal Django way and pass the field name into :class:`~wagtail.wagtailadmin.edit_handlers.FieldPanel` when defining your panels. Wagtail will take care of the rest.

Here are some Wagtail-specific types that you might include as fields in your models.


Field Customisation
~~~~~~~~~~~~~~~~~~~

By adding CSS classes to your panel definitions or adding extra parameters to your field definitions, you can control much of how your fields will display in the Wagtail page editing interface. Wagtail's page editing interface takes much of its behaviour from Django's admin, so you may find many options for customisation covered there. (See `Django model field reference`_ ).

.. _Django model field reference: https://docs.djangoproject.com/en/dev/ref/models/fields/


Full-Width Input
----------------

Use ``classname="full"`` to make a field (input element) stretch the full width of the Wagtail page editor. This will not work if the field is encapsulated in a :class:`~wagtail.wagtailadmin.edit_handlers.MultiFieldPanel`, which places its child fields into a formset.


Titles
------

Use ``classname="title"`` to make Page's built-in title field stand out with more vertical padding.


Required Fields
---------------

To make input or chooser selection mandatory for a field, add ``blank=False`` to its model definition. (See `Django model field reference (blank)`_ ).

.. _Django model field reference (blank): https://docs.djangoproject.com/en/dev/ref/models/fields/#django.db.models.Field.blank


Hiding Fields
-------------

Without a panel definition, a default form field (without label) will be used to represent your fields. If you intend to hide a field on the Wagtail page editor, define the field with ``editable=False`` (See `Django model field reference (editable)`_ ).

.. _Django model field reference (editable): https://docs.djangoproject.com/en/dev/ref/models/fields/#editable


.. _inline_panels:

Inline Panels and Model Clusters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``django-modelcluster`` module allows for streamlined relation of extra models to a Wagtail page. For instance, you can create objects related through a ``ForeignKey`` relationship on the fly and save them to a draft revision of a ``Page`` object. Normally, your related objects "cluster" would need to be created beforehand (or asynchronously) before linking them to a Page.

Let's look at the example of adding related links to a :class:`~wagtail.wagtailcore.models.Page`-derived model. We want to be able to add as many as we like, assign an order, and do all of this without leaving the page editing screen.

.. code-block:: python

  from wagtail.wagtailcore.models import Orderable, Page
  from modelcluster.fields import ParentalKey

  # The abstract model for related links, complete with panels
  class RelatedLink(models.Model):
      title = models.CharField(max_length=255)
      link_external = models.URLField("External link", blank=True)

      panels = [
          FieldPanel('title'),
          FieldPanel('link_external'),
      ]

      class Meta:
          abstract = True

  # The real model which combines the abstract model, an
  # Orderable helper class, and what amounts to a ForeignKey link
  # to the model we want to add related links to (BookPage)
  class BookPageRelatedLinks(Orderable, RelatedLink):
      page = ParentalKey('demo.BookPage', related_name='related_links')

  class BookPage(Page):
    # ...

    content_panels = Page.content_panels + [
      InlinePanel('related_links', label="Related Links"),
    ]

The ``RelatedLink`` class is a vanilla Django abstract model. The ``BookPageRelatedLinks`` model extends it with capability for being ordered in the Wagtail interface via the ``Orderable`` class as well as adding a ``page`` property which links the model to the ``BookPage`` model we're adding the related links objects to. Finally, in the panel definitions for ``BookPage``, we'll add an :class:`~wagtail.wagtailadmin.edit_handlers.InlinePanel` to provide an interface for it all. Let's look again at the parameters that :class:`~wagtail.wagtailadmin.edit_handlers.InlinePanel` accepts:

.. code-block:: python

    InlinePanel( relation_name, panels=None, label='', help_text='', min_num=None, max_num=None )

The ``relation_name`` is the ``related_name`` label given to the cluster's ``ParentalKey`` relation. You can add the ``panels`` manually or make them part of the cluster model. ``label`` and ``help_text`` provide a heading and caption, respectively, for the Wagtail editor. Finally, ``min_num`` and ``max_num`` allow you to set the minimum/maximum number of forms that the user must submit.

.. versionchanged:: 1.0

    In previous versions, it was necessary to pass the base model as the first parameter to :class:`~wagtail.wagtailadmin.edit_handlers.InlinePanel`; this is no longer required.

For another example of using model clusters, see :ref:`tagging`

For more on ``django-modelcluster``, visit `the django-modelcluster github project page`_.

.. _the django-modelcluster github project page: https://github.com/torchbox/django-modelcluster
