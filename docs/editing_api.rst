
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

  ``MultiFieldPanel( panel_list, heading )``
    This panel condenses several ``FieldPanel`` s or choosers, from a list or tuple, under a single ``heading`` string.

  ``InlinePanel( base_model, relation_name, panels=None, label='', help_text='' )``
    This panel allows for the creation of a "cluster" of related objects over a join to a separate model, such as a list of related links or slides to an image carousel. This is a very powerful, but tricky feature which will take some space to cover, so we'll skip over it for now. For a full explaination on the usage of ``InlinePanel``, see :ref:`inline_panels`.

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





Built-in Fields and Choosers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Django's field types are automatically recognized and provided with an appropriate widget for input. Just define that field the normal Django way and pass the field name into ``FieldPanel()`` when defining your panels. Wagtail will take care of the rest.

Here are some Wagtail-specific types that you might include as fields in your models.


Rich Text (HTML)
----------------

Wagtail provides a general-purpose WYSIWYG editor for creating rich text content (HTML) and embedding media such as images, video, and documents. To include this in your models, use the ``RichTextField()`` function when defining a model field:

.. code-block:: python

  from wagtail.wagtailcore.fields import RichTextField
  ...
  class BookPage(Page):
    book_text = RichTextField()



If you're interested in extending the capabilities of the Wagtail editor, See :ref:`extending_wysiwyg`.


Images
------

.. code-block:: python

  from wagtail.wagtailimages.models import Image

  feed_image = models.ForeignKey(
    'wagtailimages.Image',
    null=True,
    blank=True,
    on_delete=models.SET_NULL,
    related_name='+'
  )


Documents
---------

.. code-block:: python

  from wagtail.wagtaildocs.models import Document

  link_document = models.ForeignKey(
    'wagtaildocs.Document',
    null=True,
    blank=True,
    related_name='+'
  )


Pages and Page-derived Models
-----------------------------

.. code-block:: python

  from wagtail.wagtailcore.models import Page

  page = models.ForeignKey(
    'wagtailcore.Page',
    related_name='+',
    null=True,
    blank=True
  )

Can also use more specific models.


Snippets (and Basic Django Models?)
--------

Snippets are not not subclasses, so you must include the model class directly. A chooser is provided which takes the snippet class.

.. code-block:: python

  advert = models.ForeignKey(
    'demo.Advert',
    related_name='+'
  )














PageChooserPanel
~~~~~~~~~~~~~~~~

ImageChooserPanel
~~~~~~~~~~~~~~~~~

DocumentChooserPanel
~~~~~~~~~~~~~~~~~~~~

SnippetChooserPanel
~~~~~~~~~~~~~~~~~~~


.. _inline_panels:

Inline Panels and Model Clusters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``django-modelcluster`` module allows for streamlined relation of extra models to a Wagtail page.


.. _extending_wysiwyg:

Extending the WYSIWYG Editor (hallo.js)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~



Edit Handler API
~~~~~~~~~~~~~~~~



