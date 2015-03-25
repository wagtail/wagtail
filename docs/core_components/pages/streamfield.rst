Freeform page content using StreamField
=======================================

Wagtail's content model encourages thinking about the information on a page in a formal, structured way; for example, a page about an event is not just an assortment of headings, paragraphs and images, but has specific fields for dates, location, a list of speakers and so on. This ensures that the template developer has a known, predictable set of fields to work with, and can present that information consistently throughout the site in the most appropriate arrangement. It also allows the information to be re-used and repurposed, such as displaying an "events near you" listing.

In some cases, though, we would like to give the page author more flexibility to create freeform content, such as blog posts or news stories where the text may be interspersed with subheadings, images, pull quotes and video, and perhaps more specialised content types such as maps and charts (or, for a programming blog, code snippets). The traditional approach to this would be to use a rich text field for the entire page body, with the different content types implemented using a variety of HTML styles. This approach is not recommended; aside from rich text simply not being a very good interface for editing this kind of complex content, it also means that the content becomes an opaque blob of HTML, and we lose the semantic information that indicates what the different block types actually mean.

StreamField solves the problem of freeform content by expressing it as a sequence of 'blocks' - headings, images, paragraphs and so on - which can be repeated and arranged in any order. Each block is editable using the most suitable interface for that block type - such as a rich text area for paragraphs, or Wagtail's image chooser (along with dropdowns to specify image format, where appropriate) for images.

StreamField also provides a rich API to define your own block types, ranging from simple collections of sub-blocks (such as a 'person' block consisting of first name, surname and photograph) to completely custom components with their own editing interface. Within the database, the StreamField content is stored as JSON, ensuring that the complete informational content of the field is preserved, rather than just an HTML representation of it.

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

    BlogPage.content_panels = [
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

``ChoiceBlock`` can also be subclassed to produce a reusable block with the same list of choices everywhere it is used. For example, a block definition such as::

    blocks.ChoiceBlock(choices=[
        ('tea', 'Tea'),
        ('coffee', 'Coffee'),
    ], icon='cup')

could be rewritten as a subclass of ChoiceBlock::

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

A control for selecting a page object, using Wagtail's page browser. The keyword argument ``required`` is accepted.

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

A block consisting of a fixed group of sub-blocks to be displayed together. Takes a list of (name, block_definition) tuples as its first argument::

    ('person', blocks.StructBlock([
        ('first_name', blocks.CharBlock(required=True)),
        ('surname', blocks.CharBlock(required=True)),
        ('photo', ImageChooserBlock()),
        ('biography', blocks.RichTextBlock()),
    ], icon='user'))


Alternatively, the list of sub-blocks can be provided in a subclass of StructBlock::

    class PersonBlock(blocks.StructBlock):
        first_name = blocks.CharBlock(required=True)
        surname = blocks.CharBlock(required=True)
        photo = ImageChooserBlock()
        biography = blocks.RichTextBlock()

        class Meta:
            icon = 'user'


The ``Meta`` class supports the properties ``default``, ``label``, ``icon`` and ``template``; these have the same meanings as when they are passed to the block's constructor.

This defines ``PersonBlock()`` as a block type that can be re-used as many times as you like within your model definitions::

    body = StreamField([
        ('heading', blocks.CharBlock(classname="full title")),
        ('paragraph', blocks.RichTextBlock()),
        ('image', ImageChooserBlock()),
        ('person', PersonBlock()),
    ])


ListBlock
~~~~~~~~~

``wagtail.wagtailcore.blocks.ListBlock``

A block consisting of many sub-blocks, all of the same type. The editor can add an unlimited number of sub-blocks, and re-order and delete them. Takes the definition of the sub-block as its first argument::

    ('ingredients_list', blocks.ListBlock(blocks.CharBlock(label="Ingredient")))


Any block type is valid as the sub-block type, including structural types::

    ('ingredients_list', blocks.ListBlock(blocks.StructBlock(
        ('ingredient', blocks.CharBlock(required=True)),
        ('amount', blocks.CharBlock()),
    )))


StreamBlock
~~~~~~~~~~~

``wagtail.wagtailcore.blocks.StreamBlock``

A block consisting of a sequence of sub-blocks of different types, which can be mixed and reordered in any order. Used as the overall mechanism of the StreamField itself, but can also be nested or used within other structural block types. Takes a list of (name, block_definition) tuples as its first argument::

    ('carousel', blocks.StreamBlock(
        [
            ('image', ImageChooserBlock()),
            ('quotation', blocks.StructBlock([
                ('text', blocks.TextBlock()),
                ('author', blocks.CharBlock),
            ])),
            ('video', blocks.EmbedBlock()),
        ],
        icon='cogs'
    ))


As with StructBlock, the list of sub-blocks can also be provided as a subclass of StreamBlock::

    class CarouselBlock(blocks.StreamBlock):
        image = ImageChooserBlock()
        quotation = blocks.StructBlock([
            ('text', blocks.TextBlock()),
            ('author', blocks.CharBlock),
        ])
        video = blocks.EmbedBlock

        class Meta:
            icon='cogs'


Since ``StreamField`` accepts an instance of ``StreamBlock`` as a parameter, in place of a list of block types, this makes it possible to re-use a common set block types without repeating definitions::

    class HomePage(Page):
        carousel = StreamField(CarouselBlock())


Template rendering
------------------

The simplest way to render the contents of a StreamField into your template is to output it as a variable, like any other field::

    {{ self.body }}

This will render each block of the stream in turn, wrapped in a ``<div class="block-my_block_name">`` element (where ``my_block_name`` is the block name given in the StreamField definition). If you wish to provide your own HTML markup, you can instead iterate over the field's value to access each block in turn::

    <article>
        {% for block in self.body %}
            <section>{{ block }}</section>
        {% endfor %}
    </article>


For more control over the rendering of specific block types, each block object provides ``block_type`` and ``value`` properties::

    <article>
        {% for block in self.body %}
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

To override this with your own custom HTML rendering, you can pass a ``template`` argument to the block, giving the filename of a template file to be rendered. This is particularly useful for custom block types derived from StructBlock, as the default StructBlock rendering is simple and somewhat generic::

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


Or, when defined as a subclass of StructBlock::

    class PersonBlock(blocks.StructBlock):
        first_name = blocks.CharBlock(required=True)
        surname = blocks.CharBlock(required=True)
        photo = ImageChooserBlock()
        biography = blocks.RichTextBlock()

        class Meta:
            template = 'myapp/blocks/person.html'
            icon = 'user'



Within the template, the block value is accessible as the variable ``self``::

    {% load wagtailimages_tags %}

    <div class="person">
        {% image self.photo width-400 %}
        <h2>{{ self.first_name }} {{ self.surname }}</h2>
        {{ self.bound_blocks.biography.render }}
    </div>


The line ``self.bound_blocks.biography.render`` warrants further explanation. While blocks such as RichTextBlock are aware of their own rendering, the actual block *values* (as returned when accessing properties of a StructBlock, such as ``self.biography``), are just plain Python values such as strings. To access the block's proper HTML rendering, you must retrieve the 'bound block' - an object which has access to both the rendering method and the value - via the ``bound_blocks`` property.


Custom block types
------------------

If you need to implement a custom UI, or handle a datatype that is not provided by Wagtail's built-in block types (and cannot built up as a structure of existing fields), it is possible to define your own custom block types. For further guidance, refer to the source code of Wagtail's built-in block classes.

For block types that simply wrap an existing Django form field, Wagtail provides an abstract class ``wagtail.wagtailcore.blocks.FieldBlock`` as a helper. Subclasses just need to set a ``field`` property that returns the form field object::

    class IPAddressBlock(FieldBlock):
        def __init__(self, required=True, help_text=None, **kwargs):
            self.field = forms.GenericIPAddressField(required=required, help_text=help_text)
            super(IPAddressBlock, self).__init__(**kwargs)



Migrations
----------

As with any model field in Django, any changes to a model definition that affect a StreamField will result in a migration file that contains a 'frozen' copy of that field definition. Since a StreamField definition is more complex than a typical model field, there is an increased likelihood of definitions from your project being imported into the migration - which would cause problems later on if those definitions are moved or deleted.

To mitigate this, StructBlock, StreamBlock and ChoiceBlock implement additional logic to ensure that any subclasses of these blocks are deconstructed to plain instances of StructBlock, StreamBlock and ChoiceBlock - in this way, the migrations avoid having any references to your custom class definitions. This is possible because these block types provide a standard pattern for inheritance, and know how to reconstruct the block definition for any subclass that follows that pattern.

If you subclass any other block class, such as ``FieldBlock``, you will need to either keep that class definition in place for the lifetime of your project, or implement a `custom deconstruct method <https://docs.djangoproject.com/en/1.7/topics/migrations/#custom-deconstruct-method>`__ that expresses your block entirely in terms of classes that are guaranteed to remain in place. Similarly, if you customise a StructBlock, StreamBlock or ChoiceBlock subclass to the point where it can no longer be expressed as an instance of the basic block type - for example, if you add extra arguments to the constructor - you will need to provide your own ``deconstruct`` method.
