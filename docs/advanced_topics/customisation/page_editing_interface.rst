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

However, template output from :class:`~wagtail.core.fields.RichTextField` is special and need to be filtered to preserve embedded content. See :ref:`rich-text-filter`.


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


Adding new features to this list is generally a two step process:

 * Create a plugin that extends the editor with a new toolbar button or other control(s) to manage the rich text formatting of the feature.
 * Create conversion or whitelist rules to define how content from the editor should be filtered or transformed before storage, and front-end HTML output.

Both of these steps are performed through the ``register_rich_text_features`` hook (see :ref:`admin_hooks`). The hook function is triggered on startup, and receives a *feature registry* object as its argument; this object keeps track of the behaviours associated with each feature identifier.

This process for adding new features is described in the following sections.


.. _extending_wysiwyg:

Extending the WYSIWYG Editor (``Draftail``)
+++++++++++++++++++++++++++++++++++++++++++

Wagtail's rich text editor is built on `Draftail <https://github.com/springload/draftail>`_, and its functionality can be extended through plugins.

Extending the WYSIWYG Editor (``hallo.js``)
+++++++++++++++++++++++++++++++++++++++++++

.. warning::
  **As of Wagtail 2.0, the hallo.js editor is deprecated.** We have no intentions to remove it from Wagtail as of yet, but it will no longer receive bug fixes. Please be aware of the `known hallo.js issues <https://github.com/wagtail/wagtail/issues?q=is%3Aissue+is%3Aclosed+hallo+label%3A%22component%3ARich+text%22+label%3Atype%3ABug+label%3A%22status%3AWont+Fix%22>`_ should you want to keep using it.

  To use hallo.js on Wagtail 2.x, add the following to your settings:

  .. code-block:: python

    WAGTAILADMIN_RICH_TEXT_EDITORS = {
        'default': {
            'WIDGET': 'wagtail.admin.rich_text.HalloRichTextArea'
        }
    }

The legacy hallo.js editor’s functionality can be extended through plugins. For information on developing custom ``hallo.js`` plugins, see the project's page: https://github.com/bergie/hallo

Once the plugin has been created, it should be registered through the feature registry's ``register_editor_plugin(editor, feature_name, plugin)`` method. For a ``hallo.js`` plugin, the ``editor`` parameter should always be ``'hallo'``.

A plugin ``halloblockquote``, implemented in ``myapp/js/hallo-blockquote.js``, that adds support for the ``<blockquote>`` tag, would be registered under the feature name ``block-quote`` as follows:

.. code-block:: python

    from wagtail.admin.rich_text import HalloPlugin
    from wagtail.core import hooks

    @hooks.register('register_rich_text_features')
    def register_embed_feature(features):
        features.register_editor_plugin(
            'hallo', 'block-quote',
            HalloPlugin(
                name='halloblockquote',
                js=['myapp/js/hallo-blockquote.js'],
            )
        )

The constructor for ``HalloPlugin`` accepts the following keyword arguments:

 * ``name`` - the plugin name as defined in the Javascript code. ``hallo.js`` plugin names are prefixed with the ``"IKS."`` namespace, but the name passed here should be without the prefix.
 * ``options`` - a dictionary (or other JSON-serialisable object) of options to be passed to the Javascript plugin code on initialisation
 * ``js`` - a list of Javascript files to be imported for this plugin, defined in the same way as a `Django form media <https://docs.djangoproject.com/en/1.11/topics/forms/media/>`_ definition
 * ``css`` - a dictionary of CSS files to be imported for this plugin, defined in the same way as a `Django form media <https://docs.djangoproject.com/en/1.11/topics/forms/media/>`_ definition
 * ``order`` - an index number (default 100) specifying the order in which plugins should be listed, which in turn determines the order buttons will appear in the toolbar

To have a feature active by default (i.e. on ``RichTextFields`` that do not define an explicit ``features`` list), add it to the ``default_features`` list on the ``features`` object:

.. code-block:: python

    from django.utils.html import format_html

    @hooks.register('register_rich_text_features')
    def register_blockquote_feature(features):
        features.register_editor_plugin(
            'hallo', 'block-quote',
            # ...
        )
        features.default_features.append('block-quote')


.. _whitelisting_rich_text_elements:

Whitelisting rich text elements (``hallo.js``)
++++++++++++++++++++++++++++++++++++++++++++++

After extending the editor to support a new HTML element, you'll need to add it to the whitelist of permitted elements - Wagtail's standard behaviour is to strip out unrecognised elements, to prevent editors from inserting styles and scripts (either deliberately, or inadvertently through copy-and-paste) that the developer didn't account for.

Elements can be added to the whitelist through the feature registry's ``register_converter_rule(converter, feature_name, ruleset)`` method. When the ``hallo.js`` editor is in use, the ``converter`` parameter should always be ``'editorhtml'``.

The following code will add the ``<blockquote>`` element to the whitelist whenever the ``block-quote`` feature is active:

.. code-block:: python

    from wagtail.admin.rich_text.converters.editor_html import WhitelistRule
    from wagtail.core.whitelist import allow_without_attributes

    @hooks.register('register_rich_text_features')
    def register_blockquote_feature(features):
        features.register_converter_rule('editorhtml', 'block-quote', [
            WhitelistRule('blockquote', allow_without_attributes),
        ])

``WhitelistRule`` is passed the element name, and a callable which will perform some kind of manipulation of the element whenever it is encountered. This callable receives the element as a `BeautifulSoup <http://www.crummy.com/software/BeautifulSoup/bs4/doc/>`_ Tag object.

The ``wagtail.core.whitelist`` module provides a few helper functions to assist in defining these handlers: ``allow_without_attributes``, a handler which preserves the element but strips out all of its attributes, and ``attribute_rule`` which accepts a dict specifying how to handle each attribute, and returns a handler function. This dict will map attribute names to either True (indicating that the attribute should be kept), False (indicating that it should be dropped), or a callable (which takes the initial attribute value and returns either a final value for the attribute, or None to drop the attribute).


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
