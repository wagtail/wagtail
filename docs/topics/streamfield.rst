.. _streamfield:

Freeform page content using StreamField
=======================================

StreamField provides a content editing model suitable for pages that do not follow a fixed structure - such as blog posts or news stories, where the text may be interspersed with subheadings, images, pull quotes and video, and perhaps more specialised content types such as maps and charts (or, for a programming blog, code snippets). In this model, these different content types are represented as a sequence of 'blocks', which can be repeated and arranged in any order.

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


Note: StreamField is not backwards compatible with other field types such as RichTextField; if you migrate an existing field to StreamField, the existing data will be lost.

The parameter to ``StreamField`` is a list of (name, block_type) tuples; 'name' is used to identify the block type within templates and the internal JSON representation (and should follow standard Python conventions for variable names: lower-case and underscores, no spaces) and 'block_type' should be a block definition object as described below. (Alternatively, ``StreamField`` can be passed a single ``StreamBlock`` instance - see `Structural block types`_.)

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

URLBlock
~~~~~~~~

``wagtail.wagtailcore.blocks.URLBlock``

A single-line text input that validates that the string is a valid URL. The keyword arguments ``required``, ``max_length``, ``min_length`` and ``help_text`` are accepted.

BooleanBlock
~~~~~~~~~~~~

``wagtail.wagtailcore.blocks.BooleanBlock``

A checkbox. The keyword arguments ``required`` and ``help_text`` are accepted. As with Django's ``BooleanField``, a value of ``required=True`` (the default) indicates that the checkbox must be ticked in order to proceed; for a checkbox that can be ticked or unticked, you must explicitly pass in ``required=False``.

DateBlock
~~~~~~~~~

``wagtail.wagtailcore.blocks.DateBlock``

A date picker. The keyword arguments ``required`` and ``help_text`` are accepted.

TimeBlock
~~~~~~~~~

``wagtail.wagtailcore.blocks.TimeBlock``

A time picker. The keyword arguments ``required`` and ``help_text`` are accepted.

DateTimeBlock
~~~~~~~~~~~~~

``wagtail.wagtailcore.blocks.DateTimeBlock``

A combined date / time picker. The keyword arguments ``required`` and ``help_text`` are accepted.

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

ChoiceBlock
~~~~~~~~~~~

``wagtail.wagtailcore.blocks.ChoiceBlock``

A dropdown select box for choosing from a list of choices. The following keyword arguments are accepted:

``choices``
  A list of choices, in any format accepted by Django's ``choices`` parameter for model fields: https://docs.djangoproject.com/en/stable/ref/models/fields/#field-choices

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


``StreamField`` definitions can then refer to ``DrinksChoiceBlock()`` in place of the full ``ChoiceBlock`` definition.

PageChooserBlock
~~~~~~~~~~~~~~~~

``wagtail.wagtailcore.blocks.PageChooserBlock``

A control for selecting a page object, using Wagtail's page browser. The following keyword arguments are accepted:

``required`` (default: True)
  If true, the field cannot be left blank.

``can_choose_root`` (default: False)
  If true, the editor can choose the tree root as a page. Normally this would be undesirable, since the tree root is never a usable page, but in some specialised cases it may be appropriate; for example, a block providing a feed of related articles could use a PageChooserBlock to select which subsection articles will be taken from, with the root corresponding to 'everywhere'.

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


Structural block types
----------------------

In addition to the basic block types above, it is possible to define new block types made up of sub-blocks: for example, a 'person' block consisting of sub-blocks for first name, surname and image, or a 'carousel' block consisting of an unlimited number of image blocks. These structures can be nested to any depth, making it possible to have a structure containing a list, or a list of structures.

StructBlock
~~~~~~~~~~~

``wagtail.wagtailcore.blocks.StructBlock``

A block consisting of a fixed group of sub-blocks to be displayed together. Takes a list of (name, block_definition) tuples as its first argument:

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


The ``Meta`` class supports the properties ``default``, ``label``, ``icon`` and ``template``; these have the same meanings as when they are passed to the block's constructor.

This defines ``PersonBlock()`` as a block type that can be re-used as many times as you like within your model definitions:

.. code-block:: python

    body = StreamField([
        ('heading', blocks.CharBlock(classname="full title")),
        ('paragraph', blocks.RichTextBlock()),
        ('image', ImageChooserBlock()),
        ('person', PersonBlock()),
    ])


To customise the styling of the block as it appears in the page editor, your subclass can specify a ``form_classname`` attribute in ``Meta`` to override the default value of ``struct-block``:

.. code-block:: python

    class PersonBlock(blocks.StructBlock):
        first_name = blocks.CharBlock(required=True)
        surname = blocks.CharBlock(required=True)
        photo = ImageChooserBlock()
        biography = blocks.RichTextBlock()

        class Meta:
            icon = 'user'
            form_classname = 'person-block struct-block'


You can then provide custom CSS for this block, targeted at the specified classname, by using the ``insert_editor_css`` hook (see :doc:`Hooks </reference/hooks>`). For more extensive customisations that require changes to the HTML markup as well, you can override the ``form_template`` attribute in ``Meta``.


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

A block consisting of a sequence of sub-blocks of different types, which can be mixed and reordered in any order. Used as the overall mechanism of the StreamField itself, but can also be nested or used within other structural block types. Takes a list of (name, block_definition) tuples as its first argument:

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


Since ``StreamField`` accepts an instance of ``StreamBlock`` as a parameter, in place of a list of block types, this makes it possible to re-use a common set block types without repeating definitions:

.. code-block:: python

    class HomePage(Page):
        carousel = StreamField(CarouselBlock())


Template rendering
------------------

The simplest way to render the contents of a StreamField into your template is to output it as a variable, like any other field:

.. code-block:: html+django

    {{ page.body }}


This will render each block of the stream in turn, wrapped in a ``<div class="block-my_block_name">`` element (where ``my_block_name`` is the block name given in the StreamField definition). If you wish to provide your own HTML markup, you can instead iterate over the field's value to access each block in turn:

.. code-block:: html+django

    <article>
        {% for block in page.body %}
            <section>{{ block }}</section>
        {% endfor %}
    </article>


For more control over the rendering of specific block types, each block object provides ``block_type`` and ``value`` properties:

.. code-block:: html+django

    <article>
        {% for block in page.body %}
            {% if block.block_type == 'heading' %}
                <h1>{{ block.value }}</h1>
            {% else %}
                <section class="block-{{ block.block_type }}">
                    {{ block }}
                </section>
            {% endif %}
        {% endfor %}
    </article>


Each block type provides its own front-end HTML rendering mechanism, and this is used for the output of ``{{ block }}``. For most simple block types, such as CharBlock, this will simply output the field's value, but others will provide their own HTML markup; for example, a ListBlock will output the list of child blocks as a ``<ul>`` element (with each child wrapped in an ``<li>`` element and rendered using the child block's own HTML rendering).

To override this with your own custom HTML rendering, you can pass a ``template`` argument to the block, giving the filename of a template file to be rendered. This is particularly useful for custom block types derived from StructBlock, as the default StructBlock rendering is simple and somewhat generic:

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


.. _streamfield_get_context:

To pass additional context variables to the template, block subclasses can override the ``get_context`` method:

.. code-block:: python

    import datetime

    class EventBlock(blocks.StructBlock):
        title = blocks.CharBlock(required=True)
        date = blocks.DateBlock(required=True)

        def get_context(self, value):
            context = super(EventBlock, self).get_context(value)
            context['is_happening_today'] = (value['date'] == datetime.date.today())
            return context

        class Meta:
            template = 'myapp/blocks/event.html'


In this example, the variable ``is_happening_today`` will be made available within the block template.


BoundBlocks and values
----------------------

As you've seen above, it's possible to assign a particular template rendering to a block. This can be done on any block type, not just StructBlocks - however, there are some extra details to be aware of. Consider the following block definition:

.. code-block:: python

    class HeadingBlock(blocks.CharBlock):
        class Meta:
            template = 'blocks/heading.html'

where blocks/heading.html consists of:

.. code-block:: html+django

    <h1>{{ value }}</h1>

This gives us a block that behaves as an ordinary text field, but wraps its output in ``<h1>`` tags whenever it is rendered:

.. code-block:: python

    class BlogPage(Page):
        body = StreamField([
            # ...
            'heading': HeadingBlock(),
            # ...
        ])

.. code-block:: html+django

    {% for block in page.body %}
        {% if block.block_type == 'heading' %}
            {{ block }}  {# this block will output its own <h1>...</h1> tags #}
        {% endif %}
    {% endfor %}

This is a powerful feature, but it involves some complexity behind the scenes to make it work. Effectively, HeadingBlock has a double identity - logically it represents a plain Python string value, but in circumstances such as this it needs to yield a 'magic' object that knows its own custom HTML representation. This 'magic' object is an instance of ``BoundBlock`` - an object that represents the pairing of a value and its block definition. (Django developers may recognise this as the same principle behind ``BoundField`` in Django's forms framework.)

Most of the time, you won't need to worry about whether you're dealing with a plain value or a BoundBlock; you can trust Wagtail to do the right thing. However, there are certain cases where the distinction becomes important. For example, consider the following setup:

.. code-block:: python

    class EventBlock(blocks.StructBlock):
        heading = HeadingBlock()
        description = blocks.TextBlock()
        # ...

        class Meta:
            template = 'blocks/event.html'

where blocks/event.html is:

.. code-block:: html+django

    <div class="event {% if value.heading == 'Party!' %}lots-of-balloons{% endif %}">
        {{ value.heading }}
        - {{ value.description }}
    </div>

In this case, ``value.heading`` returns the plain string value; if this weren't the case, the comparison in ``{% if value.heading == 'Party!' %}`` would never succeed. This in turn means that ``{{ value.heading }}`` renders as the plain string, without the ``<h1>`` tags.

Interactions between BoundBlocks and plain values work according to the following rules:

1. When iterating over the value of a StreamField or StreamBlock (as in ``{% for block in page.body %}``), you will get back a sequence of BoundBlocks.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This means that ``{{ block }}`` will always render using the block's own template, if one is supplied. More specifically, these ``block`` objects will be instances of StreamChild, which additionally provides the ``block_type`` property.

2. If you have a BoundBlock instance, you can access the plain value as ``block.value``.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For example, if you had a particular page template where you wanted HeadingBlock to display as ``<h2>`` rather than ``<h1>``, you could write:

.. code-block:: html+django

    {% for block in page.body %}
        {% if block.block_type == 'heading' %}
            <h2>{{ block.value }}</h2>
        {% endif %}
    {% endfor %}

3. Accessing a child of a StructBlock (as in ``value.heading``) will return a plain value; to retrieve the BoundBlock instead, use ``value.bound_blocks.heading``.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This ensures that template tags such as ``{% if value.heading == 'Party!' %}`` and ``{% image value.photo fill-320x200 %}`` work as expected. The event template above could be rewritten as follows to access the HeadingBlock content as a BoundBlock and use its own HTML representation (with ``<h1>`` tags included):

.. code-block:: html+django

    <div class="event {% if value.heading == 'Party!' %}lots-of-balloons{% endif %}">
        {{ value.bound_block.heading }}
        {{ value.description }}
    </div>

However, in this case it's probably more readable to make the ``<h1>`` tag explicit in the EventBlock's template:

.. code-block:: html+django

    <div class="event {% if value.heading == 'Party!' %}lots-of-balloons{% endif %}">
        <h1>{{ value.heading }}</h1>
        {{ value.description }}
    </div>

4. The value of a ListBlock is a plain Python list; iterating over it returns plain child values.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

5. StructBlock and StreamBlock values always know how to render their own templates, even if you only have the plain value rather than the BoundBlock.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This is possible because the HTML rendering behaviour of these blocks does not interfere with their main role as a container for data - there's no "double identity" as there is for blocks like CharBlock. For example, if a StructBlock is nested in another StructBlock, as in:

.. code-block:: python

    class EventBlock(blocks.StructBlock):
        heading = HeadingBlock()
        description = blocks.TextBlock()
        guest_speaker = blocks.StructBlock([
            ('first_name', blocks.CharBlock()),
            ('surname', blocks.CharBlock()),
            ('photo', ImageChooserBlock()),
        ], template='blocks/speaker.html')

then writing ``{{ value.guest_speaker }}`` within the EventBlock's template will use the template rendering from blocks/speaker.html for that field.


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

As with any model field in Django, any changes to a model definition that affect a StreamField will result in a migration file that contains a 'frozen' copy of that field definition. Since a StreamField definition is more complex than a typical model field, there is an increased likelihood of definitions from your project being imported into the migration - which would cause problems later on if those definitions are moved or deleted.

To mitigate this, StructBlock, StreamBlock and ChoiceBlock implement additional logic to ensure that any subclasses of these blocks are deconstructed to plain instances of StructBlock, StreamBlock and ChoiceBlock - in this way, the migrations avoid having any references to your custom class definitions. This is possible because these block types provide a standard pattern for inheritance, and know how to reconstruct the block definition for any subclass that follows that pattern.

If you subclass any other block class, such as ``FieldBlock``, you will need to either keep that class definition in place for the lifetime of your project, or implement a `custom deconstruct method <https://docs.djangoproject.com/en/1.9/topics/migrations/#custom-deconstruct-method>`__ that expresses your block entirely in terms of classes that are guaranteed to remain in place. Similarly, if you customise a StructBlock, StreamBlock or ChoiceBlock subclass to the point where it can no longer be expressed as an instance of the basic block type - for example, if you add extra arguments to the constructor - you will need to provide your own ``deconstruct`` method.

Migrating RichTextFields to StreamField
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you change an existing RichTextField to a StreamField, and create and run migrations as normal, the migration will complete with no errors, since both fields use a text column within the database. However, StreamField uses a JSON representation for its data, and so the existing text needs to be converted with a data migration in order to become accessible again. For this to work, the StreamField needs to include a RichTextBlock as one of the available block types. The field can then be converted by creating a new migration (``./manage.py makemigrations --empty myapp``) and editing it as follows (in this example, the 'body' field of the ``demo.BlogPage`` model is being converted to a StreamField with a RichTextBlock named ``rich_text``):

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
