# Create contact page

Having a contact page on your portfolio site will help you connect with potential clients, employers, or other professionals who are interested in your skills.

In this section of the tutorial, you'll add a contact page to your portfolio site using Wagtail forms.

Start by modifying your `base/models.py` file:

```python
from django.db import models

# import parentalKey:
from modelcluster.fields import ParentalKey

# import FieldRowPanel and InlinePanel:
from wagtail.admin.panels import (
    FieldPanel,
    FieldRowPanel,
    InlinePanel,
    MultiFieldPanel,
    PublishingPanel,
)

from wagtail.fields import RichTextField
from wagtail.models import (
    DraftStateMixin,
    PreviewableMixin,
    RevisionMixin,
    TranslatableMixin,
)

# import AbstractEmailForm and AbstractFormField:
from wagtail.contrib.forms.models import AbstractEmailForm, AbstractFormField

# import FormSubmissionsPanel:
from wagtail.contrib.forms.panels import FormSubmissionsPanel
from wagtail.contrib.settings.models import (
    BaseGenericSetting,
    register_setting,
)
from wagtail.snippets.models import register_snippet


# ... keep the definition of NavigationSettings and FooterText. Add FormField and FormPage:
class FormField(AbstractFormField):
    page = ParentalKey('FormPage', on_delete=models.CASCADE, related_name='form_fields')


class FormPage(AbstractEmailForm):
    intro = RichTextField(blank=True)
    thank_you_text = RichTextField(blank=True)

    content_panels = AbstractEmailForm.content_panels + [
        FormSubmissionsPanel(),
        FieldPanel('intro'),
        InlinePanel('form_fields', label="Form fields"),
        FieldPanel('thank_you_text'),
        MultiFieldPanel([
            FieldRowPanel([
                FieldPanel('from_address'),
                FieldPanel('to_address'),
            ]),
            FieldPanel('subject'),
        ], "Email"),
    ]
```

In the preceding code, your `FormField` model inherits from `AbstractFormField`. With `AbstractFormField`, you can define any form field type of your choice in the admin interface. `page = ParentalKey('FormPage', on_delete=models.CASCADE, related_name='form_fields')` defines a parent-child relationship between the `FormField` and `FormPage` models.

On the other hand, your `FormPage` model inherits from `AbstractEmailForm`. Unlike `AbstractFormField`, `AbstractEmailForm` offers a form-to-email capability. Also, it defines the `to_address`, `from_address`, and `subject` fields. It expects a `form_fields` to be defined.

After defining your `FormField` and `FormPage` models, you must create `form_page` and `form_page_landing` templates. The `form_page` template differs from a standard Wagtail template because it's passed a variable named `form` containing a Django `Form` object in addition to the usual `Page` variable. The `form_page_landing.html`, on the other hand, is a standard Wagtail template. Your site displays the `form_page_landing.html` after a user makes a successful form submission.

Now, create a `base/templates/base/form_page.html` file and add the following to it:

```html+django
{% extends "base.html" %}
{% load wagtailcore_tags %}

{% block body_class %}template-formpage{% endblock %}

{% block content %}
    <h1>{{ page.title }}</h1>
    <div>{{ page.intro|richtext }}</div>

    <form class="page-form" action="{% pageurl page %}" method="POST">
        {% csrf_token %}
        {{ form.as_div }}
        <button type="Submit">Submit</button>
    </form>
{% endblock content %}
```

Also, create a `base/templates/base/form_page_landing.html` file and add the following to it:

```html+django
{% extends "base.html" %}
{% load wagtailcore_tags %}

{% block body_class %}template-formpage{% endblock %}

{% block content %}
    <h1>{{ page.title }}</h1>
    <div>{{ page.thank_you_text|richtext }}</div>
{% endblock content %}
```

Now, you’ve added all the necessary lines of code and templates that you need to create a contact page on your portfolio website.

Now, migrate your database by running `python manage.py makemigrations` and then `python manage.py migrate`.

(add_your_contact_information)=

## Add your contact information

To add contact information to your portfolio site, follow these steps:

1. Create a **Form page** as a child page of **Home** by following these steps:

    a. Restart your server.
    b. Go to your admin interface.
    c. Click `Pages` in your [Sidebar](https://guide.wagtail.org/en-latest/how-to-guides/find-your-way-around/#the-sidebar).
    d. Click `Home`.
    e. Click the `+` icon (Add child page) at the top of the resulting page.
    f. Click `Form page`.

2. Add the necessary data.
3. Publish your `Form Page`.

## Style your contact page

To style your contact page, add the following CSS to your `mysite/static/css/mysite.css` file:

```css
.page-form label {
    display: block;
    margin-top: 10px;
    margin-bottom: 5px;
}

.page-form :is(textarea, input, select) {
    width: 100%;
    max-width: 500px;
    min-height: 40px;
    margin-top: 5px;
    margin-bottom: 10px;
}

.page-form .helptext {
    font-style: italic;
}
```

In the next section of this tutorial, you'll learn how to add a portfolio page to your site.
