(streamfield_block_reference)=

# StreamField block reference

This document details the block types provided by Wagtail for use in [StreamField](streamfield), and how they can be combined into new block types.

```{eval-rst}
.. class:: wagtail.fields.StreamField(blocks, use_json_field=None, blank=False, min_num=None, max_num=None, block_counts=None, collapsed=False)

   A model field for representing long-form content as a sequence of content blocks of various types. See :ref:`streamfield_topic`.

   :param blocks: A list of block types, passed as either a list of ``(name, block_definition)`` tuples or a ``StreamBlock`` instance.
   :param use_json_field: When true, the field uses :class:`~django.db.models.JSONField` as its internal type, allowing the use of ``JSONField`` lookups and transforms. When false, it uses :class:`~django.db.models.TextField` instead. This argument **must** be set to ``True``/``False``.
   :param blank: When false (the default), at least one block must be provided for the field to be considered valid.
   :param min_num: Minimum number of sub-blocks that the stream must have.
   :param max_num: Maximum number of sub-blocks that the stream may have.
   :param block_counts: Specifies the minimum and maximum number of each block type, as a dictionary mapping block names to dicts with (optional) ``min_num`` and ``max_num`` fields.
   :param collapsed: When true, all blocks are initially collapsed.
```

```{versionchanged} 3.0
The required `use_json_field` argument is added.
```

```python
body = StreamField([
    ('heading', blocks.CharBlock(form_classname="full title")),
    ('paragraph', blocks.RichTextBlock()),
    ('image', ImageChooserBlock()),
], block_counts={
    'heading': {'min_num': 1},
    'image': {'max_num': 5},
}, use_json_field=True)
```

## Block options

All block definitions accept the following optional keyword arguments:

-   `default`
    -   The default value that a new 'empty' block should receive.
-   `label`
    -   The label to display in the editor interface when referring to this block - defaults to a prettified version of the block name (or, in a context where no name is assigned - such as within a `ListBlock` - the empty string).
-   `icon`
    -   The name of the icon to display for this block type in the menu of available block types. For a list of icon names, see the Wagtail style guide, which can be enabled by adding `wagtail.contrib.styleguide` to your project’s `INSTALLED_APPS`.
-   `template`
    -   The path to a Django template that will be used to render this block on the front end. See [Template rendering](streamfield_template_rendering)
-   `group`
    -   The group used to categorize this block, i.e. any blocks with the same group name will be shown together in the editor interface with the group name as a heading.

## Field block types

```{eval-rst}
.. class:: wagtail.blocks.CharBlock

   A single-line text input. The following keyword arguments are accepted in addition to the standard ones:

   :param required: If true (the default), the field cannot be left blank.
   :param max_length: The maximum allowed length of the field.
   :param min_length: The minimum allowed length of the field.
   :param help_text: Help text to display alongside the field.
   :param validators: A list of validation functions for the field (see `Django Validators <https://docs.djangoproject.com/en/stable/ref/validators/>`__).
   :param form_classname: A value to add to the form field's ``class`` attribute when rendered on the page editing form.


.. class:: wagtail.blocks.TextBlock

   A multi-line text input. As with ``CharBlock``, the following keyword arguments are accepted in addition to the standard ones:

   :param required: If true (the default), the field cannot be left blank.
   :param max_length: The maximum allowed length of the field.
   :param min_length: The minimum allowed length of the field.
   :param help_text: Help text to display alongside the field.
   :param rows: Number of rows to show on the textarea (defaults to 1).
   :param validators: A list of validation functions for the field (see `Django Validators <https://docs.djangoproject.com/en/stable/ref/validators/>`__).
   :param form_classname: A value to add to the form field's ``class`` attribute when rendered on the page editing form.


.. class:: wagtail.blocks.EmailBlock

   A single-line email input that validates that the value is a valid e-mail address. The following keyword arguments are accepted in addition to the standard ones:

   :param required: If true (the default), the field cannot be left blank.
   :param help_text: Help text to display alongside the field.
   :param validators: A list of validation functions for the field (see `Django Validators <https://docs.djangoproject.com/en/stable/ref/validators/>`__).
   :param form_classname: A value to add to the form field's ``class`` attribute when rendered on the page editing form.


.. class:: wagtail.blocks.IntegerBlock

   A single-line integer input that validates that the value is a valid whole number. The following keyword arguments are accepted in addition to the standard ones:

   :param required: If true (the default), the field cannot be left blank.
   :param max_value: The maximum allowed numeric value of the field.
   :param min_value: The minimum allowed numeric value of the field.
   :param help_text: Help text to display alongside the field.
   :param validators: A list of validation functions for the field (see `Django Validators <https://docs.djangoproject.com/en/stable/ref/validators/>`__).
   :param form_classname: A value to add to the form field's ``class`` attribute when rendered on the page editing form.


.. class:: wagtail.blocks.FloatBlock

   A single-line Float input that validates that the value is a valid floating point number. The following keyword arguments are accepted in addition to the standard ones:

   :param required: If true (the default), the field cannot be left blank.
   :param max_value: The maximum allowed numeric value of the field.
   :param min_value: The minimum allowed numeric value of the field.
   :param validators: A list of validation functions for the field (see `Django Validators <https://docs.djangoproject.com/en/stable/ref/validators/>`__).
   :param form_classname: A value to add to the form field's ``class`` attribute when rendered on the page editing form.


.. class:: wagtail.blocks.DecimalBlock

   A single-line decimal input that validates that the value is a valid decimal number. The following keyword arguments are accepted in addition to the standard ones:

   :param required: If true (the default), the field cannot be left blank.
   :param help_text: Help text to display alongside the field.
   :param max_value: The maximum allowed numeric value of the field.
   :param min_value: The minimum allowed numeric value of the field.
   :param max_digits: The maximum number of digits allowed in the number. This number must be greater than or equal to ``decimal_places``.
   :param decimal_places: The number of decimal places to store with the number.
   :param validators: A list of validation functions for the field (see `Django Validators <https://docs.djangoproject.com/en/stable/ref/validators/>`__).
   :param form_classname: A value to add to the form field's ``class`` attribute when rendered on the page editing form.


.. class:: wagtail.blocks.RegexBlock

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
   :param validators: A list of validation functions for the field (see `Django Validators <https://docs.djangoproject.com/en/stable/ref/validators/>`__).
   :param form_classname: A value to add to the form field's ``class`` attribute when rendered on the page editing form.


.. class:: wagtail.blocks.URLBlock

   A single-line text input that validates that the string is a valid URL. The following keyword arguments are accepted in addition to the standard ones:

   :param required: If true (the default), the field cannot be left blank.
   :param max_length: The maximum allowed length of the field.
   :param min_length: The minimum allowed length of the field.
   :param help_text: Help text to display alongside the field.
   :param validators: A list of validation functions for the field (see `Django Validators <https://docs.djangoproject.com/en/stable/ref/validators/>`__).
   :param form_classname: A value to add to the form field's ``class`` attribute when rendered on the page editing form.


.. class:: wagtail.blocks.BooleanBlock

   A checkbox. The following keyword arguments are accepted in addition to the standard ones:

   :param required: If true (the default), the checkbox must be ticked to proceed. As with Django's ``BooleanField``, a checkbox that can be left ticked or unticked must be explicitly denoted with ``required=False``.
   :param help_text: Help text to display alongside the field.
   :param form_classname: A value to add to the form field's ``class`` attribute when rendered on the page editing form.


.. class:: wagtail.blocks.DateBlock

    A date picker. The following keyword arguments are accepted in addition to the standard ones:

   :param format: Date format. This must be one of the recognised formats listed in the `DATE_INPUT_FORMATS <https://docs.djangoproject.com/en/stable/ref/settings/#std:setting-DATE_INPUT_FORMATS>`_ setting. If not specified Wagtail will use the ``WAGTAIL_DATE_FORMAT`` setting with fallback to '%Y-%m-%d'.
   :param required: If true (the default), the field cannot be left blank.
   :param help_text: Help text to display alongside the field.
   :param validators: A list of validation functions for the field (see `Django Validators <https://docs.djangoproject.com/en/stable/ref/validators/>`__).
   :param form_classname: A value to add to the form field's ``class`` attribute when rendered on the page editing form.


.. class:: wagtail.blocks.TimeBlock

    A time picker. The following keyword arguments are accepted in addition to the standard ones:

   :param required: If true (the default), the field cannot be left blank.
   :param help_text: Help text to display alongside the field.
   :param validators: A list of validation functions for the field (see `Django Validators <https://docs.djangoproject.com/en/stable/ref/validators/>`__).
   :param form_classname: A value to add to the form field's ``class`` attribute when rendered on the page editing form.


.. class:: wagtail.blocks.DateTimeBlock

    A combined date / time picker. The following keyword arguments are accepted in addition to the standard ones:

   :param format: Date/time format. This must be one of the recognised formats listed in the `DATETIME_INPUT_FORMATS <https://docs.djangoproject.com/en/stable/ref/settings/#std:setting-DATETIME_INPUT_FORMATS>`_ setting. If not specified Wagtail will use the ``WAGTAIL_DATETIME_FORMAT`` setting with fallback to '%Y-%m-%d %H:%M'.
   :param required: If true (the default), the field cannot be left blank.
   :param help_text: Help text to display alongside the field.
   :param validators: A list of validation functions for the field (see `Django Validators <https://docs.djangoproject.com/en/stable/ref/validators/>`__).
   :param form_classname: A value to add to the form field's ``class`` attribute when rendered on the page editing form.


.. class:: wagtail.blocks.RichTextBlock

   A WYSIWYG editor for creating formatted text including links, bold / italics etc. The following keyword arguments are accepted in addition to the standard ones:

   :param editor: The rich text editor to be used (see :ref:`WAGTAILADMIN_RICH_TEXT_EDITORS`).
   :param features: Specifies the set of features allowed (see :ref:`rich_text_features`).
   :param required: If true (the default), the field cannot be left blank.
   :param help_text: Help text to display alongside the field.
   :param validators: A list of validation functions for the field (see `Django Validators <https://docs.djangoproject.com/en/stable/ref/validators/>`__).
   :param form_classname: A value to add to the form field's ``class`` attribute when rendered on the page editing form.


.. class:: wagtail.blocks.RawHTMLBlock

   A text area for entering raw HTML which will be rendered unescaped in the page output. The following keyword arguments are accepted in addition to the standard ones:

   :param required: If true (the default), the field cannot be left blank.
   :param max_length: The maximum allowed length of the field.
   :param min_length: The minimum allowed length of the field.
   :param help_text: Help text to display alongside the field.
   :param validators: A list of validation functions for the field (see `Django Validators <https://docs.djangoproject.com/en/stable/ref/validators/>`__).
   :param form_classname: A value to add to the form field's ``class`` attribute when rendered on the page editing form.

   .. WARNING::
      When this block is in use, there is nothing to prevent editors from inserting malicious scripts into the page, including scripts that would allow the editor to acquire administrator privileges when another administrator views the page. Do not use this block unless your editors are fully trusted.


.. class:: wagtail.blocks.BlockQuoteBlock

   A text field, the contents of which will be wrapped in an HTML `<blockquote>` tag pair in the page output. The following keyword arguments are accepted in addition to the standard ones:

   :param required: If true (the default), the field cannot be left blank.
   :param max_length: The maximum allowed length of the field.
   :param min_length: The minimum allowed length of the field.
   :param help_text: Help text to display alongside the field.
   :param validators: A list of validation functions for the field (see `Django Validators <https://docs.djangoproject.com/en/stable/ref/validators/>`__).
   :param form_classname: A value to add to the form field's ``class`` attribute when rendered on the page editing form.


.. class:: wagtail.blocks.ChoiceBlock

   A dropdown select box for choosing one item from a list of choices. The following keyword arguments are accepted in addition to the standard ones:

   :param choices: A list of choices, in any format accepted by Django's :attr:`~django.db.models.Field.choices` parameter for model fields, or a callable returning such a list.
   :param required: If true (the default), the field cannot be left blank.
   :param help_text: Help text to display alongside the field.
   :param widget: The form widget to render the field with (see `Django Widgets <https://docs.djangoproject.com/en/stable/ref/forms/widgets/>`__).
   :param validators: A list of validation functions for the field (see `Django Validators <https://docs.djangoproject.com/en/stable/ref/validators/>`__).
   :param form_classname: A value to add to the form field's ``class`` attribute when rendered on the page editing form.

   ``ChoiceBlock`` can also be subclassed to produce a reusable block with the same list of choices everywhere it is used. For example, a block definition such as:

   .. code-block:: python

       blocks.ChoiceBlock(choices=[
           ('tea', 'Tea'),
           ('coffee', 'Coffee'),
       ], icon='cup')


   could be rewritten as a subclass of ChoiceBlock:

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

.. class:: wagtail.blocks.MultipleChoiceBlock

   A select box for choosing multiple items from a list of choices. The following keyword arguments are accepted in addition to the standard ones:

   :param choices: A list of choices, in any format accepted by Django's :attr:`~django.db.models.Field.choices` parameter for model fields, or a callable returning such a list.
   :param required: If true (the default), the field cannot be left blank.
   :param help_text: Help text to display alongside the field.
   :param widget: The form widget to render the field with (see `Django Widgets <https://docs.djangoproject.com/en/stable/ref/forms/widgets/>`__).
   :param validators: A list of validation functions for the field (see `Django Validators <https://docs.djangoproject.com/en/stable/ref/validators/>`__).
   :param form_classname: A value to add to the form field's ``class`` attribute when rendered on the page editing form.


.. class:: wagtail.blocks.PageChooserBlock

   A control for selecting a page object, using Wagtail's page browser. The following keyword arguments are accepted in addition to the standard ones:

   :param required: If true (the default), the field cannot be left blank.
   :param page_type: Restrict choices to one or more specific page types; by default, any page type may be selected. Can be specified as a page model class, model name (as a string), or a list or tuple of these.
   :param can_choose_root: Defaults to false. If true, the editor can choose the tree root as a page. Normally this would be undesirable, since the tree root is never a usable page, but in some specialised cases it may be appropriate. For example, a block providing a feed of related articles could use a PageChooserBlock to select which subsection of the site articles will be taken from, with the root corresponding to 'everywhere'.


.. class:: wagtail.documents.blocks.DocumentChooserBlock

   A control to allow the editor to select an existing document object, or upload a new one. The following additional keyword argument is accepted:

   :param required: If true (the default), the field cannot be left blank.


.. class:: wagtail.images.blocks.ImageChooserBlock

   A control to allow the editor to select an existing image, or upload a new one. The following additional keyword argument is accepted:

   :param required: If true (the default), the field cannot be left blank.


.. class:: wagtail.snippets.blocks.SnippetChooserBlock

   A control to allow the editor to select a snippet object. Requires one positional argument: the snippet class to choose from. The following additional keyword argument is accepted:

   :param required: If true (the default), the field cannot be left blank.


.. class:: wagtail.embeds.blocks.EmbedBlock

   A field for the editor to enter a URL to a media item (such as a YouTube video) to appear as embedded media on the page. The following keyword arguments are accepted in addition to the standard ones:

   :param required: If true (the default), the field cannot be left blank.
   :param max_width: The maximum width of the embed, in pixels; this will be passed to the provider when requesting the embed.
   :param max_height: The maximum height of the embed, in pixels; this will be passed to the provider when requesting the embed.
   :param max_length: The maximum allowed length of the field.
   :param min_length: The minimum allowed length of the field.
   :param help_text: Help text to display alongside the field.
```

(streamfield_staticblock)=

## Structural block types

```{eval-rst}
.. class:: wagtail.blocks.StaticBlock

   A block which doesn't have any fields, thus passes no particular values to its template during rendering. This can be useful if you need the editor to be able to insert some content which is always the same or doesn't need to be configured within the page editor, such as an address, embed code from third-party services, or more complex pieces of code if the template uses template tags. The following additional keyword argument is accepted:

   :param admin_text: A text string to display in the admin when this block is used. By default, some default text (which contains the ``label`` keyword argument if you pass it) will be displayed in the editor interface, so that the block doesn't look empty, but this can be customised by passing ``admin_text``:

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


.. class:: wagtail.blocks.StructBlock

   A block consisting of a fixed group of sub-blocks to be displayed together. Takes a list of ``(name, block_definition)`` tuples as its first argument:

   .. code-block:: python

       body = StreamField([
           # ...
           ('person', blocks.StructBlock([
               ('first_name', blocks.CharBlock()),
               ('surname', blocks.CharBlock()),
               ('photo', ImageChooserBlock(required=False)),
               ('biography', blocks.RichTextBlock()),
           ], icon='user')),
       ], use_json_field=True)


   Alternatively, StructBlock can be subclassed to specify a reusable set of sub-blocks:

   .. code-block:: python

       class PersonBlock(blocks.StructBlock):
           first_name = blocks.CharBlock()
           surname = blocks.CharBlock()
           photo = ImageChooserBlock(required=False)
           biography = blocks.RichTextBlock()

           class Meta:
               icon = 'user'


   The ``Meta`` class supports the properties ``default``, ``label``, ``icon`` and ``template``, which have the same meanings as when they are passed to the block's constructor.

   This defines ``PersonBlock()`` as a block type for use in StreamField definitions:

   .. code-block:: python

       body = StreamField([
           ('heading', blocks.CharBlock(form_classname="full title")),
           ('paragraph', blocks.RichTextBlock()),
           ('image', ImageChooserBlock()),
           ('person', PersonBlock()),
       ], use_json_field=True)

   The following additional options are available as either keyword arguments or Meta class attributes:

   :param form_classname: An HTML ``class`` attribute to set on the root element of this block as displayed in the editing interface. Defaults to ``struct-block``; note that the admin interface has CSS styles defined on this class, so it is advised to include ``struct-block`` in this value when overriding. See :ref:`custom_editing_interfaces_for_structblock`.
   :param form_template: Path to a Django template to use to render this block's form. See :ref:`custom_editing_interfaces_for_structblock`.
   :param value_class: A subclass of ``wagtail.blocks.StructValue`` to use as the type of returned values for this block. See :ref:`custom_value_class_for_structblock`.
   :param label_format:
     Determines the label shown when the block is collapsed in the editing interface. By default, the value of the first sub-block in the StructBlock is shown, but this can be customised by setting a string here with block names contained in braces - e.g. ``label_format = "Profile for {first_name} {surname}"``


.. class:: wagtail.blocks.ListBlock

   A block consisting of many sub-blocks, all of the same type. The editor can add an unlimited number of sub-blocks, and re-order and delete them. Takes the definition of the sub-block as its first argument:

   .. code-block:: python

       body = StreamField([
           # ...
           ('ingredients_list', blocks.ListBlock(blocks.CharBlock(label="Ingredient"))),
       ], use_json_field=True)


   Any block type is valid as the sub-block type, including structural types:

   .. code-block:: python

       body = StreamField([
           # ...
           ('ingredients_list', blocks.ListBlock(blocks.StructBlock([
               ('ingredient', blocks.CharBlock()),
               ('amount', blocks.CharBlock(required=False)),
           ]))),
       ], use_json_field=True)

   The following additional options are available as either keyword arguments or Meta class attributes:

   :param form_classname: An HTML ``class`` attribute to set on the root element of this block as displayed in the editing interface.
   :param min_num: Minimum number of sub-blocks that the list must have.
   :param max_num: Maximum number of sub-blocks that the list may have.
   :param collapsed: When true, all sub-blocks are initially collapsed.


.. class:: wagtail.blocks.StreamBlock

   A block consisting of a sequence of sub-blocks of different types, which can be mixed and reordered at will. Used as the overall mechanism of the StreamField itself, but can also be nested or used within other structural block types. Takes a list of ``(name, block_definition)`` tuples as its first argument:

   .. code-block:: python

       body = StreamField([
           # ...
           ('carousel', blocks.StreamBlock(
               [
                   ('image', ImageChooserBlock()),
                   ('quotation', blocks.StructBlock([
                       ('text', blocks.TextBlock()),
                       ('author', blocks.CharBlock()),
                   ])),
                   ('video', EmbedBlock()),
               ],
               icon='cogs'
           )),
       ], use_json_field=True)


   As with StructBlock, the list of sub-blocks can also be provided as a subclass of StreamBlock:

   .. code-block:: python

       class CarouselBlock(blocks.StreamBlock):
           image = ImageChooserBlock()
           quotation = blocks.StructBlock([
               ('text', blocks.TextBlock()),
               ('author', blocks.CharBlock()),
           ])
           video = EmbedBlock()

           class Meta:
               icon='cogs'
```

(streamfield_top_level_streamblock)=

```{eval-rst}
Since ``StreamField`` accepts an instance of ``StreamBlock`` as a parameter, in place of a list of block types, this makes it possible to re-use a common set of block types without repeating definitions:

.. code-block:: python

    class HomePage(Page):
        carousel = StreamField(
            CarouselBlock(max_num=10, block_counts={'video': {'max_num': 2}}),
            use_json_field=True
        )

``StreamBlock`` accepts the following additional options as either keyword arguments or ``Meta`` properties:

:param required: If true (the default), at least one sub-block must be supplied. This is ignored when using the ``StreamBlock`` as the top-level block of a StreamField; in this case the StreamField's ``blank`` property is respected instead.
:param min_num: Minimum number of sub-blocks that the stream must have.
:param max_num: Maximum number of sub-blocks that the stream may have.
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
    ], use_json_field=True)

.. code-block:: python
    :emphasize-lines: 6

    class EventPromotionsBlock(blocks.StreamBlock):
        hashtag = blocks.CharBlock()
        post_date = blocks.DateBlock()

        class Meta:
            form_classname = 'event-promotions'
```
