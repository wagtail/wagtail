
.. _form_builder:

Form builder
============

The ``wagtailforms`` module allows you to set up single-page forms, such as a 'Contact us' form, as pages of a Wagtail site. It provides a set of base models that site implementers can extend to create their own ``FormPage`` type with their own site-specific templates. Once a page type has been set up in this way, editors can build forms within the usual page editor, consisting of any number of fields. Form submissions are stored for later retrieval through a new 'Forms' section within the Wagtail admin interface; in addition, they can be optionally e-mailed to an address specified by the editor.

.. note::
  **wagtailforms is not a replacement for** `Django's form support <https://docs.djangoproject.com/en/1.10/topics/forms/>`_. It is designed as a way for page authors to build general-purpose data collection forms without having to write code. If you intend to build a form that assigns specific behaviour to individual fields (such as creating user accounts), or needs a custom HTML layout, you will almost certainly be better served by a standard Django form, where the fields are fixed in code rather than defined on-the-fly by a page author. See the `wagtail-form-example project <https://github.com/gasman/wagtail-form-example/commits/master>`_ for an example of integrating a Django form into a Wagtail page.

.. _form_builder_usage:

Usage
~~~~~

Add ``wagtail.wagtailforms`` to your ``INSTALLED_APPS``:

.. code-block:: python

    INSTALLED_APPS = [
       ...
       'wagtail.wagtailforms',
    ]

Within the ``models.py`` of one of your apps, create a model that extends ``wagtailforms.models.AbstractEmailForm``:


.. code-block:: python

    from modelcluster.fields import ParentalKey
    from wagtail.wagtailadmin.edit_handlers import (
        FieldPanel, FieldRowPanel,
        InlinePanel, MultiFieldPanel
    )
    from wagtail.wagtailcore.fields import RichTextField
    from wagtail.wagtailforms.models import AbstractEmailForm, AbstractFormField


    class FormField(AbstractFormField):
        page = ParentalKey('FormPage', related_name='form_fields')


    class FormPage(AbstractEmailForm):
        intro = RichTextField(blank=True)
        thank_you_text = RichTextField(blank=True)

        content_panels = AbstractEmailForm.content_panels + [
            FieldPanel('intro', classname="full"),
            InlinePanel('form_fields', label="Form fields"),
            FieldPanel('thank_you_text', classname="full"),
            MultiFieldPanel([
                FieldRowPanel([
                    FieldPanel('from_address', classname="col6"),
                    FieldPanel('to_address', classname="col6"),
                ]),
                FieldPanel('subject'),
            ], "Email"),
        ]

``AbstractEmailForm`` defines the fields ``to_address``, ``from_address`` and ``subject``, and expects ``form_fields`` to be defined. Any additional fields are treated as ordinary page content - note that ``FormPage`` is responsible for serving both the form page itself and the landing page after submission, so the model definition should include all necessary content fields for both of those views.

If you do not want your form page type to offer form-to-email functionality, you can inherit from AbstractForm instead of ``AbstractEmailForm``, and omit the ``to_address``, ``from_address`` and ``subject`` fields from the ``content_panels`` definition.

You now need to create two templates named ``form_page.html`` and ``form_page_landing.html`` (where ``form_page`` is the underscore-formatted version of the class name). ``form_page.html`` differs from a standard Wagtail template in that it is passed a variable ``form``, containing a Django ``Form`` object, in addition to the usual ``page`` variable. A very basic template for the form would thus be:

.. code-block:: html

    {% load wagtailcore_tags %}
    <html>
        <head>
            <title>{{ page.title }}</title>
        </head>
        <body>
            <h1>{{ page.title }}</h1>
            {{ page.intro|richtext }}
            <form action="{% pageurl page %}" method="POST">
                {% csrf_token %}
                {{ form.as_p }}
                <input type="submit">
            </form>
        </body>
    </html>

``form_page_landing.html`` is a regular Wagtail template, displayed after the user makes a successful form submission. If you want to dynamically override the landing page template, you can do so with the ``get_landing_page_template`` method (in the same way that you would with ``get_template``).


.. _wagtailforms_formsubmissionpanel:

Displaying form submission information
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``FormSubmissionsPanel`` can be added to your page's panel definitions to display the number of form submissions and the time of the most recent submission, along with a quick link to access the full submission data:

.. code-block:: python

    from wagtail.wagtailforms.edit_handlers import FormSubmissionsPanel

    class FormPage(AbstractEmailForm):
        # ...

        content_panels = AbstractEmailForm.content_panels + [
            FormSubmissionsPanel(),
            FieldPanel('intro', classname="full"),
            # ...
        ]


StreamField Forms
~~~~~~~~~~~~~~~~~

Inserting form fields in StreamFields allows for a more flexible form builder.
For example headings and paragraphs of text could be mixed between groups of fields to make forms more user friendly.

Pages that include form fields must inherit from ``wagtail.wagtailforms.models.StreamFieldAbstractFormMixin`` and ``wagtail.wagtailforms.models.AbstractForm``.
Unlike other classes that inherit from ``wagtail.wagtailforms.models.AbstractForm`` those that inherit from ``wagtail.wagtailforms.models.StreamFieldAbstractFormMixin`` do not require a ``form_fields`` member or a related ``Model`` class to store field information.
Instead ``wagtail.wagtailforms.models.StreamFieldAbstractFormMixin`` provides a property that provides similar features to what a related class would.

Here is an example of how this might look:

.. code-block:: python
    
    from wagtail.wagtailcore.blocks import CharBlock, RichTextBlock
    from wagtail.wagtailcore.fields import StreamField
    from wagtail.wagtailforms.models import AbstractForm, StreamFieldAbstractFormMixin
    from wagtail.wagtailforms.blocks import FormFieldBlock
    
    
    class StreamFieldFormPage(StreamFieldAbstractFormMixin, AbstractForm):
        body = StreamField([
            ('h2', CharBlock()),
            ('h3', CharBlock()),
            ('p', RichTextBlock()),
            ('field', FormFieldBlock()),
        ])
        thanks = StreamField([
            ('h2', CharBlock()),
            ('h3', CharBlock()),
            ('p', RichTextBlock()),
        ])
    
    StreamFieldFormPage.content_panels = [
        FieldPanel('title', classname='full title'),
        StreamFieldPanel('body'),
        StreamFieldPanel('thank_you_text'),
    ]


Rendering a form in a template requires an additional template tag. 
Like a normal ``wagtail.wagtailforms.models.AbstractForm`` there is a form instance passed to the template.
The ``get_form_field`` tag allows the form field instance to be stored in a template variable and used to render the form one field at a time.
See the example usage below:

.. code-block:: html

    {% load wagtailcore_tags streamfieldforms %}
    <html>
    <head><title></title></head>
    <body>
        <h1>{{ self.title }}</h1>
        
        <form action="{% pageurl page %}" method="POST">
            {% csrf_token %}
            
            {% for block in self.body %}
                {% if block.block_type == 'h2' %}
                    <h2 id="{{ block|slugify }}">{{ block }}</h2>
                {% elif block.block_type == 'h3' %}
                    <h3>{{ block }}</h3>
                {% elif block.block_type == 'p' %}
                    {{ block.value|richtext }}
                {% elif block.block_type == 'field' %}
                    {% get_form_field block form as field %}
                    <div class="form-field">
                        {{ field.label_tag }}
                        {{ field }}
                        {{ field.errors }}
                    </div>
                {% else %}
                    {{ block }}
                {% endif %}
            {% endfor %}
        
            <input type="submit" class="button"/>
        </form>
    </body>
    </html>


When an instance of ``StreamFieldFormPage`` is created the form may be displayed on the page.
When the form is submitted, it works in the same way as other Form Builder pages by showing a template that ends with ``_landing``.
Also, all values that are submitted are stored in the same way as other Form Builder pages so that exporting and viewing the submissions in the Wagtail admin work exactly the same way.


Index
~~~~~

.. toctree::
    :maxdepth: 1

    customisation
