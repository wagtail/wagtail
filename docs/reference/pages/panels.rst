.. _editing-api:

Panel types
===========

Built-in Fields and Choosers
----------------------------

Django's field types are automatically recognised and provided with an appropriate widget for input. Just define that field the normal Django way and pass the field name into :class:`~wagtail.admin.edit_handlers.FieldPanel` when defining your panels. Wagtail will take care of the rest.

Here are some Wagtail-specific types that you might include as fields in your models.

.. module:: wagtail.admin.edit_handlers

FieldPanel
~~~~~~~~~~

.. class:: FieldPanel(field_name, classname=None, widget=None, heading='', disable_comments=False)

    This is the panel used for basic Django field types.

    .. attribute:: FieldPanel.field_name

        This is the name of the class property used in your model definition.

    .. attribute:: FieldPanel.classname

        This is a string of optional CSS classes given to the panel which are used in formatting and scripted interactivity. By default, panels are formatted as inset fields.

        The CSS class ``full`` can be used to format the panel so it covers the full width of the Wagtail page editor.

        The CSS class ``title`` can be used to give the field a larger text size, suitable for representing page titles and section headings.

    .. attribute:: FieldPanel.widget (optional)

        This parameter allows you to specify a :doc:`Django form widget <django:ref/forms/widgets>` to use instead of the default widget for this field type.

    .. attribute:: FieldPanel.heading (optional)

        This allows you to override the heading for the panel, which will otherwise be set automatically using the form field's label (taken in turn from a model field's ``verbose_name``).

    .. attribute:: FieldPanel.disable_comments (optional)

        This allows you to prevent a field level comment button showing for this panel if set to ``True`` (see :ref:`commenting`).

StreamFieldPanel
~~~~~~~~~~~~~~~~

.. class:: StreamFieldPanel(field_name, classname=None, widget=None)

    This is the panel used for Wagtail's StreamField type (see :ref:`streamfield`).

    .. attribute:: FieldPanel.field_name

        This is the name of the class property used in your model definition.

    .. attribute:: FieldPanel.classname (optional)

        This is a string of optional CSS classes given to the panel which are used in formatting and scripted interactivity. By default, panels are formatted as inset fields.

        The CSS class ``full`` can be used to format the panel so it covers the full width of the Wagtail page editor.

MultiFieldPanel
~~~~~~~~~~~~~~~

.. class:: MultiFieldPanel(children, heading="", classname=None)

    This panel condenses several :class:`~wagtail.admin.edit_handlers.FieldPanel` s or choosers, from a ``list`` or ``tuple``, under a single ``heading`` string.

    .. attribute:: MultiFieldPanel.children

        A ``list`` or ``tuple`` of child panels

    .. attribute:: MultiFieldPanel.heading

        A heading for the fields


InlinePanel
~~~~~~~~~~~

.. class:: InlinePanel(relation_name, panels=None, classname='', heading='', label='', help_text='', min_num=None, max_num=None)

    This panel allows for the creation of a "cluster" of related objects over a join to a separate model, such as a list of related links or slides to an image carousel.

    This is a powerful but complex feature which will take some space to cover, so we'll skip over it for now. For a full explanation on the usage of ``InlinePanel``, see :ref:`inline_panels`.

.. topic:: Collapsing InlinePanels to save space

    Note that you can use ``classname="collapsible collapsed"`` to load the panel collapsed under its heading in order to save space in the Wagtail admin.
    See :ref:`collapsible` for more details on ``collapsible`` usage.



FieldRowPanel
~~~~~~~~~~~~~

.. class:: FieldRowPanel(children, classname=None)

    This panel creates a columnar layout in the editing interface, where each of the child Panels appears alongside each other rather than below.

    Use of FieldRowPanel particularly helps reduce the "snow-blindness" effect of seeing so many fields on the page, for complex models. It also improves the perceived association between fields of a similar nature. For example if you created a model representing an "Event" which had a starting date and ending date, it may be intuitive to find the start and end date on the same "row".

    By default, the panel is divided into equal-width columns, but this can be overridden by adding ``col*`` class names to each of the child Panels of the FieldRowPanel. The Wagtail editing interface is laid out using a grid system, in which the maximum width of the editor is 12 columns. Classes ``col1``-``col12`` can be applied to each child of a FieldRowPanel. The class ``col3`` will ensure that field appears 3 columns wide or a quarter the width. ``col4`` would cause the field to be 4 columns wide, or a third the width.

    .. attribute:: FieldRowPanel.children

        A ``list`` or ``tuple`` of child panels to display on the row

    .. attribute:: FieldRowPanel.classname

        A class to apply to the FieldRowPanel as a whole

HelpPanel
~~~~~~~~~

.. class:: HelpPanel(content='', template='wagtailadmin/edit_handlers/help_panel.html', heading='', classname='')

    .. attribute:: HelpPanel.content

        HTML string that gets displayed in the panel.

    .. attribute:: HelpPanel.template

        Path to a template rendering the full panel HTML.

    .. attribute:: HelpPanel.heading

        A heading for the help content.

    .. attribute:: HelpPanel.classname

        String of CSS classes given to the panel which are used in formatting and scripted interactivity.

PageChooserPanel
~~~~~~~~~~~~~~~~

.. class:: PageChooserPanel(field_name, page_type=None, can_choose_root=False)

    You can explicitly link :class:`~wagtail.core.models.Page`-derived models together using the :class:`~wagtail.core.models.Page` model and ``PageChooserPanel``.

    .. code-block:: python

        from wagtail.core.models import Page
        from wagtail.admin.edit_handlers import PageChooserPanel


        class BookPage(Page):
            related_page = models.ForeignKey(
                'wagtailcore.Page',
                null=True,
                blank=True,
                on_delete=models.SET_NULL,
                related_name='+',
            )

            content_panels = Page.content_panels + [
                PageChooserPanel('related_page', 'demo.PublisherPage'),
            ]

    ``PageChooserPanel`` takes one required argument, the field name. Optionally, specifying a page type (in the form of an ``"appname.modelname"`` string) will filter the chooser to display only pages of that type. A list or tuple of page types can also be passed in, to allow choosing a page that matches any of those page types:

    .. code-block:: python

        PageChooserPanel('related_page', ['demo.PublisherPage', 'demo.AuthorPage'])

    Passing ``can_choose_root=True`` will allow the editor to choose the tree root as a page. Normally this would be undesirable, since the tree root is never a usable page, but in some specialised cases it may be appropriate; for example, a page with an automatic "related articles" feed could use a PageChooserPanel to select which subsection articles will be taken from, with the root corresponding to 'everywhere'.


ImageChooserPanel
~~~~~~~~~~~~~~~~~

.. module:: wagtail.images.edit_handlers

.. class:: ImageChooserPanel(field_name)

    Wagtail includes a unified image library, which you can access in your models through the :class:`~wagtail.images.models.Image` model and the ``ImageChooserPanel`` chooser. Here's how:

    .. code-block:: python

      from wagtail.images.models import Image
      from wagtail.images.edit_handlers import ImageChooserPanel


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

    Django's default behaviour is to "cascade" deletions through a ForeignKey relationship, which may not be what you want. This is why the :attr:`~django.db.models.Field.null`, :attr:`~django.db.models.Field.blank`, and :attr:`~django.db.models.ForeignKey.on_delete` parameters should be set to allow for an empty field. ``ImageChooserPanel`` takes only one argument: the name of the field.

    Displaying ``Image`` objects in a template requires the use of a template tag. See :ref:`image_tag`.

FormSubmissionsPanel
~~~~~~~~~~~~~~~~~~~~

.. module:: wagtail.contrib.forms.edit_handlers

.. class:: FormSubmissionsPanel

    This panel adds a single, read-only section in the edit interface for pages implementing the :class:`~wagtail.contrib.forms.models.AbstractForm` model.
    It includes the number of total submissions for the given form and also a link to the listing of submissions.

    .. code-block:: python

        from wagtail.contrib.forms.models import AbstractForm
        from wagtail.contrib.forms.edit_handlers import FormSubmissionsPanel

        class ContactFormPage(AbstractForm):
            content_panels = [
                FormSubmissionsPanel(),
            ]

DocumentChooserPanel
~~~~~~~~~~~~~~~~~~~~

.. module:: wagtail.documents.edit_handlers

.. class:: DocumentChooserPanel(field_name)

    For files in other formats, Wagtail provides a generic file store through the :class:`~wagtail.documents.models.Document` model:

    .. code-block:: python

      from wagtail.documents.models import Document
      from wagtail.documents.edit_handlers import DocumentChooserPanel


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
~~~~~~~~~~~~~~~~~~~

.. module:: wagtail.snippets.edit_handlers

.. class:: SnippetChooserPanel(field_name, snippet_type=None)

    Snippets are vanilla Django models you create yourself without a Wagtail-provided base class. A chooser, ``SnippetChooserPanel``, is provided which takes the field name as an argument.

    .. code-block:: python

      from wagtail.snippets.edit_handlers import SnippetChooserPanel

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

Field Customisation
-------------------

By adding CSS classes to your panel definitions or adding extra parameters to your field definitions, you can control much of how your fields will display in the Wagtail page editing interface. Wagtail's page editing interface takes much of its behaviour from Django's admin, so you may find many options for customisation covered there. (See :doc:`Django model field reference <ref/models/fields>`).


Full-Width Input
~~~~~~~~~~~~~~~~

Use ``classname="full"`` to make a field (input element) stretch the full width of the Wagtail page editor. This will not work if the field is encapsulated in a :class:`~wagtail.admin.edit_handlers.MultiFieldPanel`, which places its child fields into a formset.


Titles
~~~~~~

Use ``classname="title"`` to make Page's built-in title field stand out with more vertical padding.


.. _collapsible:

Collapsible
~~~~~~~~~~~

By default, panels are expanded and not collapsible.
Use ``classname="collapsible"`` to enable the collapse control.
Use ``classname="collapsible collapsed"`` will load the editor page with the panel collapsed under its heading.

You must define a ``heading`` when using ``collapsible`` with ``MultiFieldPanel``.
You must define a ``heading`` or ``label`` when using ``collapsible`` with ``InlinePanel``.


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


Placeholder Text
~~~~~~~~~~~~~~~~

By default, Wagtail uses the field's label as placeholder text. To change it, pass to the FieldPanel a widget with a placeholder attribute set to your desired text. You can select widgets from :doc:`Django's form widgets <django:ref/forms/widgets>`, or any of the Wagtail's widgets found in ``wagtail.admin.widgets``.

For example, to customize placeholders for a Book model exposed via ModelAdmin:

.. code-block:: python

    # models.py
    from django import forms            # the default Django widgets live here
    from wagtail.admin import widgets   # to use Wagtail's special datetime widget

    class Book(models.Model):
        title = models.CharField(max_length=256)
        release_date = models.DateField()
        price = models.DecimalField(max_digits=5, decimal_places=2)

        # you can create them separately
        title_widget = forms.TextInput(
            attrs = {
                'placeholder': 'Enter Full Title'
            }
        )
        # using the correct widget for your field type and desired effect
        date_widget = widgets.AdminDateInput(
            attrs = {
                'placeholder': 'dd-mm-yyyy'
            }
        )

        panels = [
            FieldPanel('title', widget=title_widget), # then add them as a variable
            FieldPanel('release_date', widget=date_widget),
            FieldPanel('price', widget=forms.NumberInput(attrs={'placeholder': 'Retail price on release'})) # or directly inline
        ]

Required Fields
~~~~~~~~~~~~~~~

To make input or chooser selection mandatory for a field, add :attr:`blank=False <django.db.models.Field.blank>` to its model definition.

Hiding Fields
~~~~~~~~~~~~~

Without a panel definition, a default form field (without label) will be used to represent your fields. If you intend to hide a field on the Wagtail page editor, define the field with :attr:`editable=False <django.db.models.Field.editable>`.

.. _inline_panels:

Inline Panels and Model Clusters
--------------------------------

The ``django-modelcluster`` module allows for streamlined relation of extra models to a Wagtail page via a ForeignKey-like relationship called ``ParentalKey``.  Normally, your related objects "cluster" would need to be created beforehand (or asynchronously) before being linked to a Page; however, objects related to a Wagtail page via ``ParentalKey`` can be created on-the-fly and saved to a draft revision of a ``Page`` object.

Let's look at the example of adding related links to a :class:`~wagtail.core.models.Page`-derived model. We want to be able to add as many as we like, assign an order, and do all of this without leaving the page editing screen.

.. code-block:: python

  from wagtail.core.models import Orderable, Page
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
      page = ParentalKey('demo.BookPage', on_delete=models.CASCADE, related_name='related_links')

  class BookPage(Page):
    # ...

    content_panels = Page.content_panels + [
      InlinePanel('related_links', label="Related Links"),
    ]

The ``RelatedLink`` class is a vanilla Django abstract model. The ``BookPageRelatedLinks`` model extends it with capability for being ordered in the Wagtail interface via the ``Orderable`` class as well as adding a ``page`` property which links the model to the ``BookPage`` model we're adding the related links objects to. Finally, in the panel definitions for ``BookPage``, we'll add an :class:`~wagtail.admin.edit_handlers.InlinePanel` to provide an interface for it all. Let's look again at the parameters that :class:`~wagtail.admin.edit_handlers.InlinePanel` accepts:

.. code-block:: python

    InlinePanel( relation_name, panels=None, heading='', label='', help_text='', min_num=None, max_num=None )

The ``relation_name`` is the ``related_name`` label given to the cluster's ``ParentalKey`` relation. You can add the ``panels`` manually or make them part of the cluster model. ``heading`` and ``help_text`` provide a heading and caption, respectively, for the Wagtail editor. ``label`` sets the text on the add button, and is used as the heading when ``heading`` is not present. Finally, ``min_num`` and ``max_num`` allow you to set the minimum/maximum number of forms that the user must submit.

For another example of using model clusters, see :ref:`tagging`

For more on ``django-modelcluster``, visit `the django-modelcluster github project page`_.

.. _the django-modelcluster github project page: https://github.com/torchbox/django-modelcluster
