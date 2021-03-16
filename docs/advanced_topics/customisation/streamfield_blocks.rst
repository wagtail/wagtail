.. _custom_streamfield_blocks:

How to build custom StreamField blocks
======================================

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


Custom block types
------------------

If you need to implement a custom UI, or handle a datatype that is not provided by Wagtail's built-in block types (and cannot be built up as a structure of existing fields), it is possible to define your own custom block types. For further guidance, refer to the source code of Wagtail's built-in block classes.

For block types that simply wrap an existing Django form field, Wagtail provides an abstract class ``wagtail.core.blocks.FieldBlock`` as a helper. Subclasses just need to set a ``field`` property that returns the form field object:

.. code-block:: python

    class IPAddressBlock(FieldBlock):
        def __init__(self, required=True, help_text=None, **kwargs):
            self.field = forms.GenericIPAddressField(required=required, help_text=help_text)
            super().__init__(**kwargs)


Handling block definitions within migrations
--------------------------------------------

As with any model field in Django, any changes to a model definition that affect a StreamField will result in a migration file that contains a 'frozen' copy of that field definition. Since a StreamField definition is more complex than a typical model field, there is an increased likelihood of definitions from your project being imported into the migration -- which would cause problems later on if those definitions are moved or deleted.

To mitigate this, StructBlock, StreamBlock and ChoiceBlock implement additional logic to ensure that any subclasses of these blocks are deconstructed to plain instances of StructBlock, StreamBlock and ChoiceBlock -- in this way, the migrations avoid having any references to your custom class definitions. This is possible because these block types provide a standard pattern for inheritance, and know how to reconstruct the block definition for any subclass that follows that pattern.

If you subclass any other block class, such as ``FieldBlock``, you will need to either keep that class definition in place for the lifetime of your project, or implement a :ref:`custom deconstruct method <django:custom-deconstruct-method>` that expresses your block entirely in terms of classes that are guaranteed to remain in place. Similarly, if you customise a StructBlock, StreamBlock or ChoiceBlock subclass to the point where it can no longer be expressed as an instance of the basic block type -- for example, if you add extra arguments to the constructor -- you will need to provide your own ``deconstruct`` method.
