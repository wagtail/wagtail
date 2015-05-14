.. _editing-api:

Setting up the page editor interface
====================================

Wagtail provides a highly-customizable editing interface consisting of several components:

  * **Fields** — built-in content types to augment the basic types provided by Django
  * **Panels** — the basic editing blocks for fields, groups of fields, and related object clusters
  * **Choosers** — interfaces for finding related objects in a ForeignKey relationship

Configuring your models to use these components will shape the Wagtail editor to your needs. Wagtail also provides an API for injecting custom CSS and JavaScript for further customization, including extending the ``hallo.js`` rich text editor.

There is also an Edit Handler API for creating your own Wagtail editor components.

Defining Panels
~~~~~~~~~~~~~~~

A "panel" is the basic editing block in Wagtail. Wagtail will automatically pick the appropriate editing widget for most Django field types; implementors just need to add a panel for each field they want to show in the Wagtail page editor, in the order they want them to appear.

Wagtail provides a tabbed interface to help organize panels. Three such tabs are provided:

* ``content_panels`` is the main tab, used for the bulk of your model's fields.
* ``promote_panels`` is suggested for organizing fields regarding the promotion of the page around the site and the Internet. For example, a field to dictate whether the page should show in site-wide menus, descriptive text that should appear in site search results, SEO-friendly titles, OpenGraph meta tag content and other machine-readable information.
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

After the ``Page``-derived class definition, just add lists of panel definitions to order and organize the Wagtail page editing interface for your model.

Available panel types
~~~~~~~~~~~~~~~~~~~~~

.. module:: wagtail.wagtailadmin.edit_handers

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

        This parameter allows you to specify a `django form widget`_ to use instead of the default widget for this field type.

.. _django form widget: https://docs.djangoproject.com/en/dev/ref/forms/widgets/

MultiFieldPanel
---------------

.. class:: MultiFieldPanel(children, heading="", classname=None)

    This panel condenses several ``FieldPanel`` s or choosers, from a ``list`` or ``tuple``, under a single ``heading`` string.

    .. attribute:: MultiFieldPanel.children

        A ``list`` or ``tuple`` of child panels

    .. attribute:: MultiFieldPanel.heading

        A heading for the fields

InlinePanel
-----------

.. class:: InlinePanel(relation_name, panels=None, classname=None, label='', help_text='')

    This panel allows for the creation of a "cluster" of related objects over a join to a separate model, such as a list of related links or slides to an image carousel.

    This is a very powerful, but tricky feature which will take some space to cover, so we'll skip over it for now. For a full explanation on the usage of ``InlinePanel``, see :ref:`inline_panels`.

FieldRowPanel
-------------

.. class:: FieldRowPanel(children, classname=None)

    This panel creates a columnar layout in the editing interface, where each of the child Panels appears alongside each other rather than below.

    Use of FieldRowPanel particularly helps reduce the "snow-blindness" effect of seeing so many fields on the page, for complex models. It also improves the perceived association between fields of a similar nature. For example if you created a model representing an "Event" which had a starting date and ending date, it may be intuitive to find the start and end date on the same "row".

    FieldRowPanel should be used in combination with ``col*`` classnames added to each of the child Panels of the FieldRowPanel. The Wagtail editing interface is layed out using a grid system, in which the maximum width of the editor is 12 columns wide. Classes ``col1``-``col12`` can be applied to each child of a FieldRowPanel. The class ``col3`` will ensure that field appears 3 columns wide or a quarter the width. ``col4`` would cause the field to be 4 columns wide, or a third the width.

    .. attribute:: FieldRowPanel.children

        A ``list`` or ``tuple`` of child panels to display on the row

    .. attribute:: FieldRowPanel.classname

        A class to apply to the FieldRowPanel as a whole

PageChooserPanel
----------------

.. class:: PageChooserPanel(field_name, model=None)

    You can explicitly link ``Page``-derived models together using the ``Page`` model and ``PageChooserPanel``.

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

    ``PageChooserPanel`` takes two arguments: a field name and an optional page type. Specifying a page type (in the form of an ``"appname.modelname"`` string) will filter the chooser to display only pages of that type.

ImageChooserPanel
-----------------

.. class:: ImageChooserPanel(field_name)

    One of the features of Wagtail is a unified image library, which you can access in your models through the ``Image`` model and the ``ImageChooserPanel`` chooser. Here's how:

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

    Django's default behavior is to "cascade" deletions through a ForeignKey relationship, which is probably not what you want happening. This is why the ``null``, ``blank``, and ``on_delete`` parameters should be set to allow for an empty field. (See `Django model field reference (on_delete)`_ ). ``ImageChooserPanel`` takes only one argument: the name of the field.

    .. _Django model field reference (on_delete): https://docs.djangoproject.com/en/dev/ref/models/fields/#django.db.models.ForeignKey.on_delete

    Displaying ``Image`` objects in a template requires the use of a template tag. See :ref:`image_tag`.

DocumentChooserPanel
--------------------

.. class:: DocumentChooserPanel(field_name)

    For files in other formats, Wagtail provides a generic file store through the ``Document`` model:

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

.. class:: SnippetChooserPanel(field_name, model)

    Snippets are vanilla Django models you create yourself without a Wagtail-provided base class. So using them as a field in a page requires specifying your own ``appname.modelname``. A chooser, ``SnippetChooserPanel``, is provided which takes the field name and snippet class.

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
              SnippetChooserPanel('advert', Advert),
          ]

    See :ref:`snippets` for more information.

Built-in Fields and Choosers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Django's field types are automatically recognized and provided with an appropriate widget for input. Just define that field the normal Django way and pass the field name into ``FieldPanel()`` when defining your panels. Wagtail will take care of the rest.

Here are some Wagtail-specific types that you might include as fields in your models.


Rich Text (HTML)
----------------

Wagtail provides a general-purpose WYSIWYG editor for creating rich text content (HTML) and embedding media such as images, video, and documents. To include this in your models, use the ``RichTextField()`` function when defining a model field:

.. code-block:: python

    from wagtail.wagtailcore.fields import RichTextField
    from wagtail.wagtailadmin.edit_handlers import FieldPanel


    class BookPage(Page):
        book_text = RichTextField()

        content_panels = Page.content_panels + [
            FieldPanel('body', classname="full"),
        ]

``RichTextField`` inherits from Django's basic ``TextField`` field, so you can pass any field parameters into ``RichTextField`` as if using a normal Django field. This field does not need a special panel and can be defined with ``FieldPanel``.

However, template output from ``RichTextField`` is special and need to be filtered to preserve embedded content. See :ref:`rich-text-filter`.

If you're interested in extending the capabilities of the Wagtail WYSIWYG editor (hallo.js), See :ref:`extending_wysiwyg`.


Field Customization
~~~~~~~~~~~~~~~~~~~

By adding CSS classnames to your panel definitions or adding extra parameters to your field definitions, you can control much of how your fields will display in the Wagtail page editing interface. Wagtail's page editing interface takes much of its behavior from Django's admin, so you may find many options for customization covered there. (See `Django model field reference`_ ).

.. _Django model field reference: https://docs.djangoproject.com/en/dev/ref/models/fields/


Full-Width Input
----------------

Use ``classname="full"`` to make a field (input element) stretch the full width of the Wagtail page editor. This will not work if the field is encapsulated in a ``MultiFieldPanel``, which places its child fields into a formset.


Titles
------

Use ``classname="title"`` to make Page's built-in title field stand out with more vertical padding.


Required Fields
---------------

To make input or chooser selection manditory for a field, add ``blank=False`` to its model definition. (See `Django model field reference (blank)`_ ).

.. _Django model field reference (blank): https://docs.djangoproject.com/en/dev/ref/models/fields/#django.db.models.Field.blank


Hiding Fields
-------------

Without a panel definition, a default form field (without label) will be used to represent your fields. If you intend to hide a field on the Wagtail page editor, define the field with ``editable=False`` (See `Django model field reference (editable)`_ ).

.. _Django model field reference (editable): https://docs.djangoproject.com/en/dev/ref/models/fields/#editable


MultiFieldPanel
~~~~~~~~~~~~~~~

The ``MultiFieldPanel`` groups a list of child fields into a fieldset, which can also be collapsed into a heading bar to save space.

.. code-block:: python

    BOOK_FIELD_COLLECTION = [
        ImageChooserPanel('cover'),
        DocumentChooserPanel('book_file'),
        PageChooserPanel('publisher'),
    ]

    BookPage.content_panels = [
        MultiFieldPanel(
            BOOK_FIELD_COLLECTION,
            heading="Collection of Book Fields",
            classname="collapsible collapsed"
        ),
    ]

By default, ``MultiFieldPanel`` s are expanded and not collapsible. Adding the classname ``collapsible`` will enable the collapse control. Adding both ``collapsible`` and ``collapsed`` to the classname parameter will load the editor page with the ``MultiFieldPanel`` collapsed under its heading.


.. _inline_panels:

Inline Panels and Model Clusters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``django-modelcluster`` module allows for streamlined relation of extra models to a Wagtail page. For instance, you can create objects related through a ``ForeignKey`` relationship on the fly and save them to a draft revision of a ``Page`` object. Normally, your related objects "cluster" would need to be created beforehand (or asynchronously) before linking them to a Page.

Let's look at the example of adding related links to a ``Page``-derived model. We want to be able to add as many as we like, assign an order, and do all of this without leaving the page editing screen.

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

The ``RelatedLink`` class is a vanilla Django abstract model. The ``BookPageRelatedLinks`` model extends it with capability for being ordered in the Wagtail interface via the ``Orderable`` class as well as adding a ``page`` property which links the model to the ``BookPage`` model we're adding the related links objects to. Finally, in the panel definitions for ``BookPage``, we'll add an ``InlinePanel`` to provide an interface for it all. Let's look again at the parameters that ``InlinePanel`` accepts:

.. code-block:: python

    InlinePanel( relation_name, panels=None, label='', help_text='' )

The ``relation_name`` is the ``related_name`` label given to the cluster's ``ParentalKey`` relation. You can add the ``panels`` manually or make them part of the cluster model. Finally, ``label`` and ``help_text`` provide a heading and caption, respectively, for the Wagtail editor.

.. versionchanged:: 1.0

    In previous versions, it was necessary to pass the base model as the first parameter to ``InlinePanel``; this is no longer required.

For another example of using model clusters, see :ref:`tagging`

For more on ``django-modelcluster``, visit `the django-modelcluster github project page`_.

.. _the django-modelcluster github project page: https://github.com/torchbox/django-modelcluster


.. _customising_the_tabbed_interface:

Customising the tabbed interface
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. versionadded:: 1.0

As standard, Wagtail organises panels into three tabs: 'Content', 'Promote' and 'Settings'. Depending on the requirements of your site, you may wish to customise this for specific page types - for example, adding an additional tab for sidebar content. This can be done by specifying an ``edit_handler`` property on the page model. For example:

.. code-block:: python

    from wagtail.wagtailadmin.edit_handlers import TabbedInterface, ObjectList

    class BlogPage(Page):
        # field definitions omitted

        content_panels = [
            FieldPanel('title', classname="full title"),
            FieldPanel('date'),
            FieldPanel('body', classname="full"),
        ]
        sidebar_content_panels = [
            SnippetChooserPanel('advert', Advert),
            InlinePanel('related_links', label="Related links"),
        ]

        edit_handler = TabbedInterface([
            ObjectList(content_panels, heading='Content'),
            ObjectList(sidebar_content_panels, heading='Sidebar content'),
            ObjectList(Page.promote_panels, heading='Promote'),
            ObjectList(Page.settings_panels, heading='Settings', classname="settings"),
        ])


.. _extending_wysiwyg:

Extending the WYSIWYG Editor (hallo.js)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To inject JavaScript into the Wagtail page editor, see the :ref:`insert_editor_js <insert_editor_js>` hook. Once you have the hook in place and your hallo.js plugin loads into the Wagtail page editor, use the following Javascript to register the plugin with hallo.js.

.. code-block:: javascript

    registerHalloPlugin(name, opts);

hallo.js plugin names are prefixed with the ``"IKS."`` namespace, but the ``name`` you pass into ``registerHalloPlugin()`` should be without the prefix. ``opts`` is an object passed into the plugin.

For information on developing custom hallo.js plugins, see the project's page: https://github.com/bergie/hallo

Image Formats in the Rich Text Editor
-------------------------------------

On loading, Wagtail will search for any app with the file ``image_formats.py`` and execute the contents. This provides a way to customize the formatting options shown to the editor when inserting images in the ``RichTextField`` editor.

As an example, add a "thumbnail" format:

.. code-block:: python

    # image_formats.py
    from wagtail.wagtailimages.formats import Format, register_image_format

    register_image_format(Format('thumbnail', 'Thumbnail', 'richtext-image thumbnail', 'max-120x120'))


To begin, import the the ``Format`` class, ``register_image_format`` function, and optionally ``unregister_image_format`` function. To register a new ``Format``, call the ``register_image_format`` with the ``Format`` object as the argument. The ``Format`` takes the following init arguments:

``name``
  The unique key used to identify the format. To unregister this format, call ``unregister_image_format`` with this string as the only argument.

``label``
  The label used in the chooser form when inserting the image into the ``RichTextField``.

``classnames``
  The string to assign to the ``class`` attribute of the generated ``<img>`` tag.

``filter_spec``
  The string specification to create the image rendition. For more, see the :ref:`image_tag`.


To unregister, call ``unregister_image_format`` with the string of the ``name`` of the ``Format`` as the only argument.
