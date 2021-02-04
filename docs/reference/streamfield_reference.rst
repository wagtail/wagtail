.. _streamfield_reference:

StreamField reference
=====================

StreamField
-----------

``wagtail.core.fields.StreamField``

A model field for representing long-form content as a sequence of content blocks of various types.

Accepts a list of block types, passed as either a list of ``(name, block_type)`` tuples or a ``StreamBlock`` instance. Also accepts the following optional keyword arguments:

``blank`` (default: ``False``)
  When false, at least one block must be provided for the field to be considered valid.

``min_num``
  Minimum number of sub-blocks that the stream must have.

``max_num``
  Maximum number of sub-blocks that the stream may have.

``block_counts``
  Specifies the minimum and maximum number of each block type, as a dictionary mapping block names to dicts with (optional) ``min_num`` and ``max_num`` fields.

.. versionadded:: 2.13

    The ``min_num``, ``max_num`` and ``block_counts`` arguments were added. Previously, these were only available on the ``StreamBlock`` definition.


Block types
-----------

All block types accept the following optional keyword arguments:

``default``
  The default value that a new 'empty' block should receive.

``label``
  The label to display in the editor interface when referring to this block - defaults to a prettified version of the block name (or, in a context where no name is assigned - such as within a ``ListBlock`` - the empty string).

``icon``
  The name of the icon to display for this block type in the menu of available block types. For a list of icon names, see the Wagtail style guide, which can be enabled by adding ``wagtail.contrib.styleguide`` to your project's ``INSTALLED_APPS``.

``template``
  The path to a Django template that will be used to render this block on the front end. See :ref:`streamfield_template_rendering`.

``group``
  The group used to categorize this block, i.e. any blocks with the same group name will be shown together in the editor interface with the group name as a heading.

CharBlock
~~~~~~~~~

``wagtail.core.blocks.CharBlock``

A single-line text input. The following keyword arguments are accepted:

``required`` (default: True)
  If true, the field cannot be left blank.

``max_length``, ``min_length``
  Ensures that the string is at most or at least the given length.

``help_text``
  Help text to display alongside the field.

``validators``
  A list of validation functions for the field (see `Django Validators <https://docs.djangoproject.com/en/stable/ref/validators/>`__).

``form_classname``
  A value to add to the form field's ``class`` attribute when rendered on the page editing form.

.. versionchanged:: 2.11

    The ``class`` attribute was previously set via the keyword argument ``classname``.


TextBlock
~~~~~~~~~

``wagtail.core.blocks.TextBlock``

A multi-line text input. As with ``CharBlock``, the keyword arguments ``required`` (default: True), ``max_length``, ``min_length``, ``help_text``, ``validators`` and ``form_classname`` are accepted.

EmailBlock
~~~~~~~~~~

``wagtail.core.blocks.EmailBlock``

A single-line email input that validates that the email is a valid Email Address. The keyword arguments ``required`` (default: True), ``help_text``, ``validators`` and ``form_classname`` are accepted.

For an example of ``EmailBlock`` in use, see :ref:`streamfield_personblock_example`

IntegerBlock
~~~~~~~~~~~~

``wagtail.core.blocks.IntegerBlock``

A single-line integer input that validates that the integer is a valid whole number. The keyword arguments ``required`` (default: True), ``max_value``, ``min_value``, ``help_text``, ``validators`` and ``form_classname`` are accepted.

For an example of ``IntegerBlock`` in use, see :ref:`streamfield_personblock_example`

FloatBlock
~~~~~~~~~~

``wagtail.core.blocks.FloatBlock``

A single-line Float input that validates that the value is a valid floating point number. The keyword arguments ``required`` (default: True), ``max_value``, ``min_value``, ``validators`` and ``form_classname`` are accepted.

DecimalBlock
~~~~~~~~~~~~

``wagtail.core.blocks.DecimalBlock``

A single-line decimal input that validates that the value is a valid decimal number. The keyword arguments ``required`` (default: True), ``help_text``, ``max_value``, ``min_value``, ``max_digits``, ``decimal_places``, ``validators`` and ``form_classname`` are accepted.

For an example of ``DecimalBlock`` in use, see :ref:`streamfield_personblock_example`

RegexBlock
~~~~~~~~~~

``wagtail.core.blocks.RegexBlock``

A single-line text input that validates a string against a regex expression. The regular expression used for validation must be supplied as the first argument, or as the keyword argument ``regex``. To customise the message text used to indicate a validation error, pass a dictionary as the keyword argument ``error_messages`` containing either or both of the keys ``required`` (for the message shown on an empty value) or ``invalid`` (for the message shown on a non-matching value):

.. code-block:: python

    blocks.RegexBlock(regex=r'^[0-9]{3}$', error_messages={
        'invalid': "Not a valid library card number."
    })

The keyword arguments ``regex``, ``error_messages``, ``help_text``, ``required`` (default: True), ``max_length``, ``min_length``, ``validators`` and ``form_classname`` are accepted.

URLBlock
~~~~~~~~

``wagtail.core.blocks.URLBlock``

A single-line text input that validates that the string is a valid URL. The keyword arguments ``required`` (default: True), ``max_length``, ``min_length``, ``help_text``, ``validators`` and ``form_classname`` are accepted.

BooleanBlock
~~~~~~~~~~~~

``wagtail.core.blocks.BooleanBlock``

A checkbox. The keyword arguments ``required``, ``help_text`` and ``form_classname`` are accepted. As with Django's ``BooleanField``, a value of ``required=True`` (the default) indicates that the checkbox must be ticked in order to proceed. For a checkbox that can be ticked or unticked, you must explicitly pass in ``required=False``.

DateBlock
~~~~~~~~~

``wagtail.core.blocks.DateBlock``

A date picker. The keyword arguments ``required`` (default: True), ``help_text``, ``validators``, ``form_classname`` and ``format`` are accepted.

``format`` (default: None)
  Date format. This must be one of the recognised formats listed in the `DATE_INPUT_FORMATS <https://docs.djangoproject.com/en/stable/ref/settings/#std:setting-DATE_INPUT_FORMATS>`_ setting. If not specified Wagtail will use ``WAGTAIL_DATE_FORMAT`` setting with fallback to '%Y-%m-%d'.

TimeBlock
~~~~~~~~~

``wagtail.core.blocks.TimeBlock``

A time picker. The keyword arguments ``required`` (default: True), ``help_text``, ``validators`` and ``form_classname`` are accepted.

DateTimeBlock
~~~~~~~~~~~~~

``wagtail.core.blocks.DateTimeBlock``

A combined date / time picker. The keyword arguments ``required`` (default: True), ``help_text``, ``format``, ``validators`` and ``form_classname`` are accepted.

``format`` (default: None)
  Date format. This must be one of the recognised formats listed in the `DATETIME_INPUT_FORMATS <https://docs.djangoproject.com/en/stable/ref/settings/#std:setting-DATETIME_INPUT_FORMATS>`_ setting. If not specified Wagtail will use ``WAGTAIL_DATETIME_FORMAT`` setting with fallback to '%Y-%m-%d %H:%M'.

RichTextBlock
~~~~~~~~~~~~~

``wagtail.core.blocks.RichTextBlock``

A WYSIWYG editor for creating formatted text including links, bold / italics etc. The keyword arguments ``required`` (default: True), ``help_text``, ``validators``, ``form_classname``, ``editor`` and ``features`` are accepted.

``editor`` (default: ``default``)
  The rich text editor to be used (see :ref:`WAGTAILADMIN_RICH_TEXT_EDITORS`).

``features`` (default: None)
  Specify the set of features allowed (see :ref:`rich_text_features`).


RawHTMLBlock
~~~~~~~~~~~~

``wagtail.core.blocks.RawHTMLBlock``

A text area for entering raw HTML which will be rendered unescaped in the page output. The keyword arguments ``required`` (default: True), ``max_length``, ``min_length``, ``help_text``, ``validators`` and ``form_classname`` are accepted.

.. WARNING::
   When this block is in use, there is nothing to prevent editors from inserting malicious scripts into the page, including scripts that would allow the editor to acquire administrator privileges when another administrator views the page. Do not use this block unless your editors are fully trusted.

BlockQuoteBlock
~~~~~~~~~~~~~~~

``wagtail.core.blocks.BlockQuoteBlock``

A text field, the contents of which will be wrapped in an HTML `<blockquote>` tag pair. The keyword arguments ``required`` (default: True), ``max_length``, ``min_length``, ``help_text``, ``validators`` and ``form_classname`` are accepted.


ChoiceBlock
~~~~~~~~~~~

``wagtail.core.blocks.ChoiceBlock``

A dropdown select box for choosing from a list of choices. The following keyword arguments are accepted:

``choices``
  A list of choices, in any format accepted by Django's :attr:`~django.db.models.Field.choices` parameter for model fields, or a callable returning such a list.

``required`` (default: True)
  If true, the field cannot be left blank.

``help_text``
  Help text to display alongside the field.

``validators``
  A list of validation functions for the field (see `Django Validators <https://docs.djangoproject.com/en/stable/ref/validators/>`__).

``form_classname``
  A value to add to the form field's ``class`` attribute when rendered on the page editing form.

``widget``
  The form widget to render the field with (see `Django Widgets <https://docs.djangoproject.com/en/stable/ref/forms/widgets/>`__).

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


.. _streamfield_multiplechoiceblock:

MultipleChoiceBlock
~~~~~~~~~~~~~~~~~~~

``wagtail.core.blocks.MultipleChoiceBlock``

A multiple select box for choosing from a list of choices. The following keyword arguments are accepted:

``choices``
  A list of choices, in any format accepted by Django's :attr:`~django.db.models.Field.choices` parameter for model fields, or a callable returning such a list.

``required`` (default: True)
  If true, the field cannot be left blank.

``help_text``
  Help text to display alongside the field.

``validators``
  A list of validation functions for the field (see `Django Validators <https://docs.djangoproject.com/en/stable/ref/validators/>`__).

``form_classname``
  A value to add to the form field's ``class`` attribute when rendered on the page editing form.

``widget``
  The form widget to render the field with (see `Django Widgets <https://docs.djangoproject.com/en/stable/ref/forms/widgets/>`__).


PageChooserBlock
~~~~~~~~~~~~~~~~

``wagtail.core.blocks.PageChooserBlock``

A control for selecting a page object, using Wagtail's page browser. The following keyword arguments are accepted:

``required`` (default: True)
  If true, the field cannot be left blank.

``page_type`` (default: Page)
  Restrict choices to one or more specific page types. Accepts a page model class, model name (as a string), or a list or tuple of these.

``can_choose_root`` (default: False)
  If true, the editor can choose the tree root as a page. Normally this would be undesirable, since the tree root is never a usable page, but in some specialised cases it may be appropriate. For example, a block providing a feed of related articles could use a PageChooserBlock to select which subsection of the site articles will be taken from, with the root corresponding to 'everywhere'.

DocumentChooserBlock
~~~~~~~~~~~~~~~~~~~~

``wagtail.documents.blocks.DocumentChooserBlock``

A control to allow the editor to select an existing document object, or upload a new one. The keyword argument ``required`` (default: True) is accepted.

ImageChooserBlock
~~~~~~~~~~~~~~~~~

``wagtail.images.blocks.ImageChooserBlock``

A control to allow the editor to select an existing image, or upload a new one. The keyword argument ``required`` (default: True) is accepted.

SnippetChooserBlock
~~~~~~~~~~~~~~~~~~~

``wagtail.snippets.blocks.SnippetChooserBlock``

A control to allow the editor to select a snippet object. Requires one positional argument: the snippet class to choose from. The keyword argument ``required`` (default: True) is accepted.

EmbedBlock
~~~~~~~~~~

``wagtail.embeds.blocks.EmbedBlock``

A field for the editor to enter a URL to a media item (such as a YouTube video) to appear as embedded media on the page. The keyword arguments ``required`` (default: True), ``max_length``, ``min_length`` and ``help_text`` are accepted.


.. _streamfield_staticblock:

StaticBlock
~~~~~~~~~~~

``wagtail.core.blocks.StaticBlock``

A block which doesn't have any fields, thus passes no particular values to its template during rendering. This can be useful if you need the editor to be able to insert some content which is always the same or doesn't need to be configured within the page editor, such as an address, embed code from third-party services, or more complex pieces of code if the template uses template tags.

By default, some default text (which contains the ``label`` keyword argument if you pass it) will be displayed in the editor interface, so that the block doesn't look empty. But you can also customise it entirely by passing a text string as the ``admin_text`` keyword argument instead:

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

StructBlock
~~~~~~~~~~~

``wagtail.core.blocks.StructBlock``

A block consisting of a fixed group of sub-blocks to be displayed together. Takes a list of ``(name, block_definition)`` tuples as its first argument:

.. code-block:: python

    ('person', blocks.StructBlock([
        ('first_name', blocks.CharBlock()),
        ('surname', blocks.CharBlock()),
        ('photo', ImageChooserBlock(required=False)),
        ('biography', blocks.RichTextBlock()),
    ], icon='user'))


Alternatively, the list of sub-blocks can be provided in a subclass of StructBlock:

.. code-block:: python

    class PersonBlock(blocks.StructBlock):
        first_name = blocks.CharBlock()
        surname = blocks.CharBlock()
        photo = ImageChooserBlock(required=False)
        biography = blocks.RichTextBlock()

        class Meta:
            icon = 'user'


The ``Meta`` class supports the properties ``default``, ``label``, ``icon`` and ``template``, which have the same meanings as when they are passed to the block's constructor.

This defines ``PersonBlock()`` as a block type that can be re-used as many times as you like within your model definitions:

.. code-block:: python

    body = StreamField([
        ('heading', blocks.CharBlock(form_classname="full title")),
        ('paragraph', blocks.RichTextBlock()),
        ('image', ImageChooserBlock()),
        ('person', PersonBlock()),
    ])

Further options are available for customising the display of a ``StructBlock`` within the page editor - see :ref:`custom_editing_interfaces_for_structblock`.

You can also customise how the value of a ``StructBlock`` is prepared for using in templates - see :ref:`custom_value_class_for_structblock`.



ListBlock
~~~~~~~~~

``wagtail.core.blocks.ListBlock``

A block consisting of many sub-blocks, all of the same type. The editor can add an unlimited number of sub-blocks, and re-order and delete them. Takes the definition of the sub-block as its first argument:

.. code-block:: python

    ('ingredients_list', blocks.ListBlock(blocks.CharBlock(label="Ingredient")))


Any block type is valid as the sub-block type, including structural types:

.. code-block:: python

    ('ingredients_list', blocks.ListBlock(blocks.StructBlock([
        ('ingredient', blocks.CharBlock()),
        ('amount', blocks.CharBlock(required=False)),
    ])))

To customise the class name of a ``ListBlock`` as it appears in the page editor, you can specify a ``form_classname`` attribute as a keyword argument to the ``ListBlock`` constructor:

.. code-block:: python
    :emphasize-lines: 4

    ('ingredients_list', blocks.ListBlock(blocks.StructBlock([
        ('ingredient', blocks.CharBlock()),
        ('amount', blocks.CharBlock(required=False)),
    ]), form_classname='ingredients-list'))

Alternatively, you can add ``form_classname`` in a subclass's ``Meta``:

.. code-block:: python
    :emphasize-lines: 6

    class IngredientsListBlock(blocks.ListBlock):
        ingredient = blocks.CharBlock()
        amount = blocks.CharBlock(required=False)

        class Meta:
            form_classname = 'ingredients-list'


StreamBlock
~~~~~~~~~~~

``wagtail.core.blocks.StreamBlock``

A block consisting of a sequence of sub-blocks of different types, which can be mixed and reordered at will. Used as the overall mechanism of the StreamField itself, but can also be nested or used within other structural block types. Takes a list of ``(name, block_definition)`` tuples as its first argument:

.. code-block:: python

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
    ))


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

.. _streamfield_top_level_streamblock:

Since ``StreamField`` accepts an instance of ``StreamBlock`` as a parameter, in place of a list of block types, this makes it possible to re-use a common set of block types without repeating definitions:

.. code-block:: python

    class HomePage(Page):
        carousel = StreamField(CarouselBlock(max_num=10, block_counts={'video': {'max_num': 2}}))

``StreamBlock`` accepts the following options as either keyword arguments or ``Meta`` properties:

``required`` (default: True)
  If true, at least one sub-block must be supplied. This is ignored when using the ``StreamBlock`` as the top-level block of a StreamField; in this case the StreamField's ``blank`` property is respected instead.

``min_num``
  Minimum number of sub-blocks that the stream must have.

``max_num``
  Maximum number of sub-blocks that the stream may have.

``block_counts``
  Specifies the minimum and maximum number of each block type, as a dictionary mapping block names to dicts with (optional) ``min_num`` and ``max_num`` fields.

``form_classname``
  Customise the class name added to a ``StreamBlock`` form in the page editor.

    .. code-block:: python
        :emphasize-lines: 4

        ('event_promotions', blocks.StreamBlock([
            ('hashtag', blocks.CharBlock()),
            ('post_date', blocks.DateBlock()),
        ], form_classname='event-promotions'))

    .. code-block:: python
        :emphasize-lines: 6

        class EventPromotionsBlock(blocks.StreamBlock):
            hashtag = blocks.CharBlock()
            post_date = blocks.DateBlock()

            class Meta:
                form_classname = 'event-promotions'
