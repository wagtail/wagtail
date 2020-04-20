Customising the editing interface
=================================

.. _customising_the_tabbed_interface:

Customising the tabbed interface
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

As standard, Wagtail organises panels for pages into three tabs: 'Content', 'Promote' and 'Settings'. For snippets Wagtail puts all panels into one page. Depending on the requirements of your site, you may wish to customise this for specific page types or snippets - for example, adding an additional tab for sidebar content. This can be done by specifying an ``edit_handler`` attribute on the page or snippet model. For example:

.. code-block:: python

    from wagtail.admin.edit_handlers import TabbedInterface, ObjectList

    class BlogPage(Page):
        # field definitions omitted

        content_panels = [
            FieldPanel('title', classname="full title"),
            FieldPanel('date'),
            FieldPanel('body', classname="full"),
        ]
        sidebar_content_panels = [
            SnippetChooserPanel('advert'),
            InlinePanel('related_links', label="Related links"),
        ]

        edit_handler = TabbedInterface([
            ObjectList(content_panels, heading='Content'),
            ObjectList(sidebar_content_panels, heading='Sidebar content'),
            ObjectList(Page.promote_panels, heading='Promote'),
            ObjectList(Page.settings_panels, heading='Settings', classname="settings"),
        ])


.. _rich-text:

Rich Text (HTML)
~~~~~~~~~~~~~~~~

Wagtail provides a general-purpose WYSIWYG editor for creating rich text content (HTML) and embedding media such as images, video, and documents. To include this in your models, use the :class:`~wagtail.core.fields.RichTextField` function when defining a model field:

.. code-block:: python

    from wagtail.core.fields import RichTextField
    from wagtail.admin.edit_handlers import FieldPanel


    class BookPage(Page):
        book_text = RichTextField()

        content_panels = Page.content_panels + [
            FieldPanel('body', classname="full"),
        ]

:class:`~wagtail.core.fields.RichTextField` inherits from Django's basic ``TextField`` field, so you can pass any field parameters into :class:`~wagtail.core.fields.RichTextField` as if using a normal Django field. This field does not need a special panel and can be defined with ``FieldPanel``.

However, template output from :class:`~wagtail.core.fields.RichTextField` is special and needs to be filtered in order to preserve embedded content. See :ref:`rich-text-filter`.


.. _rich_text_features:

Limiting features in a rich text field
--------------------------------------

By default, the rich text editor provides users with a wide variety of options for text formatting and inserting embedded content such as images. However, we may wish to restrict a rich text field to a more limited set of features - for example:

 * The field might be intended for a short text snippet, such as a summary to be pulled out on index pages, where embedded images or videos would be inappropriate;
 * When page content is defined using :ref:`StreamField <streamfield>`, elements such as headings, images and videos are usually given their own block types, alongside a rich text block type used for ordinary paragraph text; in this case, allowing headings and images to also exist within the rich text content is redundant (and liable to result in inconsistent designs).

This can be achieved by passing a ``features`` keyword argument to ``RichTextField``, with a list of identifiers for the features you wish to allow:

.. code-block:: python

    body = RichTextField(features=['h2', 'h3', 'bold', 'italic', 'link'])

The feature identifiers provided on a default Wagtail installation are as follows:

 * ``h1``, ``h2``, ``h3``, ``h4``, ``h5``, ``h6`` - heading elements
 * ``bold``, ``italic`` - bold / italic text
 * ``ol``, ``ul`` - ordered / unordered lists
 * ``hr`` - horizontal rules
 * ``link`` - page, external and email links
 * ``document-link`` - links to documents
 * ``image`` - embedded images
 * ``embed`` - embedded media (see :ref:`embedded_content`)


We have few additional feature identifiers as well. They are not enabled by default, but you can use them in your list of identifers. These are as follows:

* ``code`` - inline code
* ``superscript``, ``subscript``, ``strikethrough`` - text formatting
* ``blockquote`` - blockquote

The process for creating new features is described in the following pages:

* :doc:`./rich_text_internals`
* :doc:`./extending_draftail`
* :doc:`./extending_hallo`

.. _rich_text_image_formats:

Image Formats in the Rich Text Editor
-------------------------------------

On loading, Wagtail will search for any app with the file ``image_formats.py`` and execute the contents. This provides a way to customise the formatting options shown to the editor when inserting images in the :class:`~wagtail.core.fields.RichTextField` editor.

As an example, add a "thumbnail" format:

.. code-block:: python

    # image_formats.py
    from wagtail.images.formats import Format, register_image_format

    register_image_format(Format('thumbnail', 'Thumbnail', 'richtext-image thumbnail', 'max-120x120'))


To begin, import the ``Format`` class, ``register_image_format`` function, and optionally ``unregister_image_format`` function. To register a new ``Format``, call the ``register_image_format`` with the ``Format`` object as the argument. The ``Format`` class takes the following constructor arguments:

``name``
  The unique key used to identify the format. To unregister this format, call ``unregister_image_format`` with this string as the only argument.

``label``
  The label used in the chooser form when inserting the image into the :class:`~wagtail.core.fields.RichTextField`.

``classnames``
  The string to assign to the ``class`` attribute of the generated ``<img>`` tag.

  .. note::
    Any class names you provide must have CSS rules matching them written separately, as part of the front end CSS code. Specifying a ``classnames`` value of ``left`` will only ensure that class is output in the generated markup, it won't cause the image to align itself left.

``filter_spec``
  The string specification to create the image rendition. For more, see the :ref:`image_tag`.


To unregister, call ``unregister_image_format`` with the string of the ``name`` of the ``Format`` as the only argument.

  .. warning::
     Unregistering ``Format`` objects will cause errors viewing or editing pages that reference them.

.. _custom_edit_handler_forms:

Customising generated forms
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. class:: wagtail.admin.forms.WagtailAdminModelForm
.. class:: wagtail.admin.forms.WagtailAdminPageForm

Wagtail automatically generates forms using the panels configured on the model.
By default, this form subclasses :class:`~wagtail.admin.forms.WagtailAdminModelForm`,
or :class:`~wagtail.admin.forms.WagtailAdminPageForm` for pages.
A custom base form class can be configured by setting the :attr:`base_form_class` attribute on any model.
Custom forms for snippets must subclass :class:`~wagtail.admin.forms.WagtailAdminModelForm`,
and custom forms for pages must subclass :class:`~wagtail.admin.forms.WagtailAdminPageForm`.

This can be used to add non-model fields to the form, to automatically generate field content,
or to add custom validation logic for your models:

.. code-block:: python

    from django import forms
    from django.db import models
    import geocoder  # not in Wagtail, for example only - http://geocoder.readthedocs.io/
    from wagtail.admin.edit_handlers import FieldPanel
    from wagtail.admin.forms import WagtailAdminPageForm
    from wagtail.core.models import Page


    class EventPageForm(WagtailAdminPageForm):
        address = forms.CharField()

        def clean(self):
            cleaned_data = super().clean()

            # Make sure that the event starts before it ends
            start_date = cleaned_data['start_date']
            end_date = cleaned_data['end_date']
            if start_date and end_date and start_date > end_date:
                self.add_error('end_date', 'The end date must be after the start date')

            return cleaned_data

        def save(self, commit=True):
            page = super().save(commit=False)

            # Update the duration field from the submitted dates
            page.duration = (page.end_date - page.start_date).days

            # Fetch the location by geocoding the address
            page.location = geocoder.arcgis(self.cleaned_data['address'])

            if commit:
                page.save()
            return page


    class EventPage(Page):
        start_date = models.DateField()
        end_date = models.DateField()
        duration = models.IntegerField()
        location = models.CharField(max_length=255)

        content_panels = [
            FieldPanel('title'),
            FieldPanel('start_date'),
            FieldPanel('end_date'),
            FieldPanel('address'),
        ]
        base_form_class = EventPageForm

Wagtail will generate a new subclass of this form for the model,
adding any fields defined in ``panels`` or ``content_panels``.
Any fields already defined on the model will not be overridden by these automatically added fields,
so the form field for a model field can be overridden by adding it to the custom form.
