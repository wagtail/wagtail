# Customize your home page

When building your portfolio website, the first step is to set up and personalize your homepage. The homepage is your chance to make an excellent first impression and convey the core message of your portfolio. So your homepage should include the following features:

1. **Introduction:** A concise introduction captures visitors' attention.
2. **Biography:** Include a brief biography that introduces yourself. This section should mention your name, role, expertise, and unique qualities.
3. **Hero Image:** This may be a professional headshot or other image that showcases your work and adds visual appeal.
4. **Call to Action (CTA):** Incorporate a CTA that guides visitors to take a specific action, such as "View Portfolio," "Hire Me," or "Learn More".
5. **Resume:** This is a document that provides a summary of your education, work experience, achievements, and qualifications.

In this section, you'll learn how to add features **1** through **4** to your homepage. You'll add your resume or CV later in the tutorial.

Now, modify your `home/models` file to include the following:

```python
from django.db import models

from wagtail.models import Page
from wagtail.fields import RichTextField

# import MultiFieldPanel:
from wagtail.admin.panels import FieldPanel, MultiFieldPanel


class HomePage(Page):
    # add the Hero section of HomePage:
    image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Homepage image",
    )
    hero_text = models.CharField(
        blank=True,
        max_length=255, help_text="Write an introduction for the site"
    )
    hero_cta = models.CharField(
        blank=True,
        verbose_name="Hero CTA",
        max_length=255,
        help_text="Text to display on Call to Action",
    )
    hero_cta_link = models.ForeignKey(
        "wagtailcore.Page",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name="Hero CTA link",
        help_text="Choose a page to link to for the Call to Action",
    )

    body = RichTextField(blank=True)

    # modify your content_panels:
    content_panels = Page.content_panels + [
        MultiFieldPanel(
            [
                FieldPanel("image"),
                FieldPanel("hero_text"),
                FieldPanel("hero_cta"),
                FieldPanel("hero_cta_link"),
            ],
            heading="Hero section",
        ),
        FieldPanel('body'),
    ]
```

You might already be familiar with the different parts of your `HomePage` model. The `image` field is a `ForeignKey` referencing Wagtail's built-in Image model for storing images. Similarly, `hero_cta_link` is a `ForeignKey` to `wagtailcore.Page`. The `wagtailcore.Page` is the base class for all other page types in Wagtail. This means all Wagtail pages inherit from `wagtailcore.Page`. For instance, your `class HomePage(page)` inherits from `wagtailcore.Page`.

Using `on_delete=models.SET_NULL` ensures that if you remove an image or hero link from your admin interface, the `image` and `hero_cta_link` fields on your Homepage will be set to null, preserving their data entries. Read the [Django documentation](https://docs.djangoproject.com/en/4.2/ref/models/fields/#django.db.models.ForeignKey.on_delete) for more values for the `on-delete` attribute.

The `related_name` attribute creates a relationship between related models. For example, if you want to access the HomePage's `image` from `wagtailimages.Image`, you can use the `related_name` attribute. When you use `related_name="+"`, you create a connection between models that doesn't create a reverse relationship for your `ForeignKey` fields. In other words, you're instructing Django to create a way to access the HomePage's `image` from `wagtailimages.Image` but not a way to access `wagtailimages.Image` from the HomePage's `image`.

While `body` is a `RichTextField`, `hero_text` and `hero_cta` are `CharField`, a Django string field for storing short text.

The [Your First Wagtail Tutorial](../getting_started/tutorial.md) already explained `content_panels`. [FieldPanel](field_panel) and [MultiPanel](multiFieldPanel) are types of Wagtail built-in [Panels](editing_api). They're both subclasses of the base Panel class and accept all of Wagtail's `Panel` parameters in addition to their own. While the `FieldPanel` provides a widget for basic Django model fields, `MultiFieldPanel` helps you decide the structure of the editing form. For example, you can group related fields.

Now that you understand the different parts of your `HomePage` model, migrate your database by running `python manage.py makemigrations` and
then `python manage.py migrate`

After migrating your database, start your server by running
`python manage.py runserver`.

(add_content_to_your_homepage)=

## Add content to your homepage

To add content to your homepage through the admin interface, follow these steps:

1. Log in to your [admin interface](http://127.0.0.1:8000/admin/), with your admin username and password.
2. Click Pages.
3. Click the **pencil**  icon beside **Home**.
4. Choose an image, choose a page, and add data to the input fields.

```Note
You can choose your home page or blog index page to link to your Call to Action. You can choose a more suitable page later in the tutorial.
```

5. Publish your Home page.

You have all the necessary data for your Home page now. You can visit your Home page by going to `http://127.0.0.1:8000` in your browser. You can't see all your data, right? That’s because you must modify your Homepage template to display the data.

Replace the content of your `home/templates/home/home_page.html` file with the following:

```html+django
{% extends "base.html" %}
{% load wagtailcore_tags wagtailimages_tags %}

{% block body_class %}template-homepage{% endblock %}

{% block content %}
    <div>
        <h1>{{ page.title }}</h1>
        {% image page.image fill-480x320 %}
        <p>{{ page.hero_text }}</p>
        {% if page.hero_cta_link %}
            <a href="{% pageurl page.hero_cta_link %}">
                {% firstof page.hero_cta page.hero_cta_link.title %}
            </a>
        {% endif %}
    </div>

  {{ page.body|richtext }}
{% endblock content %}
```

In your Homepage template, notice the use of `firstof` in line 13. It's helpful to use this tag when you have created a series of fallback options, and you want to display the first one that has a value. So, in your template, the `firstof` template tag displays `page.hero_cta` if it has a value. If `page.hero_cta` doesn't have a value, then it displays `page.hero_cta_link.title`.

Congratulations! You've completed the first stage of your Portfolio website 🎉🎉🎉.

<!-- 
Ask Thibaud if the Resume page is downloadable.
-->
