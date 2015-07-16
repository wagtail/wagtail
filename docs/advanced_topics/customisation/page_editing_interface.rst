Customising the page editing interface
======================================

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


Rich Text (HTML)
~~~~~~~~~~~~~~~~

Wagtail provides a general-purpose WYSIWYG editor for creating rich text content (HTML) and embedding media such as images, video, and documents. To include this in your models, use the :class:`~wagtail.wagtailcore.fields.RichTextField` function when defining a model field:

.. code-block:: python

    from wagtail.wagtailcore.fields import RichTextField
    from wagtail.wagtailadmin.edit_handlers import FieldPanel


    class BookPage(Page):
        book_text = RichTextField()

        content_panels = Page.content_panels + [
            FieldPanel('body', classname="full"),
        ]

:class:`~wagtail.wagtailcore.fields.RichTextField` inherits from Django's basic ``TextField`` field, so you can pass any field parameters into :class:`~wagtail.wagtailcore.fields.RichTextField` as if using a normal Django field. This field does not need a special panel and can be defined with ``FieldPanel``.

However, template output from :class:`~wagtail.wagtailcore.fields.RichTextField` is special and need to be filtered to preserve embedded content. See :ref:`rich-text-filter`.

If you're interested in extending the capabilities of the Wagtail WYSIWYG editor (``hallo.js``), See :ref:`extending_wysiwyg`.

.. _extending_wysiwyg:

Extending the WYSIWYG Editor (``hallo.js``)
-------------------------------------------

To inject JavaScript into the Wagtail page editor, see the :ref:`insert_editor_js <insert_editor_js>` hook. Once you have the hook in place and your ``hallo.js`` plugin loads into the Wagtail page editor, use the following JavaScript to register the plugin with ``hallo.js``.

.. code-block:: javascript

    registerHalloPlugin(name, opts);

``hallo.js`` plugin names are prefixed with the ``"IKS."`` namespace, but the ``name`` you pass into ``registerHalloPlugin()`` should be without the prefix. ``opts`` is an object passed into the plugin.

For information on developing custom ``hallo.js`` plugins, see the project's page: https://github.com/bergie/hallo

Image Formats in the Rich Text Editor
-------------------------------------

On loading, Wagtail will search for any app with the file ``image_formats.py`` and execute the contents. This provides a way to customise the formatting options shown to the editor when inserting images in the :class:`~wagtail.wagtailcore.fields.RichTextField` editor.

As an example, add a "thumbnail" format:

.. code-block:: python

    # image_formats.py
    from wagtail.wagtailimages.formats import Format, register_image_format

    register_image_format(Format('thumbnail', 'Thumbnail', 'richtext-image thumbnail', 'max-120x120'))


To begin, import the the ``Format`` class, ``register_image_format`` function, and optionally ``unregister_image_format`` function. To register a new ``Format``, call the ``register_image_format`` with the ``Format`` object as the argument. The ``Format`` class takes the following constructor arguments:

``name``
  The unique key used to identify the format. To unregister this format, call ``unregister_image_format`` with this string as the only argument.

``label``
  The label used in the chooser form when inserting the image into the :class:`~wagtail.wagtailcore.fields.RichTextField`.

``classnames``
  The string to assign to the ``class`` attribute of the generated ``<img>`` tag.

``filter_spec``
  The string specification to create the image rendition. For more, see the :ref:`image_tag`.


To unregister, call ``unregister_image_format`` with the string of the ``name`` of the ``Format`` as the only argument.
