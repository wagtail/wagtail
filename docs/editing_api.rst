
Editing API
===========

.. note::
    This documentation is currently being written.
    

Wagtail provides a highly-customizable editing interface consisting of several components:

  * **Fields** — built-in content types to augment the basic types provided by Django.
  * **Panels** — the basic editing blocks for fields, groups of fields, and related object clusters
  * **Choosers** — interfaces for finding related objects in a ForeignKey relationship

Configuring your models to use these components will shape the Wagtail editor to your needs. Wagtail also provides an API for injecting custom CSS and Javascript for further customization, including extending the hallo.js rich text editor.

There is also an Edit Handler API for creating your own Wagtail editor components.


Defining Panels
~~~~~~~~~~~~~~~

A "panel" is the basic editing block in Wagtail. Wagtail will automatically pick the appropriate editing widget for most Django field types, you just need to add a panel for each field you want to show in the Wagtail page editor, in the order you want them to appear.

There are three types of panels:

  ``FieldPanel( field_name, classname=None )``
    This is the panel used for basic Django field types. ``field_name`` is the name of the class property used in your model definition. ``classname`` is a string of optional CSS classes given to the panel which are used in formatting and scripted interactivity. By default, panels are formatted as inset fields. The CSS class ``full`` can be used to format the panel so it covers the full width of the Wagtail page editor. The CSS class ``title`` can be used to mark a field as the source for auto-generated slug strings.

  ``MultiFieldPanel( children, heading="", classname=None )``
    This panel condenses several ``FieldPanel`` s or choosers, from a list or tuple, under a single ``heading`` string.

  ``InlinePanel( base_model, relation_name, panels=None, label='', help_text='' )``
    This panel allows for the creation of a "cluster" of related objects over a join to a separate model, such as a list of related links or slides to an image carousel. This is a very powerful, but tricky feature which will take some space to cover, so we'll skip over it for now. For a full explanation on the usage of ``InlinePanel``, see :ref:`inline_panels`.

Wagtail provides a tabbed interface to help organize panels. ``content_panels`` is the main tab, used for the meat of your model content. The other, ``promote_panels``, is suggested for organizing metadata about the content, such as SEO information and other machine-readable information. Since you're writing the panel definitions, you can organize them however you want.

Let's look at an example of a panel definition:

.. code-block:: python

  COMMON_PANELS = (
    FieldPanel('slug'),
    FieldPanel('seo_title'),
    FieldPanel('show_in_menus'),
    FieldPanel('search_description'),
  )

  ...

  class ExamplePage( Page ):
    # field definitions omitted
    ...

  ExamplePage.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('body', classname="full"),
    FieldPanel('date'),
    ImageChooserPanel('splash_image'),
    DocumentChooserPanel('free_download'),
    PageChooserPanel('related_page'),
  ]

  ExamplePage.promote_panels = [
    MultiFieldPanel(COMMON_PANELS, "Common page configuration"),
  ]

After the ``Page``-derived class definition, just add lists of panel definitions to order and organize the Wagtail page editing interface for your model.


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
  # ...
  class BookPage(Page):
    book_text = RichTextField()

  BookPage.content_panels = [
    FieldPanel('body', classname="full"),
    # ...
  ]

``RichTextField`` inherits from Django's basic ``TextField`` field, so you can pass any field parameters into ``RichTextField`` as if using a normal Django field. This field does not need a special panel and can be defined with ``FieldPanel``.

However, template output from ``RichTextField`` is special and need to be filtered to preserve embedded content. See :ref:`rich-text-filter`.

If you're interested in extending the capabilities of the Wagtail WYSIWYG editor (hallo.js), See :ref:`extending_wysiwyg`.


Images
------

One of the features of Wagtail is a unified image library, which you can access in your models through the ``Image`` model and the ``ImageChooserPanel`` chooser. Here's how:

.. code-block:: python

  from wagtail.wagtailimages.models import Image
  from wagtail.wagtailimages.edit_handlers import ImageChooserPanel
  # ...
  class BookPage(Page):
    cover = models.ForeignKey(
      'wagtailimages.Image',
      null=True,
      blank=True,
      on_delete=models.SET_NULL,
      related_name='+'
    )
    
  BookPage.content_panels = [
    ImageChooserPanel('cover'),
    # ...
  ]

Django's default behavior is to "cascade" deletions through a ForeignKey relationship, which is probably not what you want happening. This is why the ``null``, ``blank``, and ``on_delete`` parameters should be set to allow for an empty field. (See `Django model field reference (on_delete)`_ ). ``ImageChooserPanel`` takes only one argument: the name of the field.

.. _Django model field reference (on_delete): https://docs.djangoproject.com/en/dev/ref/models/fields/#django.db.models.ForeignKey.on_delete

Displaying ``Image`` objects in a template requires the use of a template tag. See :ref:`image_tag`.


Documents
---------

For files in other formats, Wagtail provides a generic file store through the ``Document`` model:

.. code-block:: python

  from wagtail.wagtaildocs.models import Document
  from wagtail.wagtaildocs.edit_handlers import DocumentChooserPanel
  # ...
  class BookPage(Page):
    book_file = models.ForeignKey(
      'wagtaildocs.Document',
      null=True,
      blank=True,
      on_delete=models.SET_NULL,
      related_name='+'
    )

  BookPage.content_panels = [
    DocumentChooserPanel('book_file'),
    # ...
  ]

As with images, Wagtail documents should also have the appropriate extra parameters to prevent cascade deletions across a ForeignKey relationship. ``DocumentChooserPanel`` takes only one argument: the name of the field.

Documents can be used directly in templates without tags or filters. Its properties are:

.. glossary::

  ``title``
    The title of the document.

  ``url``
    URL to the file.

  ``created_at``
    The date and time the document was created (DateTime).

  ``filename``
    The filename of the file.

  ``file_extension``
    The extension of the file.

  ``tags``
    A ``TaggableManager`` which keeps track of tags associated with the document (uses the ``django-taggit`` module).


Pages and Page-derived Models
-----------------------------

You can explicitly link ``Page``-derived models together using the ``Page`` model and ``PageChooserPanel``.

.. code-block:: python

  from wagtail.wagtailcore.models import Page
  from wagtail.wagtailadmin.edit_handlers import PageChooserPanel
  # ...
  class BookPage(Page):
    publisher = models.ForeignKey(
      'wagtailcore.Page',
      null=True,
      blank=True,
      on_delete=models.SET_NULL,
      related_name='+',
    )

  BookPage.content_panels = [
    PageChooserPanel('related_page', 'demo.PublisherPage'),
    # ...
  ]

``PageChooserPanel`` takes two arguments: a field name and an optional page type. Specifying a page type (in the form of an ``"appname.modelname"`` string) will filter the chooser to display only pages of that type.


Snippets
--------

Snippets are not subclasses, so you must include the model class directly. A chooser is provided which takes the field name snippet class.

.. code-block:: python

  from wagtail.wagtailsnippets.edit_handlers import SnippetChooserPanel
  # ...
  class BookPage(Page):
    advert = models.ForeignKey(
      'demo.Advert',
      null=True,
      blank=True,
      on_delete=models.SET_NULL,
      related_name='+'
    )
    
  BookPage.content_panels = [
    SnippetChooserPanel('advert', Advert),
    # ...
  ]

See :ref:`snippets` for more information.


Field Customization
~~~~~~~~~~~~~~~~~~~

By adding CSS classnames to your panel definitions or adding extra parameters to your field definitions, you can control much of how your fields will display in the Wagtail page editing interface. Wagtail's page editing interface takes much of its behavior from Django's admin, so you may find many options for customization covered there. (See `Django model field reference`_ ).

.. _Django model field reference:https://docs.djangoproject.com/en/dev/ref/models/fields/


Full-Width Input
----------------

Use ``classname="full"`` to make a field (input element) stretch the full width of the Wagtail page editor. This will not work if the field is encapsulated in a ``MultiFieldPanel``, which places its child fields into a formset.


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
    # ...
  ]





.. _inline_panels:

Inline Panels and Model Clusters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``django-modelcluster`` module allows for streamlined relation of extra models to a Wagtail page.


.. _extending_wysiwyg:

Extending the WYSIWYG Editor (hallo.js)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Adding hallo.js plugins:
https://github.com/torchbox/wagtail/commit/1ecc215759142e6cafdacb185bbfd3f8e9cd3185


Edit Handler API
~~~~~~~~~~~~~~~~



