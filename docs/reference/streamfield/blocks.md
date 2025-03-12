(streamfield_block_reference)=

# StreamField block reference

This document details the block types provided by Wagtail for use in [StreamField](streamfield_topic), and how they can be combined into new block types.

```{note}
   While block definitions look similar to model fields, they are not the same thing. Blocks are only valid within a StreamField - using them in place of a model field will not work.
```

```{eval-rst}
.. class:: wagtail.fields.StreamField(blocks, blank=False, min_num=None, max_num=None, block_counts=None, collapsed=False)

   A model field for representing long-form content as a sequence of content blocks of various types. See :ref:`streamfield_topic`.

   :param blocks: A list of block types, passed as either a list of ``(name, block_definition)`` tuples or a ``StreamBlock`` instance.
   :param blank: When false (the default), at least one block must be provided for the field to be considered valid.
   :param min_num: Minimum number of sub-blocks that the stream must have.
   :param max_num: Maximum number of sub-blocks that the stream may have.
   :param block_counts: Specifies the minimum and maximum number of each block type, as a dictionary mapping block names to dicts with (optional) ``min_num`` and ``max_num`` fields.
   :param collapsed: When true, all blocks are initially collapsed.
```

```python
body = StreamField([
    ('heading', blocks.CharBlock(form_classname="title")),
    ('paragraph', blocks.RichTextBlock()),
    ('image', ImageBlock()),
], block_counts={
    'heading': {'min_num': 1},
    'image': {'max_num': 5},
})
```

## Block options and methods

All block definitions accept the following optional keyword arguments or `Meta` class attributes:

-   `default`
    -   The default value that a new 'empty' block should receive.
-   `label`
    -   The label to display in the editor interface when referring to this block - defaults to a prettified version of the block name (or, in a context where no name is assigned - such as within a `ListBlock` - the empty string).
-   `icon`
    -   The name of the icon to display for this block type in the editor. For more details, see our [icons overview](icons).
-   `template`
    -   The path to a Django template that will be used to render this block on the front end. See [Template rendering](streamfield_template_rendering)
-   `group`
    -   The group used to categorize this block. Any blocks with the same group name will be shown together in the editor interface with the group name as a heading.

(block_preview_arguments)=

[StreamField blocks can have previews](configuring_block_previews) that will be shown inside the block picker. To accommodate the feature, all block definitions also accept the following options:

-   `preview_value`
    -   The placeholder value that will be used for rendering the preview. See {meth}`~wagtail.blocks.Block.get_preview_value` for more details.
-   `preview_template`
    -   The template that is used to render the preview. See {meth}`~wagtail.blocks.Block.get_preview_template` for more details.
-   `description`
    -   The description of the block to be shown to editors. See {meth}`~wagtail.blocks.Block.get_description` for more details.

All block definitions have the following methods that can be overridden:

```{eval-rst}
.. autoclass:: wagtail.blocks.Block

    .. automethod:: wagtail.blocks.Block.get_context
    .. automethod:: wagtail.blocks.Block.get_template
    .. automethod:: wagtail.blocks.Block.get_preview_value
    .. automethod:: wagtail.blocks.Block.get_preview_context
    .. automethod:: wagtail.blocks.Block.get_preview_template
    .. automethod:: wagtail.blocks.Block.get_description
```

(field_block_types)=

## Field block types

```{eval-rst}
.. autoclass:: wagtail.blocks.FieldBlock
    :show-inheritance:

    The parent class of all StreamField field block types.


.. autoclass:: wagtail.blocks.CharBlock
    :show-inheritance:

    A single-line text input. The following keyword arguments are accepted in addition to the standard ones:

    :param required: If true (the default), the field cannot be left blank.
    :param max_length: The maximum allowed length of the field.
    :param min_length: The minimum allowed length of the field.
    :param help_text: Help text to display alongside the field.
    :param search_index: If false (default true), the content of this block will not be indexed for searching.
    :param validators: A list of validation functions for the field (see :doc:`Django Validators <django:ref/validators>`).
    :param form_classname: A value to add to the form field's ``class`` attribute when rendered on the page editing form.


.. autoclass:: wagtail.blocks.TextBlock
    :show-inheritance:

    A multi-line text input. As with ``CharBlock``, the following keyword arguments are accepted in addition to the standard ones:

    :param required: If true (the default), the field cannot be left blank.
    :param max_length: The maximum allowed length of the field.
    :param min_length: The minimum allowed length of the field.
    :param help_text: Help text to display alongside the field.
    :param search_index: If false (default true), the content of this block will not be indexed for searching.
    :param rows: Number of rows to show on the textarea (defaults to 1).
    :param validators: A list of validation functions for the field (see :doc:`Django Validators <django:ref/validators>`).
    :param form_classname: A value to add to the form field's ``class`` attribute when rendered on the page editing form.


.. autoclass:: wagtail.blocks.EmailBlock
    :show-inheritance:

    A single-line email input that validates that the value is a valid e-mail address. The following keyword arguments are accepted in addition to the standard ones:

    :param required: If true (the default), the field cannot be left blank.
    :param help_text: Help text to display alongside the field.
    :param validators: A list of validation functions for the field (see :doc:`Django Validators <django:ref/validators>`).
    :param form_classname: A value to add to the form field's ``class`` attribute when rendered on the page editing form.


.. autoclass:: wagtail.blocks.IntegerBlock
    :show-inheritance:

    A single-line integer input that validates that the value is a valid whole number. The following keyword arguments are accepted in addition to the standard ones:

    :param required: If true (the default), the field cannot be left blank.
    :param max_value: The maximum allowed numeric value of the field.
    :param min_value: The minimum allowed numeric value of the field.
    :param help_text: Help text to display alongside the field.
    :param validators: A list of validation functions for the field (see :doc:`Django Validators <django:ref/validators>`).
    :param form_classname: A value to add to the form field's ``class`` attribute when rendered on the page editing form.


.. autoclass:: wagtail.blocks.FloatBlock
    :show-inheritance:

    A single-line Float input that validates that the value is a valid floating point number. The following keyword arguments are accepted in addition to the standard ones:

    :param required: If true (the default), the field cannot be left blank.
    :param max_value: The maximum allowed numeric value of the field.
    :param min_value: The minimum allowed numeric value of the field.
    :param validators: A list of validation functions for the field (see :doc:`Django Validators <django:ref/validators>`).
    :param form_classname: A value to add to the form field's ``class`` attribute when rendered on the page editing form.


.. autoclass:: wagtail.blocks.DecimalBlock
    :show-inheritance:

    A single-line decimal input that validates that the value is a valid decimal number. The following keyword arguments are accepted in addition to the standard ones:

    :param required: If true (the default), the field cannot be left blank.
    :param help_text: Help text to display alongside the field.
    :param max_value: The maximum allowed numeric value of the field.
    :param min_value: The minimum allowed numeric value of the field.
    :param max_digits: The maximum number of digits allowed in the number. This number must be greater than or equal to ``decimal_places``.
    :param decimal_places: The number of decimal places to store with the number.
    :param validators: A list of validation functions for the field (see :doc:`Django Validators <django:ref/validators>`).
    :param form_classname: A value to add to the form field's ``class`` attribute when rendered on the page editing form.


.. autoclass:: wagtail.blocks.RegexBlock
    :show-inheritance:

    A single-line text input that validates a string against a regular expression. The regular expression used for validation must be supplied as the first argument, or as the keyword argument ``regex``.

    .. code-block:: python

       blocks.RegexBlock(regex=r'^[0-9]{3}$', error_messages={
           'invalid': "Not a valid library card number."
       })

    The following keyword arguments are accepted in addition to the standard ones:

    :param regex: Regular expression to validate against.
    :param error_messages: Dictionary of error messages, containing either or both of the keys ``required`` (for the message shown on an empty value) or ``invalid`` (for the message shown on a non-matching value).
    :param required: If true (the default), the field cannot be left blank.
    :param help_text: Help text to display alongside the field.
    :param max_length: The maximum allowed length of the field.
    :param min_length: The minimum allowed length of the field.
    :param validators: A list of validation functions for the field (see :doc:`Django Validators <django:ref/validators>`).
    :param form_classname: A value to add to the form field's ``class`` attribute when rendered on the page editing form.


.. autoclass:: wagtail.blocks.URLBlock
    :show-inheritance:

    A single-line text input that validates that the string is a valid URL. The following keyword arguments are accepted in addition to the standard ones:

    :param required: If true (the default), the field cannot be left blank.
    :param max_length: The maximum allowed length of the field.
    :param min_length: The minimum allowed length of the field.
    :param help_text: Help text to display alongside the field.
    :param validators: A list of validation functions for the field (see :doc:`Django Validators <django:ref/validators>`).
    :param form_classname: A value to add to the form field's ``class`` attribute when rendered on the page editing form.


.. autoclass:: wagtail.blocks.BooleanBlock
    :show-inheritance:

    A checkbox. The following keyword arguments are accepted in addition to the standard ones:

    :param required: If true (the default), the checkbox must be ticked to proceed. As with Django's ``BooleanField``, a checkbox that can be left ticked or unticked must be explicitly denoted with ``required=False``.
    :param help_text: Help text to display alongside the field.
    :param form_classname: A value to add to the form field's ``class`` attribute when rendered on the page editing form.


.. autoclass:: wagtail.blocks.DateBlock
    :show-inheritance:

    A date picker. The following keyword arguments are accepted in addition to the standard ones:

    :param format: Date format. This must be one of the recognized formats listed in the :std:setting:`django:DATE_INPUT_FORMATS` setting. If not specified Wagtail will use the ``WAGTAIL_DATE_FORMAT`` setting with fallback to ``"%Y-%m-%d"``.
    :param required: If true (the default), the field cannot be left blank.
    :param help_text: Help text to display alongside the field.
    :param validators: A list of validation functions for the field (see :doc:`Django Validators <django:ref/validators>`).
    :param form_classname: A value to add to the form field's ``class`` attribute when rendered on the page editing form.


.. autoclass:: wagtail.blocks.TimeBlock
    :show-inheritance:

    A time picker. The following keyword arguments are accepted in addition to the standard ones:

    :param format: Time format. This must be one of the recognized formats listed in the :std:setting:`django:TIME_INPUT_FORMATS` setting. If not specified Wagtail will use the ``WAGTAIL_TIME_FORMAT`` setting with fallback to ``"%H:%M"``.
    :param required: If true (the default), the field cannot be left blank.
    :param help_text: Help text to display alongside the field.
    :param validators: A list of validation functions for the field (see :doc:`Django Validators <django:ref/validators>`).
    :param form_classname: A value to add to the form field's ``class`` attribute when rendered on the page editing form.


.. autoclass:: wagtail.blocks.DateTimeBlock
    :show-inheritance:

    A combined date/time picker. The following keyword arguments are accepted in addition to the standard ones:

    :param format: Date/time format. This must be one of the recognized formats listed in the :std:setting:`django:DATETIME_INPUT_FORMATS` setting. If not specified Wagtail will use the ``WAGTAIL_DATETIME_FORMAT`` setting with fallback to ``"%Y-%m-%d %H:%M"``.
    :param required: If true (the default), the field cannot be left blank.
    :param help_text: Help text to display alongside the field.
    :param validators: A list of validation functions for the field (see :doc:`Django Validators <django:ref/validators>`).
    :param form_classname: A value to add to the form field's ``class`` attribute when rendered on the page editing form.


.. autoclass:: wagtail.blocks.RichTextBlock
    :show-inheritance:

    A WYSIWYG editor for creating formatted text including links, bold / italics etc. The following keyword arguments are accepted in addition to the standard ones:

    :param editor: The rich text editor to be used (see :ref:`wagtailadmin_rich_text_editors`).
    :param features: Specifies the set of features allowed (see :ref:`rich_text_features`).
    :param required: If true (the default), the field cannot be left blank.
    :param max_length: The maximum allowed length of the field. Only text is counted; rich text formatting, embedded content and paragraph / line breaks do not count towards the limit.
    :param min_length: The minimum allowed length of the field. Only text is counted; rich text formatting, embedded content and paragraph / line breaks do not count towards the limit.
    :param search_index: If false (default true), the content of this block will not be indexed for searching.
    :param help_text: Help text to display alongside the field.
    :param validators: A list of validation functions for the field (see :doc:`Django Validators <django:ref/validators>`).
    :param form_classname: A value to add to the form field's ``class`` attribute when rendered on the page editing form.


.. autoclass:: wagtail.blocks.RawHTMLBlock
    :show-inheritance:

    A text area for entering raw HTML which will be rendered unescaped in the page output. The following keyword arguments are accepted in addition to the standard ones:

    :param required: If true (the default), the field cannot be left blank.
    :param max_length: The maximum allowed length of the field.
    :param min_length: The minimum allowed length of the field.
    :param help_text: Help text to display alongside the field.
    :param validators: A list of validation functions for the field (see :doc:`Django Validators <django:ref/validators>`).
    :param form_classname: A value to add to the form field's ``class`` attribute when rendered on the page editing form.

    .. WARNING::
      When this block is in use, there is nothing to prevent editors from inserting malicious scripts into the page, including scripts that would allow the editor to acquire administrator privileges when another administrator views the page. Do not use this block unless your editors are fully trusted.


.. autoclass:: wagtail.blocks.BlockQuoteBlock
    :show-inheritance:

    A text field, the contents of which will be wrapped in an HTML `<blockquote>` tag pair in the page output. The following keyword arguments are accepted in addition to the standard ones:

    :param required: If true (the default), the field cannot be left blank.
    :param max_length: The maximum allowed length of the field.
    :param min_length: The minimum allowed length of the field.
    :param help_text: Help text to display alongside the field.
    :param validators: A list of validation functions for the field (see :doc:`Django Validators <django:ref/validators>`).
    :param form_classname: A value to add to the form field's ``class`` attribute when rendered on the page editing form.


.. autoclass:: wagtail.blocks.ChoiceBlock
    :show-inheritance:

    A dropdown select box for choosing one item from a list of choices. The following keyword arguments are accepted in addition to the standard ones:

    :param choices: A list of choices, in any format accepted by Django's :attr:`~django.db.models.Field.choices` parameter for model fields, or a callable returning such a list.
    :param required: If true (the default), the field cannot be left blank.
    :param help_text: Help text to display alongside the field.
    :param search_index: If false (default true), the content of this block will not be indexed for searching.
    :param widget: The form widget to render the field with (see :doc:`Django Widgets <django:ref/forms/widgets>`).
    :param validators: A list of validation functions for the field (see :doc:`Django Validators <django:ref/validators>`).
    :param form_classname: A value to add to the form field's ``class`` attribute when rendered on the page editing form.

    ``ChoiceBlock`` can also be subclassed to produce a reusable block with the same list of choices everywhere it is used. For example, a block definition such as:

    .. code-block:: python

       blocks.ChoiceBlock(choices=[
           ('tea', 'Tea'),
           ('coffee', 'Coffee'),
       ], icon='cup')


    Could be rewritten as a subclass of ChoiceBlock:


    .. code-block:: python

       class DrinksChoiceBlock(blocks.ChoiceBlock):
           choices = [
               ('tea', 'Tea'),
               ('coffee', 'Coffee'),
           ]

           class Meta:
               icon = 'cup'


    ``StreamField`` definitions can then refer to ``DrinksChoiceBlock()`` in place of the full ``ChoiceBlock`` definition. Note that this only works when ``choices`` is a fixed list, not a callable.
```

(streamfield_multiplechoiceblock)=

```{eval-rst}

.. autoclass:: wagtail.blocks.MultipleChoiceBlock
    :show-inheritance:

    A select box for choosing multiple items from a list of choices. The following keyword arguments are accepted in addition to the standard ones:

    :param choices: A list of choices, in any format accepted by Django's :attr:`~django.db.models.Field.choices` parameter for model fields, or a callable returning such a list.
    :param required: If true (the default), the field cannot be left blank.
    :param help_text: Help text to display alongside the field.
    :param search_index: If false (default true), the content of this block will not be indexed for searching.
    :param widget: The form widget to render the field with (see :doc:`Django Widgets <django:ref/forms/widgets>`).
    :param validators: A list of validation functions for the field (see :doc:`Django Validators <django:ref/validators>`).
    :param form_classname: A value to add to the form field's ``class`` attribute when rendered on the page editing form.


.. autoclass:: wagtail.blocks.PageChooserBlock
    :show-inheritance:

    A control for selecting a page object, using Wagtail's page browser. The following keyword arguments are accepted in addition to the standard ones:

    :param required: If true (the default), the field cannot be left blank.
    :param page_type: Restrict choices to one or more specific page types; by default, any page type may be selected. Can be specified as a page model class, model name (as a string), or a list or tuple of these.
    :param can_choose_root: Defaults to false. If true, the editor can choose the tree root as a page. Normally this would be undesirable since the tree root is never a usable page, but in some specialized cases, it may be appropriate. For example, a block providing a feed of related articles could use a PageChooserBlock to select which subsection of the site articles will be taken from, with the root corresponding to 'everywhere'.


.. autoclass:: wagtail.documents.blocks.DocumentChooserBlock
    :show-inheritance:

    A control to allow the editor to select an existing document object, or upload a new one. The following additional keyword argument is accepted:

    :param required: If true (the default), the field cannot be left blank.
```

(streamfield_imageblock)=

```{eval-rst}

.. autoclass:: wagtail.images.blocks.ImageBlock
    :show-inheritance:

    An accessibility-focused control to allow the editor to select an existing image, or upload a new one. This has provision for adding alt text and indicating whether images are purely decorative, and is the Wagtail-recommended approach to uploading images. The following additional keyword argument is accepted:

    :param required: If true (the default), the field cannot be left blank.

    ``ImageBlock`` incorporates backwards compatibility with ``ImageChooserBlock``. A block initially defined as ``ImageChooserBlock`` can be directly replaced with ``ImageBlock`` - existing data created with ``ImageChooserBlock`` will be handled automatically and changed to ``ImageBlock``'s data format when the field is resaved.
```

```{eval-rst}
.. autoclass:: wagtail.images.blocks.ImageChooserBlock
    :show-inheritance:

    A control to allow the editor to select an existing image, or upload a new one. The following additional keyword argument is accepted:

    :param required: If true (the default), the field cannot be left blank.


.. autoclass:: wagtail.snippets.blocks.SnippetChooserBlock
    :show-inheritance:

    A control to allow the editor to select a snippet object. Requires one positional argument: the snippet class to choose from. The following additional keyword argument is accepted:

    :param required: If true (the default), the field cannot be left blank.


.. autoclass:: wagtail.embeds.blocks.EmbedBlock
    :show-inheritance:

    A field for the editor to enter a URL to a media item (such as a YouTube video) to appear as embedded media on the page. The following keyword arguments are accepted in addition to the standard ones:

    :param required: If true (the default), the field cannot be left blank.
    :param max_width: The maximum width of the embed, in pixels; this will be passed to the provider when requesting the embed.
    :param max_height: The maximum height of the embed, in pixels; this will be passed to the provider when requesting the embed.:param max_length: The maximum allowed length of the field.
    :param min_length: The minimum allowed length of the field.
    :param help_text: Help text to display alongside the field.
```

(streamfield_staticblock)=

## Structural block types

```{eval-rst}
.. autoclass:: wagtail.blocks.StaticBlock
    :show-inheritance:

    A block which doesn't have any fields, thus passes no particular values to its template during rendering. This can be useful if you need the editor to be able to insert some content that is always the same or doesn't need to be configured within the page editor, such as an address, embed code from third-party services, or more complex pieces of code if the template uses template tags. The following additional keyword argument is accepted:

    :param admin_text: A text string to display in the admin when this block is used. By default, some default text (which contains the ``label`` keyword argument if you pass it) will be displayed in the editor interface, so that the block doesn't look empty, but this can be customized by passing ``admin_text``:

    .. code-block:: python

       blocks.StaticBlock(
           admin_text='Latest posts: no configuration needed.',
           # or admin_text=mark_safe('<b>Latest posts</b>: no configuration needed.'),
           template='latest_posts.html')

    ``StaticBlock`` can also be subclassed to produce a reusable block with the same configuration everywhere it is used:


    .. code-block:: python

       class LatestPostsStaticBlock(blocks.StaticBlock):
           class Meta:
               icon = 'user'
               label = 'Latest posts'
               admin_text = '{label}: configured elsewhere'.format(label=label)
               template = 'latest_posts.html'


.. autoclass:: wagtail.blocks.StructBlock
    :show-inheritance:

    A block consisting of a fixed group of sub-blocks to be displayed together. Takes a list of ``(name, block_definition)`` tuples as its first argument:

    .. code-block:: python

       body = StreamField([
           # ...
           ('person', blocks.StructBlock([
               ('first_name', blocks.CharBlock()),
               ('surname', blocks.CharBlock()),
               ('photo', ImageBlock(required=False)),
               ('biography', blocks.RichTextBlock()),
           ], icon='user')),
       ])


    Alternatively, StructBlock can be subclassed to specify a reusable set of sub-blocks:


    .. code-block:: python

       class PersonBlock(blocks.StructBlock):
           first_name = blocks.CharBlock()
           surname = blocks.CharBlock()
           photo = ImageBlock(required=False)
           biography = blocks.RichTextBlock()

           class Meta:
               icon = 'user'

    The ``Meta`` class supports the properties ``default``, ``label``, ``icon`` and ``template``, which have the same meanings as when they are passed to the block's constructor.


    This defines ``PersonBlock()`` as a block type for use in StreamField definitions:

    .. code-block:: python

       body = StreamField([
           ('heading', blocks.CharBlock(form_classname="title")),
           ('paragraph', blocks.RichTextBlock()),
           ('image', ImageBlock()),
           ('person', PersonBlock()),
       ])


    The following additional options are available as either keyword arguments or Meta class attributes:

    :param form_classname: An HTML ``class`` attribute to set on the root element of this block as displayed in the editing interface. Defaults to ``struct-block``; note that the admin interface has CSS styles defined on this class, so it is advised to include ``struct-block`` in this value when overriding. See :ref:`custom_editing_interfaces_for_structblock`.
    :param form_template: Path to a Django template to use to render this block's form. See :ref:`custom_editing_interfaces_for_structblock`.
    :param value_class: A subclass of ``wagtail.blocks.StructValue`` to use as the type of returned values for this block. See :ref:`custom_value_class_for_structblock`.
    :param search_index: If false (default true), the content of this block will not be indexed for searching.
    :param label_format:
     Determines the label shown when the block is collapsed in the editing interface. By default, the value of the first sub-block in the StructBlock is shown, but this can be customized by setting a string here with block names contained in braces - for example ``label_format = "Profile for {first_name} {surname}"``


.. autoclass:: wagtail.blocks.ListBlock
    :show-inheritance:

    A block consisting of many sub-blocks, all of the same type. The editor can add an unlimited number of sub-blocks, and re-order and delete them. Takes the definition of the sub-block as its first argument:

    .. code-block:: python

       body = StreamField([
           # ...
           ('ingredients_list', blocks.ListBlock(blocks.CharBlock(label="Ingredient"))),
       ])



    Any block type is valid as the sub-block type, including structural types:

    .. code-block:: python

       body = StreamField([
           # ...
           ('ingredients_list', blocks.ListBlock(blocks.StructBlock([
               ('ingredient', blocks.CharBlock()),
               ('amount', blocks.CharBlock(required=False)),
           ]))),
       ])


    The following additional options are available as either keyword arguments or Meta class attributes:

    :param form_classname: An HTML ``class`` attribute to set on the root element of this block as displayed in the editing interface.
    :param min_num: Minimum number of sub-blocks that the list must have.
    :param max_num: Maximum number of sub-blocks that the list may have.
    :param search_index: If false (default true), the content of this block will not be indexed for searching.
    :param collapsed: When true, all sub-blocks are initially collapsed.


.. autoclass:: wagtail.blocks.StreamBlock
    :show-inheritance:

    A block consisting of a sequence of sub-blocks of different types, which can be mixed and reordered at will. Used as the overall mechanism of the StreamField itself, but can also be nested or used within other structural block types. Takes a list of ``(name, block_definition)`` tuples as its first argument:

    .. code-block:: python

       body = StreamField([
           # ...
           ('carousel', blocks.StreamBlock(
               [
                   ('image', ImageBlock()),
                   ('quotation', blocks.StructBlock([
                       ('text', blocks.TextBlock()),
                       ('author', blocks.CharBlock()),
                   ])),
                   ('video', EmbedBlock()),
               ],
               icon='cogs'
           )),
       ])


    As with StructBlock, the list of sub-blocks can also be provided as a subclass of StreamBlock:

    .. code-block:: python

       class CarouselBlock(blocks.StreamBlock):
           image = ImageBlock()
           quotation = blocks.StructBlock([
               ('text', blocks.TextBlock()),
               ('author', blocks.CharBlock()),
           ])
           video = EmbedBlock()

           class Meta:
               icon='cogs'

    Since ``StreamField`` accepts an instance of ``StreamBlock`` as a parameter, in place of a list of block types, this makes it possible to re-use a common set of block types without repeating definitions:

    .. code-block:: python

        class HomePage(Page):
            carousel = StreamField(
                CarouselBlock(max_num=10, block_counts={'video': {'max_num': 2}}),
            )

    ``StreamBlock`` accepts the following additional options as either keyword arguments or ``Meta`` properties:

    :param required: If true (the default), at least one sub-block must be supplied. This is ignored when using the ``StreamBlock`` as the top-level block of a StreamField; in this case, the StreamField's ``blank`` property is respected instead.
    :param min_num: Minimum number of sub-blocks that the stream must have.
    :param max_num: Maximum number of sub-blocks that the stream may have.
    :param search_index: If false (default true), the content of this block will not be indexed for searching.
    :param block_counts: Specifies the minimum and maximum number of each block type, as a dictionary mapping block names to dicts with (optional) ``min_num`` and ``max_num`` fields.
    :param collapsed: When true, all sub-blocks are initially collapsed.
    :param form_classname: An HTML ``class`` attribute to set on the root element of this block as displayed in the editing interface.

    .. code-block:: python
        :emphasize-lines: 6

        body = StreamField([
            # ...
            ('event_promotions', blocks.StreamBlock([
                ('hashtag', blocks.CharBlock()),
                ('post_date', blocks.DateBlock()),
            ], form_classname='event-promotions')),
        ])

    .. code-block:: python
        :emphasize-lines: 6

        class EventPromotionsBlock(blocks.StreamBlock):
            hashtag = blocks.CharBlock()
            post_date = blocks.DateBlock()

            class Meta:
                form_classname = 'event-promotions'
```
