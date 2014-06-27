
.. _form_builder:

Form builder
============

The `wagtailforms` module allows you to set up single-page forms, such as a 'Contact us' form, as pages of a Wagtail site. It provides a set of base models that site implementors can extend to create their own 'Form' page type with their own site-specific templates. Once a page type has been set up in this way, editors can build forms within the usual page editor, consisting of any number of fields. Form submissions are stored for later retrieval through a new 'Forms' section within the Wagtail admin interface; in addition, they can be optionally e-mailed to an address specified by the editor.


Usage
~~~~~

Add 'wagtail.wagtailforms' to your INSTALLED_APPS:

.. code:: python

    INSTALLED_APPS = [
       ...
       'wagtail.wagtailforms',
    ]

Within the models.py of one of your apps, create a model that extends wagtailforms.models.AbstractEmailForm:


.. code:: python

    from wagtail.wagtailforms.models import AbstractEmailForm, AbstractFormField

    class FormField(AbstractFormField):
        page = ParentalKey('FormPage', related_name='form_fields')

    class FormPage(AbstractEmailForm):
        intro = RichTextField(blank=True)
        thank_you_text = RichTextField(blank=True)

    FormPage.content_panels = [
        FieldPanel('title', classname="full title"),
        FieldPanel('intro', classname="full"),
        InlinePanel(FormPage, 'form_fields', label="Form fields"),
        FieldPanel('thank_you_text', classname="full"),
        MultiFieldPanel([
            FieldPanel('to_address', classname="full"),
            FieldPanel('from_address', classname="full"),
            FieldPanel('subject', classname="full"),
        ], "Email")
    ]

AbstractEmailForm defines the fields 'to_address', 'from_address' and 'subject', and expects form_fields to be defined. Any additional fields are treated as ordinary page content - note that FormPage is responsible for serving both the form page itself and the landing page after submission, so the model definition should include all necessary content fields for both of those views.

If you do not want your form page type to offer form-to-email functionality, you can inherit from AbstractForm instead of AbstractEmailForm, and omit the 'to_address', 'from_address' and 'subject' fields from the content_panels definition.

You now need to create two templates named form_page.html and form_page_landing.html (where 'form_page' is the underscore-formatted version of the class name). form_page.html differs from a standard Wagtail template in that it is passed a variable 'form', containing a Django form object, in addition to the usual 'self' variable. A very basic template for the form would thus be:

.. code:: html

    {% load pageurl rich_text %}
    <html>
        <head>
            <title>{{ self.title }}</title>
        </head>
        <body>
            <h1>{{ self.title }}</h1>
            {{ self.intro|richtext }}
            <form action="{% pageurl self %}" method="POST">
                {% csrf_token %}
                {{ form.as_p }}
                <input type="submit">
            </form>
        </body>
    </html>

form_page_landing.html is a regular Wagtail template, displayed after the user makes a successful form submission.
