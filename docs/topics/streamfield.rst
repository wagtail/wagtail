.. _streamfield:

Freeform page content using StreamField
=======================================

StreamField provides a content editing model suitable for pages that do not follow a fixed structure -- such as blog posts or news stories -- where the text may be interspersed with subheadings, images, pull quotes and video. It's also suitable for more specialised content types, such as maps and charts (or, for a programming blog, code snippets). In this model, these different content types are represented as a sequence of 'blocks', which can be repeated and arranged in any order.

For further background on StreamField, and why you would use it instead of a rich text field for the article body, see the blog post `Rich text fields and faster horses <https://torchbox.com/blog/rich-text-fields-and-faster-horses/>`__.

StreamField also offers a rich API to define your own block types, ranging from simple collections of sub-blocks (such as a 'person' block consisting of first name, surname and photograph) to completely custom components with their own editing interface. Within the database, the StreamField content is stored as JSON, ensuring that the full informational content of the field is preserved, rather than just an HTML representation of it.


Using StreamField
-----------------

``StreamField`` is a model field that can be defined within your page model like any other field:

.. code-block:: python

    from django.db import models

    from wagtail.wagtailcore.models import Page
    from wagtail.wagtailcore.fields import StreamField
    from wagtail.wagtailcore import blocks
    from wagtail.wagtailadmin.edit_handlers import FieldPanel, StreamFieldPanel
    from wagtail.wagtailimages.blocks import ImageChooserBlock

    class BlogPage(Page):
        author = models.CharField(max_length=255)
        date = models.DateField("Post date")
        body = StreamField([
            ('heading', blocks.CharBlock(classname="full title")),
            ('paragraph', blocks.RichTextBlock()),
            ('image', ImageChooserBlock()),
        ])

        content_panels = Page.content_panels + [
            FieldPanel('author'),
            FieldPanel('date'),
            StreamFieldPanel('body'),
        ]


Note: StreamField is not backwards compatible with other field types such as RichTextField. If you need to migrate an existing field to StreamField, refer to :ref:`streamfield_migrating_richtext`.

The parameter to ``StreamField`` is a list of ``(name, block_type)`` tuples. 'name' is used to identify the block type within templates and the internal JSON representation (and should follow standard Python conventions for variable names: lower-case and underscores, no spaces) and 'block_type' should be a block definition object as described below. (Alternatively, ``StreamField`` can be passed a single ``StreamBlock`` instance - see `Structural block types`_.)

This defines the set of available block types that can be used within this field. The author of the page is free to use these blocks as many times as desired, in any order.

Basic block types
-----------------

All block types accept the following optional keyword arguments:

``default``
  The default value that a new 'empty' block should receive.

``label``
  The label to display in the editor interface when referring to this block - defaults to a prettified version of the block name (or, in a context where no name is assigned - such as within a ``ListBlock`` - the empty string).

``icon``
  The name of the icon to display for this block type in the menu of available block types. For a list of icon names, see the Wagtail style guide, which can be enabled by adding ``wagtail.contrib.wagtailstyleguide`` to your project's ``INSTALLED_APPS``.

``template``
  The path to a Django template that will be used to render this block on the front end. See `Template rendering`_.

``group``
  The group used to categorize this block, i.e. any blocks with the same group name will be shown together in the editor interface with the group name as a heading.

The basic block types provided by Wagtail are as follows:

CharBlock
~~~~~~~~~

``wagtail.wagtailcore.blocks.CharBlock``

A single-line text input. The following keyword arguments are accepted:

``required`` (default: True)
  If true, the field cannot be left blank.

``max_length``, ``min_length``
  Ensures that the string is at most or at least the given length.

``help_text``
  Help text to display alongside the field.

TextBlock
~~~~~~~~~

``wagtail.wagtailcore.blocks.TextBlock``

A multi-line text input. As with ``CharBlock``, the keyword arguments ``required``, ``max_length``, ``min_length`` and ``help_text`` are accepted.

EmailBlock
~~~~~~~~~~

``wagtail.wagtailcore.blocks.EmailBlock``

A single-line email input that validates that the email is a valid Email Address. The keyword arguments ``required`` and ``help_text`` are accepted.

For an example of ``EmailBlock`` in use, see :ref:`streamfield_personblock_example`

IntegerBlock
~~~~~~~~~~~~

``wagtail.wagtailcore.blocks.IntegerBlock``

A single-line integer input that validates that the integer is a valid whole number. The keyword arguments ``required``, ``max_value``, ``min_value`` and ``help_text`` are accepted.

For an example of ``IntegerBlock`` in use, see :ref:`streamfield_personblock_example`

FloatBlock
~~~~~~~~~~

``wagtail.wagtailcore.blocks.FloatBlock``

A single-line Float input that validates that the value is a valid floating point number. The keyword arguments ``required``, ``max_value`` and ``min_value``  are accepted.

DecimalBlock
~~~~~~~~~~~~

``wagtail.wagtailcore.blocks.DecimalBlock``

A single-line decimal input that validates that the value is a valid decimal number. The keyword arguments ``required``, ``max_value``, ``min_value``, ``max_digits`` and ``decimal_places`` are accepted.

For an example of ``DecimalBlock`` in use, see :ref:`streamfield_personblock_example`

RegexBlock
~~~~~~~~~~

``wagtail.wagtailcore.blocks.RegexBlock``

A single-line text input that validates a string against a regex expression. The regular expression used for validation must be supplied as the first argument, or as the keyword argument ``regex``. To customise the message text used to indicate a validation error, pass a dictionary as the keyword argument ``error_messages`` containing either or both of the keys ``required`` (for the message shown on an empty value) or ``invalid`` (for the message shown on a non-matching value):

.. code-block:: python

    blocks.RegexBlock(regex=r'^[0-9]{3}$', error_messages={
        'invalid': "Not a valid library card number."
    })

The keyword arguments ``regex``, ``required``, ``max_length``, ``min_length`` and ``error_messages`` are accepted.

URLBlock
~~~~~~~~

``wagtail.wagtailcore.blocks.URLBlock``

A single-line text input that validates that the string is a valid URL. The keyword arguments ``required``, ``max_length``, ``min_length`` and ``help_text`` are accepted.

BooleanBlock
~~~~~~~~~~~~

``wagtail.wagtailcore.blocks.BooleanBlock``

A checkbox. The keyword arguments ``required`` and ``help_text`` are accepted. As with Django's ``BooleanField``, a value of ``required=True`` (the default) indicates that the checkbox must be ticked in order to proceed. For a checkbox that can be ticked or unticked, you must explicitly pass in ``required=False``.

DateBlock
~~~~~~~~~

``wagtail.wagtailcore.blocks.DateBlock``

A date picker. The keyword arguments ``required``, ``help_text`` and ``format`` are accepted.

``format`` (default: None)
  Date format. This must be one of the recognised formats listed in the `DATE_INPUT_FORMATS <https://docs.djangoproject.com/en/1.10/ref/settings/#std:setting-DATE_INPUT_FORMATS>`_ setting. If not specifed Wagtail will use ``WAGTAIL_DATE_FORMAT`` setting with fallback to '%Y-%m-%d'.

TimeBlock
~~~~~~~~~

``wagtail.wagtailcore.blocks.TimeBlock``

A time picker. The keyword arguments ``required`` and ``help_text`` are accepted.

DateTimeBlock
~~~~~~~~~~~~~

``wagtail.wagtailcore.blocks.DateTimeBlock``

A combined date / time picker. The keyword arguments ``required``, ``help_text`` and ``format`` are accepted.

``format`` (default: None)
  Date format. This must be one of the recognised formats listed in the `DATETIME_INPUT_FORMATS <https://docs.djangoproject.com/en/1.10/ref/settings/#std:setting-DATETIME_INPUT_FORMATS>`_ setting. If not specifed Wagtail will use ``WAGTAIL_DATETIME_FORMAT`` setting with fallback to '%Y-%m-%d %H:%M'.

RichTextBlock
~~~~~~~~~~~~~

``wagtail.wagtailcore.blocks.RichTextBlock``

A WYSIWYG editor for creating formatted text including links, bold / italics etc.

RawHTMLBlock
~~~~~~~~~~~~

``wagtail.wagtailcore.blocks.RawHTMLBlock``

A text area for entering raw HTML which will be rendered unescaped in the page output. The keyword arguments ``required``, ``max_length``, ``min_length`` and ``help_text`` are accepted.

.. WARNING::
   When this block is in use, there is nothing to prevent editors from inserting malicious scripts into the page, including scripts that would allow the editor to acquire administrator privileges when another administrator views the page. Do not use this block unless your editors are fully trusted.

BlockQuoteBlock
~~~~~~~~~~~~~~~

``wagtail.wagtailcore.blocks.BlockQuoteBlock``

A text field, the contents of which will be wrapped in an HTML `<blockquote>` tag pair. The keyword arguments ``required``, ``max_length``, ``min_length`` and ``help_text`` are accepted.


ChoiceBlock
~~~~~~~~~~~

``wagtail.wagtailcore.blocks.ChoiceBlock``

A dropdown select box for choosing from a list of choices. The following keyword arguments are accepted:

``choices``
  A list of choices, in any format accepted by Django's ``choices`` parameter for model fields (https://docs.djangoproject.com/en/stable/ref/models/fields/#field-choices), or a callable returning such a list.

``required`` (default: True)
  If true, the field cannot be left blank.

``help_text``
  Help text to display alongside the field.

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

PageChooserBlock
~~~~~~~~~~~~~~~~

``wagtail.wagtailcore.blocks.PageChooserBlock``

A control for selecting a page object, using Wagtail's page browser. The following keyword arguments are accepted:

``required`` (default: True)
  If true, the field cannot be left blank.

``target_model`` (default: Page)
  Restrict choices to one or more specific page types. Accepts a page model class, model name (as a string), or a list or tuple of these.

``can_choose_root`` (default: False)
  If true, the editor can choose the tree root as a page. Normally this would be undesirable, since the tree root is never a usable page, but in some specialised cases it may be appropriate. For example, a block providing a feed of related articles could use a PageChooserBlock to select which subsection of the site articles will be taken from, with the root corresponding to 'everywhere'.

DocumentChooserBlock
~~~~~~~~~~~~~~~~~~~~

``wagtail.wagtaildocs.blocks.DocumentChooserBlock``

A control to allow the editor to select an existing document object, or upload a new one. The keyword argument ``required`` is accepted.

ImageChooserBlock
~~~~~~~~~~~~~~~~~

``wagtail.wagtailimages.blocks.ImageChooserBlock``

A control to allow the editor to select an existing image, or upload a new one. The keyword argument ``required`` is accepted.

SnippetChooserBlock
~~~~~~~~~~~~~~~~~~~

``wagtail.wagtailsnippets.blocks.SnippetChooserBlock``

A control to allow the editor to select a snippet object. Requires one positional argument: the snippet class to choose from. The keyword argument ``required`` is accepted.

EmbedBlock
~~~~~~~~~~

``wagtail.wagtailembeds.blocks.EmbedBlock``

A field for the editor to enter a URL to a media item (such as a YouTube video) to appear as embedded media on the page. The keyword arguments ``required``, ``max_length``, ``min_length`` and ``help_text`` are accepted.


.. _streamfield_staticblock:

StaticBlock
~~~~~~~~~~~

``wagtail.wagtailcore.blocks.StaticBlock``

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


Structural block types
----------------------

In addition to the basic block types above, it is possible to define new block types made up of sub-blocks: for example, a 'person' block consisting of sub-blocks for first name, surname and image, or a 'carousel' block consisting of an unlimited number of image blocks. These structures can be nested to any depth, making it possible to have a structure containing a list, or a list of structures.

StructBlock
~~~~~~~~~~~

``wagtail.wagtailcore.blocks.StructBlock``

A block consisting of a fixed group of sub-blocks to be displayed together. Takes a list of ``(name, block_definition)`` tuples as its first argument:

.. code-block:: python

    ('person', blocks.StructBlock([
        ('first_name', blocks.CharBlock(required=True)),
        ('surname', blocks.CharBlock(required=True)),
        ('photo', ImageChooserBlock()),
        ('biography', blocks.RichTextBlock()),
    ], icon='user'))


Alternatively, the list of sub-blocks can be provided in a subclass of StructBlock:

.. code-block:: python

    class PersonBlock(blocks.StructBlock):
        first_name = blocks.CharBlock(required=True)
        surname = blocks.CharBlock(required=True)
        photo = ImageChooserBlock()
        biography = blocks.RichTextBlock()

        class Meta:
            icon = 'user'


The ``Meta`` class supports the properties ``default``, ``label``, ``icon`` and ``template``, which have the same meanings as when they are passed to the block's constructor.

This defines ``PersonBlock()`` as a block type that can be re-used as many times as you like within your model definitions:

.. code-block:: python

    body = StreamField([
        ('heading', blocks.CharBlock(classname="full title")),
        ('paragraph', blocks.RichTextBlock()),
        ('image', ImageChooserBlock()),
        ('person', PersonBlock()),
    ])

Further options are available for customising the display of a ``StructBlock`` within the page editor - see :ref:`custom_editing_interfaces_for_structblock`.


ListBlock
~~~~~~~~~

``wagtail.wagtailcore.blocks.ListBlock``

A block consisting of many sub-blocks, all of the same type. The editor can add an unlimited number of sub-blocks, and re-order and delete them. Takes the definition of the sub-block as its first argument:

.. code-block:: python

    ('ingredients_list', blocks.ListBlock(blocks.CharBlock(label="Ingredient")))


Any block type is valid as the sub-block type, including structural types:

.. code-block:: python

    ('ingredients_list', blocks.ListBlock(blocks.StructBlock([
        ('ingredient', blocks.CharBlock(required=True)),
        ('amount', blocks.CharBlock()),
    ])))


StreamBlock
~~~~~~~~~~~

``wagtail.wagtailcore.blocks.StreamBlock``

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


Since ``StreamField`` accepts an instance of ``StreamBlock`` as a parameter, in place of a list of block types, this makes it possible to re-use a common set of block types without repeating definitions:

.. code-block:: python

    class HomePage(Page):
        carousel = StreamField(CarouselBlock())


.. _streamfield_personblock_example:

Example: ``PersonBlock``
------------------------

This example demonstrates how the basic block types introduced above can be combined into a more complex block type based on ``StructBlock``:

.. code-block:: python

    from wagtail.wagtailcore import blocks

    class PersonBlock(blocks.StructBlock):
        name = blocks.CharBlock()
        height = blocks.DecimalBlock()
        age = blocks.IntegerBlock()
        email = blocks.EmailBlock()

        class Meta:
            template = 'blocks/person_block.html'


.. _streamfield_template_rendering:

Template rendering
------------------

StreamField provides an HTML representation for the stream content as a whole, as well as for each individual block. To include this HTML into your page, use the ``{% include_block %}`` tag:

.. code-block:: html+django

    {% load wagtailcore_tags %}

     ...

    {% include_block page.body %}


In the default rendering, each block of the stream is wrapped in a ``<div class="block-my_block_name">`` element (where ``my_block_name`` is the block name given in the StreamField definition). If you wish to provide your own HTML markup, you can instead iterate over the field's value, and invoke ``{% include_block %}`` on each block in turn:

.. code-block:: html+django

    {% load wagtailcore_tags %}

     ...

    <article>
        {% for block in page.body %}
            <section>{% include_block block %}</section>
        {% endfor %}
    </article>


For more control over the rendering of specific block types, each block object provides ``block_type`` and ``value`` properties:

.. code-block:: html+django

    {% load wagtailcore_tags %}

     ...

    <article>
        {% for block in page.body %}
            {% if block.block_type == 'heading' %}
                <h1>{{ block.value }}</h1>
            {% else %}
                <section class="block-{{ block.block_type }}">
                    {% include_block block %}
                </section>
            {% endif %}
        {% endfor %}
    </article>


By default, each block is rendered using simple, minimal HTML markup, or no markup at all. For example, a CharBlock value is rendered as plain text, while a ListBlock outputs its child blocks in a `<ul>` wrapper. To override this with your own custom HTML rendering, you can pass a ``template`` argument to the block, giving the filename of a template file to be rendered. This is particularly useful for custom block types derived from StructBlock:

.. code-block:: python

    ('person', blocks.StructBlock(
        [
            ('first_name', blocks.CharBlock(required=True)),
            ('surname', blocks.CharBlock(required=True)),
            ('photo', ImageChooserBlock()),
            ('biography', blocks.RichTextBlock()),
        ],
        template='myapp/blocks/person.html',
        icon='user'
    ))


Or, when defined as a subclass of StructBlock:

.. code-block:: python

    class PersonBlock(blocks.StructBlock):
        first_name = blocks.CharBlock(required=True)
        surname = blocks.CharBlock(required=True)
        photo = ImageChooserBlock()
        biography = blocks.RichTextBlock()

        class Meta:
            template = 'myapp/blocks/person.html'
            icon = 'user'


Within the template, the block value is accessible as the variable ``value``:

.. code-block:: html+django

    {% load wagtailimages_tags %}

    <div class="person">
        {% image value.photo width-400 %}
        <h2>{{ value.first_name }} {{ value.surname }}</h2>
        {{ value.biography }}
    </div>

Since ``first_name``, ``surname``, ``photo`` and ``biography`` are defined as blocks in their own right, this could also be written as:

.. code-block:: html+django

    {% load wagtailcore_tags wagtailimages_tags %}

    <div class="person">
        {% image value.photo width-400 %}
        <h2>{% include_block value.first_name %} {% include_block value.surname %}</h2>
        {% include_block value.biography %}
    </div>

Writing ``{{ my_block }}`` is roughly equivalent to ``{% include_block my_block %}``, but the short form is more restrictive, as it does not pass variables from the calling template such as ``request`` or ``page``; for this reason, it is recommended that you only use it for simple values that do not render HTML of their own. For example, if our PersonBlock used the template:

.. code-block:: html+django

    {% load wagtailimages_tags %}

    <div class="person">
        {% image value.photo width-400 %}
        <h2>{{ value.first_name }} {{ value.surname }}</h2>

        {% if request.user.is_authenticated %}
            <a href="#">Contact this person</a>
        {% endif %}

        {{ value.biography }}
    </div>

then the ``request.user.is_authenticated`` test would not work correctly when rendering the block through a ``{{ ... }}`` tag:

.. code-block:: html+django

    {# Incorrect: #}

    {% for block in page.body %}
        {% if block.block_type == 'person' %}
            <div>
                {{ block }}
            </div>
        {% endif %}
    {% endfor %}

    {# Correct: #}

    {% for block in page.body %}
        {% if block.block_type == 'person' %}
            <div>
                {% include_block block %}
            </div>
        {% endif %}
    {% endfor %}

Like Django's ``{% include %}`` tag, ``{% include_block %}`` also allows passing additional variables to the included template, through the syntax ``{% include_block my_block with foo="bar" %}``:

.. code-block:: html+django

    {# In page template: #}

    {% for block in page.body %}
        {% if block.block_type == 'person' %}
            {% include_block block with classname="important" %}
        {% endif %}
    {% endfor %}

    {# In PersonBlock template: #}

    <div class="{{ classname }}">
        ...
    </div>

The syntax ``{% include_block my_block with foo="bar" only %}`` is also supported, to specify that no variables from the parent template other than ``foo`` will be passed to the child template.

.. _streamfield_get_context:

As well as passing variables from the parent template, block subclasses can pass additional template variables of their own by overriding the ``get_context`` method:

.. code-block:: python

    import datetime

    class EventBlock(blocks.StructBlock):
        title = blocks.CharBlock(required=True)
        date = blocks.DateBlock(required=True)

        def get_context(self, value, parent_context=None):
            context = super(EventBlock, self).get_context(value, parent_context=parent_context)
            context['is_happening_today'] = (value['date'] == datetime.date.today())
            return context

        class Meta:
            template = 'myapp/blocks/event.html'


In this example, the variable ``is_happening_today`` will be made available within the block template. The ``parent_context`` keyword argument is available when the block is rendered through an ``{% include_block %}`` tag, and is a dict of variables passed from the calling template.


BoundBlocks and values
----------------------

All block types, not just StructBlock, accept a ``template`` parameter to determine how they will be rendered on a page. However, for blocks that handle basic Python data types, such as ``CharBlock`` and ``IntegerBlock``, there are some limitations on where the template will take effect, since those built-in types (``str``, ``int`` and so on) cannot be 'taught' about their template rendering. As an example of this, consider the following block definition:

.. code-block:: python

    class HeadingBlock(blocks.CharBlock):
        class Meta:
            template = 'blocks/heading.html'

where ``blocks/heading.html`` consists of:

.. code-block:: html+django

    <h1>{{ value }}</h1>

This gives us a block that behaves as an ordinary text field, but wraps its output in ``<h1>`` tags whenever it is rendered:

.. code-block:: python

    class BlogPage(Page):
        body = StreamField([
            # ...
            ('heading', HeadingBlock()),
            # ...
        ])

.. code-block:: html+django

    {% load wagtailcore_tags %}

    {% for block in page.body %}
        {% if block.block_type == 'heading' %}
            {% include_block block %}  {# This block will output its own <h1>...</h1> tags. #}
        {% endif %}
    {% endfor %}

This kind of arrangement - a value that supposedly represents a plain text string, but has its own custom HTML representation when output on a template - would normally be a very messy thing to achieve in Python, but it works here because the items you get when iterating over a StreamField are not actually the 'native' values of the blocks. Instead, each item is returned as an instance of ``BoundBlock`` - an object that represents the pairing of a value and its block definition. By keeping track of the block definition, a ``BoundBlock`` always knows which template to render. To get to the underlying value - in this case, the text content of the heading - you would need to access ``block.value``. Indeed, if you were to output ``{% include_block block.value %}`` on the page, you would find that it renders as plain text, without the ``<h1>`` tags.

(More precisely, the items returned when iterating over a StreamField are instances of a class ``StreamChild``, which provides the ``block_type`` property as well as ``value``.)

Experienced Django developers may find it helpful to compare this to the ``BoundField`` class in Django's forms framework, which represents the pairing of a form field value with its corresponding form field definition, and therefore knows how to render the value as an HTML form field.

Most of the time, you won't need to worry about these internal details; Wagtail will use the template rendering wherever you would expect it to. However, there are certain cases where the illusion isn't quite complete - namely, when accessing children of a ``ListBlock`` or ``StructBlock``. In these cases, there is no ``BoundBlock`` wrapper, and so the item cannot be relied upon to know its own template rendering. For example, consider the following setup, where our ``HeadingBlock`` is a child of a StructBlock:

.. code-block:: python

    class EventBlock(blocks.StructBlock):
        heading = HeadingBlock()
        description = blocks.TextBlock()
        # ...

        class Meta:
            template = 'blocks/event.html'

In ``blocks/event.html``:

.. code-block:: html+django

    {% load wagtailcore_tags %}

    <div class="event {% if value.heading == 'Party!' %}lots-of-balloons{% endif %}">
        {% include_block value.heading %}
        - {% include_block value.description %}
    </div>

In this case, ``value.heading`` returns the plain string value rather than a ``BoundBlock``; this is necessary because otherwise the comparison in ``{% if value.heading == 'Party!' %}`` would never succeed. This in turn means that ``{% include_block value.heading %}`` renders as the plain string, without the ``<h1>`` tags. To get the HTML rendering, you need to explicitly access the ``BoundBlock`` instance through ``value.bound_blocks.heading``:

.. code-block:: html+django

    {% load wagtailcore_tags %}

    <div class="event {% if value.heading == 'Party!' %}lots-of-balloons{% endif %}">
        {% include_block value.bound_blocks.heading %}
        - {% include_block value.description %}
    </div>

In practice, it would probably be more natural and readable to make the ``<h1>`` tag explicit in the EventBlock's template:

.. code-block:: html+django

    {% load wagtailcore_tags %}

    <div class="event {% if value.heading == 'Party!' %}lots-of-balloons{% endif %}">
        <h1>{{ value.heading }}</h1>
        - {% include_block value.description %}
    </div>

This limitation does not apply to StructBlock and StreamBlock values as children of a StructBlock, because Wagtail implements these as complex objects that know their own template rendering, even when not wrapped in a ``BoundBlock``. For example, if a StructBlock is nested in another StructBlock, as in:

.. code-block:: python

    class EventBlock(blocks.StructBlock):
        heading = HeadingBlock()
        description = blocks.TextBlock()
        guest_speaker = blocks.StructBlock([
            ('first_name', blocks.CharBlock()),
            ('surname', blocks.CharBlock()),
            ('photo', ImageChooserBlock()),
        ], template='blocks/speaker.html')

then ``{% include_block value.guest_speaker %}`` within the EventBlock's template will pick up the template rendering from ``blocks/speaker.html`` as intended.

In summary, interactions between BoundBlocks and plain values work according to the following rules:

1. When iterating over the value of a StreamField or StreamBlock (as in ``{% for block in page.body %}``), you will get back a sequence of BoundBlocks.
2. If you have a BoundBlock instance, you can access the plain value as ``block.value``.
3. Accessing a child of a StructBlock (as in ``value.heading``) will return a plain value; to retrieve the BoundBlock instead, use ``value.bound_blocks.heading``.
4. The value of a ListBlock is a plain Python list; iterating over it returns plain child values.
5. StructBlock and StreamBlock values always know how to render their own templates, even if you only have the plain value rather than the BoundBlock.


.. _custom_editing_interfaces_for_structblock:

Custom editing interfaces for ``StructBlock``
---------------------------------------------

To customise the styling of a ``StructBlock`` as it appears in the page editor, you can specify a ``form_classname`` attribute (either as a keyword argument to the ``StructBlock`` constructor, or in a subclass's ``Meta``) to override the default value of ``struct-block``:

.. code-block:: python

    class PersonBlock(blocks.StructBlock):
        first_name = blocks.CharBlock(required=True)
        surname = blocks.CharBlock(required=True)
        photo = ImageChooserBlock()
        biography = blocks.RichTextBlock()

        class Meta:
            icon = 'user'
            form_classname = 'person-block struct-block'


You can then provide custom CSS for this block, targeted at the specified classname, by using the :ref:`insert_editor_css` hook.

For more extensive customisations that require changes to the HTML markup as well, you can override the ``form_template`` attribute in ``Meta`` to specify your own template path. The following variables are available on this template:

``children``
  An ``OrderedDict`` of ``BoundBlock``\s for all of the child blocks making up this ``StructBlock``; typically your template will call ``render_form`` on each of these.

``help_text``
  The help text for this block, if specified.

``classname``
  The class name passed as ``form_classname`` (defaults to ``struct-block``).

``block_definition``
  The ``StructBlock`` instance that defines this block.

``prefix``
  The prefix used on form fields for this block instance, guaranteed to be unique across the form.

To add additional variables, you can override the block's ``get_form_context`` method:

.. code-block:: python

    class PersonBlock(blocks.StructBlock):
        first_name = blocks.CharBlock(required=True)
        surname = blocks.CharBlock(required=True)
        photo = ImageChooserBlock()
        biography = blocks.RichTextBlock()

        def get_form_context(self, value, prefix='', errors=None):
            context = super(PersonBlock, self).get_form_context(value, prefix=prefix, errors=errors)
            context['suggested_first_names'] = ['John', 'Paul', 'George', 'Ringo']
            return context

        class Meta:
            icon = 'user'
            form_template = 'myapp/block_forms/person.html'


Custom block types
------------------

If you need to implement a custom UI, or handle a datatype that is not provided by Wagtail's built-in block types (and cannot built up as a structure of existing fields), it is possible to define your own custom block types. For further guidance, refer to the source code of Wagtail's built-in block classes.

For block types that simply wrap an existing Django form field, Wagtail provides an abstract class ``wagtail.wagtailcore.blocks.FieldBlock`` as a helper. Subclasses just need to set a ``field`` property that returns the form field object:

.. code-block:: python

    class IPAddressBlock(FieldBlock):
        def __init__(self, required=True, help_text=None, **kwargs):
            self.field = forms.GenericIPAddressField(required=required, help_text=help_text)
            super(IPAddressBlock, self).__init__(**kwargs)


Migrations
----------

StreamField definitions within migrations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

As with any model field in Django, any changes to a model definition that affect a StreamField will result in a migration file that contains a 'frozen' copy of that field definition. Since a StreamField definition is more complex than a typical model field, there is an increased likelihood of definitions from your project being imported into the migration -- which would cause problems later on if those definitions are moved or deleted.

To mitigate this, StructBlock, StreamBlock and ChoiceBlock implement additional logic to ensure that any subclasses of these blocks are deconstructed to plain instances of StructBlock, StreamBlock and ChoiceBlock -- in this way, the migrations avoid having any references to your custom class definitions. This is possible because these block types provide a standard pattern for inheritance, and know how to reconstruct the block definition for any subclass that follows that pattern.

If you subclass any other block class, such as ``FieldBlock``, you will need to either keep that class definition in place for the lifetime of your project, or implement a `custom deconstruct method <https://docs.djangoproject.com/en/1.9/topics/migrations/#custom-deconstruct-method>`__ that expresses your block entirely in terms of classes that are guaranteed to remain in place. Similarly, if you customise a StructBlock, StreamBlock or ChoiceBlock subclass to the point where it can no longer be expressed as an instance of the basic block type -- for example, if you add extra arguments to the constructor -- you will need to provide your own ``deconstruct`` method.

.. _streamfield_migrating_richtext:

Migrating RichTextFields to StreamField
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you change an existing RichTextField to a StreamField, and create and run migrations as normal, the migration will complete with no errors, since both fields use a text column within the database. However, StreamField uses a JSON representation for its data, so the existing text needs to be converted with a data migration in order to become accessible again. For this to work, the StreamField needs to include a RichTextBlock as one of the available block types. The field can then be converted by creating a new migration (``./manage.py makemigrations --empty myapp``) and editing it as follows (in this example, the 'body' field of the ``demo.BlogPage`` model is being converted to a StreamField with a RichTextBlock named ``rich_text``):

.. code-block:: python

    # -*- coding: utf-8 -*-
    from __future__ import unicode_literals

    from django.db import models, migrations
    from wagtail.wagtailcore.rich_text import RichText


    def convert_to_streamfield(apps, schema_editor):
        BlogPage = apps.get_model("demo", "BlogPage")
        for page in BlogPage.objects.all():
            if page.body.raw_text and not page.body:
                page.body = [('rich_text', RichText(page.body.raw_text))]
                page.save()


    def convert_to_richtext(apps, schema_editor):
        BlogPage = apps.get_model("demo", "BlogPage")
        for page in BlogPage.objects.all():
            if page.body.raw_text is None:
                raw_text = ''.join([
                    child.value.source for child in page.body
                    if child.block_type == 'rich_text'
                ])
                page.body = raw_text
                page.save()


    class Migration(migrations.Migration):

        dependencies = [
            # leave the dependency line from the generated migration intact!
            ('demo', '0001_initial'),
        ]

        operations = [
            migrations.RunPython(
                convert_to_streamfield,
                convert_to_richtext,
            ),
        ]


Note that the above migration will work on published Page objects only. If you also need to migrate draft pages and page revisions, then edit your new data migration as in the following example instead:

.. code-block:: python

    # -*- coding: utf-8 -*-
    from __future__ import unicode_literals

    import json

    from django.core.serializers.json import DjangoJSONEncoder
    from django.db import migrations, models

    from wagtail.wagtailcore.rich_text import RichText


    def page_to_streamfield(page):
        changed = False
        if page.body.raw_text and not page.body:
            page.body = [('rich_text', {'rich_text': RichText(page.body.raw_text)})]
            changed = True
        return page, changed


    def pagerevision_to_streamfield(revision_data):
        changed = False
        body = revision_data.get('body')
        if body:
            try:
                json.loads(body)
            except ValueError:
                revision_data['body'] = json.dumps(
                    [{
                        "value": {"rich_text": body},
                        "type": "rich_text"
                    }],
                    cls=DjangoJSONEncoder)
                changed = True
            else:
                # It's already valid JSON. Leave it.
                pass
        return revision_data, changed


    def page_to_richtext(page):
        changed = False
        if page.body.raw_text is None:
            raw_text = ''.join([
                child.value['rich_text'].source for child in page.body
                if child.block_type == 'rich_text'
            ])
            page.body = raw_text
            changed = True
        return page, changed


    def pagerevision_to_richtext(revision_data):
        changed = False
        body = revision_data.get('body', 'definitely non-JSON string')
        if body:
            try:
                body_data = json.loads(body)
            except ValueError:
                # It's not apparently a StreamField. Leave it.
                pass
            else:
                raw_text = ''.join([
                    child['value']['rich_text'] for child in body_data
                    if child['type'] == 'rich_text'
                ])
                revision_data['body'] = raw_text
                changed = True
        return revision_data, changed


    def convert(apps, schema_editor, page_converter, pagerevision_converter):
        BlogPage = apps.get_model("demo", "BlogPage")
        for page in BlogPage.objects.all():

            page, changed = page_converter(page)
            if changed:
                page.save()

            for revision in page.revisions.all():
                revision_data = json.loads(revision.content_json)
                revision_data, changed = pagerevision_converter(revision_data)
                if changed:
                    revision.content_json = json.dumps(revision_data, cls=DjangoJSONEncoder)
                    revision.save()


    def convert_to_streamfield(apps, schema_editor):
        return convert(apps, schema_editor, page_to_streamfield, pagerevision_to_streamfield)


    def convert_to_richtext(apps, schema_editor):
        return convert(apps, schema_editor, page_to_richtext, pagerevision_to_richtext)


    class Migration(migrations.Migration):

        dependencies = [
            # leave the dependency line from the generated migration intact!
            ('demo', '0001_initial'),
        ]

        operations = [
            migrations.RunPython(
                convert_to_streamfield,
                convert_to_richtext,
            ),
        ]
