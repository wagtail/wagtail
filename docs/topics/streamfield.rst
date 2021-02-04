.. _streamfield:

How to use StreamField
======================

StreamField provides a content editing model suitable for pages that do not follow a fixed structure -- such as blog posts or news stories -- where the text may be interspersed with subheadings, images, pull quotes and video. It's also suitable for more specialised content types, such as maps and charts (or, for a programming blog, code snippets). In this model, these different content types are represented as a sequence of 'blocks', which can be repeated and arranged in any order.

For further background on StreamField, and why you would use it instead of a rich text field for the article body, see the blog post `Rich text fields and faster horses <https://torchbox.com/blog/rich-text-fields-and-faster-horses/>`__.

StreamField also offers a rich API to define your own block types, ranging from simple collections of sub-blocks (such as a 'person' block consisting of first name, surname and photograph) to completely custom components with their own editing interface. Within the database, the StreamField content is stored as JSON, ensuring that the full informational content of the field is preserved, rather than just an HTML representation of it.


Using StreamField
-----------------

``StreamField`` is a model field that can be defined within your page model like any other field:

.. code-block:: python

    from django.db import models

    from wagtail.core.models import Page
    from wagtail.core.fields import StreamField
    from wagtail.core import blocks
    from wagtail.admin.edit_handlers import FieldPanel, StreamFieldPanel
    from wagtail.images.blocks import ImageChooserBlock

    class BlogPage(Page):
        author = models.CharField(max_length=255)
        date = models.DateField("Post date")
        body = StreamField([
            ('heading', blocks.CharBlock(form_classname="full title")),
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

You can find the complete list of available block types in the :ref:`StreamField reference <streamfield_reference>`.

Structural block types
----------------------

In addition to the basic block types, it is possible to define new block types made up of sub-blocks: for example, a 'person' block consisting of sub-blocks for first name, surname and image, or a 'carousel' block consisting of an unlimited number of image blocks. These structures can be nested to any depth, making it possible to have a structure containing a list, or a list of structures.

.. _streamfield_personblock_example:

This example demonstrates how the basic block types can be combined into a more complex block type based on ``StructBlock``:

.. code-block:: python

    from wagtail.core import blocks

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
            ('first_name', blocks.CharBlock()),
            ('surname', blocks.CharBlock()),
            ('photo', ImageChooserBlock(required=False)),
            ('biography', blocks.RichTextBlock()),
        ],
        template='myapp/blocks/person.html',
        icon='user'
    ))


Or, when defined as a subclass of StructBlock:

.. code-block:: python

    class PersonBlock(blocks.StructBlock):
        first_name = blocks.CharBlock()
        surname = blocks.CharBlock()
        photo = ImageChooserBlock(required=False)
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
        title = blocks.CharBlock()
        date = blocks.DateBlock()

        def get_context(self, value, parent_context=None):
            context = super().get_context(value, parent_context=parent_context)
            context['is_happening_today'] = (value['date'] == datetime.date.today())
            return context

        class Meta:
            template = 'myapp/blocks/event.html'


In this example, the variable ``is_happening_today`` will be made available within the block template. The ``parent_context`` keyword argument is available when the block is rendered through an ``{% include_block %}`` tag, and is a dict of variables passed from the calling template.

All block types, not just ``StructBlock``, support the ``template`` property. However, for blocks that handle basic Python data types, such as ``CharBlock`` and ``IntegerBlock``, there are some limitations on where the template will take effect. For further details, see :ref:`boundblocks_and_values`.


.. _custom_editing_interfaces_for_structblock:

Custom editing interfaces for ``StructBlock``
---------------------------------------------

To customise the styling of a ``StructBlock`` as it appears in the page editor, you can specify a ``form_classname`` attribute (either as a keyword argument to the ``StructBlock`` constructor, or in a subclass's ``Meta``) to override the default value of ``struct-block``:

.. code-block:: python

    class PersonBlock(blocks.StructBlock):
        first_name = blocks.CharBlock()
        surname = blocks.CharBlock()
        photo = ImageChooserBlock(required=False)
        biography = blocks.RichTextBlock()

        class Meta:
            icon = 'user'
            form_classname = 'person-block struct-block'


You can then provide custom CSS for this block, targeted at the specified classname, by using the :ref:`insert_editor_css` hook.

.. Note::
    Wagtail's editor styling has some built in styling for the ``struct-block`` class and other related elements. If you specify a value for ``form_classname``, it will overwrite the classes that are already applied to ``StructBlock``, so you must remember to specify the ``struct-block`` as well.

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
        first_name = blocks.CharBlock()
        surname = blocks.CharBlock()
        photo = ImageChooserBlock(required=False)
        biography = blocks.RichTextBlock()

        def get_form_context(self, value, prefix='', errors=None):
            context = super().get_form_context(value, prefix=prefix, errors=errors)
            context['suggested_first_names'] = ['John', 'Paul', 'George', 'Ringo']
            return context

        class Meta:
            icon = 'user'
            form_template = 'myapp/block_forms/person.html'


.. _custom_value_class_for_structblock:

Custom value class for ``StructBlock``
--------------------------------------

To customise the methods available for a ``StructBlock`` value, you can specify a ``value_class`` attribute (either as a keyword argument to the ``StructBlock`` constructor, or in a subclass's ``Meta``) to override how the value is prepared.

This ``value_class`` must be a subclass of ``StructValue``, any additional methods can access the value from sub-blocks via the block key on ``self`` (e.g. ``self.get('my_block')``).

Example:

.. code-block:: python

    from wagtail.core.models import Page
    from wagtail.core.blocks import (
      CharBlock, PageChooserBlock, StructValue, StructBlock, TextBlock, URLBlock)


    class LinkStructValue(StructValue):
        def url(self):
            external_url = self.get('external_url')
            page = self.get('page')
            if external_url:
                return external_url
            elif page:
                return page.url


    class QuickLinkBlock(StructBlock):
        text = CharBlock(label="link text", required=True)
        page = PageChooserBlock(label="page", required=False)
        external_url = URLBlock(label="external URL", required=False)

        class Meta:
            icon = 'site'
            value_class = LinkStructValue


    class MyPage(Page):
        quick_links = StreamField([('links', QuickLinkBlock())], blank=True)
        quotations = StreamField([('quote', StructBlock([
            ('quote', TextBlock(required=True)),
            ('page', PageChooserBlock(required=False)),
            ('external_url', URLBlock(required=False)),
        ], icon='openquote', value_class=LinkStructValue))], blank=True)

        content_panels = Page.content_panels + [
            StreamFieldPanel('quick_links'),
            StreamFieldPanel('quotations'),
        ]



Your extended value class methods will be available in your template:

.. code-block:: html+django

    {% load wagtailcore_tags %}

    <ul>
        {% for link in page.quick_links %}
          <li><a href="{{ link.value.url }}">{{ link.value.text }}</a></li>
        {% endfor %}
    </ul>

    <div>
        {% for quotation in page.quotations %}
          <blockquote cite="{{ quotation.value.url }}">
            {{ quotation.value.quote }}
          </blockquote>
        {% endfor %}
    </div>


.. _modifying_streamfield_data:

Modifying StreamField data
--------------------------

A StreamField's value behaves as a list, and blocks can be inserted, overwritten and deleted before saving the instance back to the database. A new item can be written to the list as a tuple of *(block_type, value)* - when read back, it will be returned as a ``BoundBlock`` object.

.. code-block:: python

    # Replace the first block with a new block of type 'heading'
    my_page.body[0] = ('heading', "My story")

    # Delete the last block
    del my_page.body[-1]

    # Append a block to the stream
    my_page.body.append(('paragraph', "<p>And they all lived happily ever after.</p>"))

    # Save the updated data back to the database
    my_page.save()


.. versionadded:: 2.12

    In earlier versions, a StreamField value could be replaced by assigning a new list of *(block_type, value)* tuples, but not modified in-place.


Custom block types
------------------

If you need to implement a custom UI, or handle a datatype that is not provided by Wagtail's built-in block types (and cannot be built up as a structure of existing fields), it is possible to define your own custom block types. For further guidance, refer to the source code of Wagtail's built-in block classes.

For block types that simply wrap an existing Django form field, Wagtail provides an abstract class ``wagtail.core.blocks.FieldBlock`` as a helper. Subclasses just need to set a ``field`` property that returns the form field object:

.. code-block:: python

    class IPAddressBlock(FieldBlock):
        def __init__(self, required=True, help_text=None, **kwargs):
            self.field = forms.GenericIPAddressField(required=required, help_text=help_text)
            super().__init__(**kwargs)


Migrations
----------

StreamField definitions within migrations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

As with any model field in Django, any changes to a model definition that affect a StreamField will result in a migration file that contains a 'frozen' copy of that field definition. Since a StreamField definition is more complex than a typical model field, there is an increased likelihood of definitions from your project being imported into the migration -- which would cause problems later on if those definitions are moved or deleted.

To mitigate this, StructBlock, StreamBlock and ChoiceBlock implement additional logic to ensure that any subclasses of these blocks are deconstructed to plain instances of StructBlock, StreamBlock and ChoiceBlock -- in this way, the migrations avoid having any references to your custom class definitions. This is possible because these block types provide a standard pattern for inheritance, and know how to reconstruct the block definition for any subclass that follows that pattern.

If you subclass any other block class, such as ``FieldBlock``, you will need to either keep that class definition in place for the lifetime of your project, or implement a :ref:`custom deconstruct method <django:custom-deconstruct-method>` that expresses your block entirely in terms of classes that are guaranteed to remain in place. Similarly, if you customise a StructBlock, StreamBlock or ChoiceBlock subclass to the point where it can no longer be expressed as an instance of the basic block type -- for example, if you add extra arguments to the constructor -- you will need to provide your own ``deconstruct`` method.

.. _streamfield_migrating_richtext:

Migrating RichTextFields to StreamField
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you change an existing RichTextField to a StreamField, the database migration will complete with no errors, since both fields use a text column within the database. However, StreamField uses a JSON representation for its data, so the existing text requires an extra conversion step in order to become accessible again. For this to work, the StreamField needs to include a RichTextBlock as one of the available block types. (When updating the model, don't forget to change ``FieldPanel`` to ``StreamFieldPanel`` too.) Create the migration as normal using ``./manage.py makemigrations``, then edit it as follows (in this example, the 'body' field of the ``demo.BlogPage`` model is being converted to a StreamField with a RichTextBlock named ``rich_text``):

.. code-block:: python

    # -*- coding: utf-8 -*-
    from django.db import models, migrations
    from wagtail.core.rich_text import RichText


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
            # leave the generated AlterField intact!
            migrations.AlterField(
                model_name='BlogPage',
                name='body',
                field=wagtail.core.fields.StreamField([('rich_text', wagtail.core.blocks.RichTextBlock())]),
            ),

            migrations.RunPython(
                convert_to_streamfield,
                convert_to_richtext,
            ),
        ]


Note that the above migration will work on published Page objects only. If you also need to migrate draft pages and page revisions, then edit the migration as in the following example instead:

.. code-block:: python

    # -*- coding: utf-8 -*-
    import json

    from django.core.serializers.json import DjangoJSONEncoder
    from django.db import migrations, models

    from wagtail.core.rich_text import RichText


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
            # leave the generated AlterField intact!
            migrations.AlterField(
                model_name='BlogPage',
                name='body',
                field=wagtail.core.fields.StreamField([('rich_text', wagtail.core.blocks.RichTextBlock())]),
            ),

            migrations.RunPython(
                convert_to_streamfield,
                convert_to_richtext,
            ),
        ]
