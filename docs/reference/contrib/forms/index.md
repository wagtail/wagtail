(form_builder)=

# Form builder

The `wagtailforms` module allows you to set up single-page forms, such as a 'Contact us' form, as pages of a Wagtail site. It provides a set of base models that site implementers can extend to create their own `FormPage` type with their own site-specific templates. Once a page type has been set up in this way, editors can build forms within the usual page editor, consisting of any number of fields. Form submissions are stored for later retrieval through a new 'Forms' section within the Wagtail admin interface; in addition, they can be optionally e-mailed to an address specified by the editor.

```{note}
**wagtailforms is not a replacement for** [Django's form support](django:topics/forms/index). It is designed as a way for page authors to build general-purpose data collection forms without having to write code. If you intend to build a form that assigns specific behaviour to individual fields (such as creating user accounts), or needs a custom HTML layout, you will almost certainly be better served by a standard Django form, where the fields are fixed in code rather than defined on-the-fly by a page author. See the [wagtail-form-example project](https://github.com/gasman/wagtail-form-example/commits/master) for an example of integrating a Django form into a Wagtail page.
```

(form_builder_usage)=

## Usage

Add `wagtail.contrib.forms` to your `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    ...
    'wagtail.contrib.forms',
]
```

Within the `models.py` of one of your apps, create a model that extends `wagtail.contrib.forms.models.AbstractEmailForm`:

```python
from django.db import models
from modelcluster.fields import ParentalKey
from wagtail.admin.panels import (
    FieldPanel, FieldRowPanel,
    InlinePanel, MultiFieldPanel
)
from wagtail.fields import RichTextField
from wagtail.contrib.forms.models import AbstractEmailForm, AbstractFormField


class FormField(AbstractFormField):
    page = ParentalKey('FormPage', on_delete=models.CASCADE, related_name='form_fields')


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
```

`AbstractEmailForm` defines the fields `to_address`, `from_address` and `subject`, and expects `form_fields` to be defined. Any additional fields are treated as ordinary page content - note that `FormPage` is responsible for serving both the form page itself and the landing page after submission, so the model definition should include all necessary content fields for both of those views.

Date and datetime values in a form response will be formatted with the [SHORT_DATE_FORMAT](https://docs.djangoproject.com/en/3.0/ref/settings/#short-date-format) and [SHORT_DATETIME_FORMAT](https://docs.djangoproject.com/en/3.0/ref/settings/#short-datetime-format) respectively. (see [](form_builder_render_email) for how to customise the email content).

If you do not want your form page type to offer form-to-email functionality, you can inherit from AbstractForm instead of `AbstractEmailForm`, and omit the `to_address`, `from_address` and `subject` fields from the `content_panels` definition.

You now need to create two templates named `form_page.html` and `form_page_landing.html` (where `form_page` is the underscore-formatted version of the class name). `form_page.html` differs from a standard Wagtail template in that it is passed a variable `form`, containing a Django `Form` object, in addition to the usual `page` variable. A very basic template for the form would thus be:

```html+django
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
```

`form_page_landing.html` is a standard Wagtail template, displayed after the user makes a successful form submission, `form_submission` will be available in this template. If you want to dynamically override the landing page template, you can do so with the `get_landing_page_template` method (in the same way that you would with `get_template`).

(wagtailforms_formsubmissionpanel)=

## Displaying form submission information

`FormSubmissionsPanel` can be added to your page's panel definitions to display the number of form submissions and the time of the most recent submission, along with a quick link to access the full submission data:

```python
from wagtail.contrib.forms.panels import FormSubmissionsPanel

class FormPage(AbstractEmailForm):
    # ...

    content_panels = AbstractEmailForm.content_panels + [
        FormSubmissionsPanel(),
        FieldPanel('intro', classname="full"),
        # ...
    ]
```

## Index

```{toctree}
---
maxdepth: 1
titlesonly:
---
customisation
```
