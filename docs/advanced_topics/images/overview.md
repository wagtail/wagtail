(images_overview)=

# Images overview

This page provides an overview of the basics of using the `'wagtail.images'` app in your Wagtail project.

## Including `'wagtail.images'` in `INSTALLED_APPS`

To use the `wagtail.images` app, you need to include it in the `INSTALLED_APPS` list in your Django project's settings. Simply add it to the list like this:

```python
# settings.py

INSTALLED_APPS = [
    # ...
    'wagtail.images',
    # ...
]
```

Images are stored in the database using the `wagtailimages.Image` model. Uploaded image files are saved to your configured media storage, and resized versions (known as [renditions](image_renditions)) are generated on demand. This means the app relies on the `MEDIA_ROOT` and `MEDIA_URL` settings being configured. See [](/getting_started/integrating_into_django) for the full set of settings required to run Wagtail.

New images saved are stored in the [reference index](managing_the_reference_index) by default.

## Using images in a Page

To attach an image to a Wagtail page, add a `ForeignKey` to the image model on your page model, then expose it with a `FieldPanel`.

You can refer to the image model either by its string reference `'wagtailimages.Image'` or, to remain compatible with [custom image models](/advanced_topics/images/custom_image_model), by calling {func}`~wagtail.images.get_image_model`.

Here's an example:

```python
# models.py

from django.db import models

from wagtail.admin.panels import FieldPanel
from wagtail.images import get_image_model
from wagtail.models import Page


class YourPage(Page):
    # ...
    image = models.ForeignKey(
        get_image_model(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    content_panels = Page.content_panels + [
        # ...
        FieldPanel("image"),
    ]
```

```{note}
Use `related_name="+"` to tell Django not to create a reverse accessor on the image model, which is useful when several models refer to images. Use `on_delete=models.SET_NULL` (together with `null=True`) so that deleting an image does not delete the pages that use it.
```

This allows you to select an image when creating or editing a page, and render it in your page template using the [`{% image %}` tag](image_tag):

```html+django
{% load wagtailimages_tags %}

{% if page.image %}
    {% image page.image width-400 %}
{% endif %}
```

The `{% image %}` tag generates a rendition on the fly at the requested size. For the full set of resizing rules and options, see [](image_tag).

## Using images within `RichTextFields`

Images can be inserted into pages using the [`RichTextField`](rich_text_field). By default, Wagtail includes the feature for adding images, see [](rich_text_features).

You can either exclude or include this by passing the `features` to your `RichTextField`. In the example below we create a `RichTextField` with only images and basic formatting.

```python
# models.py
from wagtail.fields import RichTextField

class BlogPage(Page):
    # ...other fields
    body = RichTextField(
        blank=True,
        features=["bold", "italic", "ol", "image"]
    )

    panels = [
        # ...other panels
        FieldPanel("body"),
    ]
```

## Using images within `StreamField`

`StreamField` provides a content editing model suitable for pages that do not follow a fixed structure. To add images using `StreamField`, include it in your models and also include the `ImageChooserBlock`.

Create a `Page` model with a `StreamField` named `body` and an `ImageChooserBlock` named `image` inside the field:

```python
# models.py

from wagtail.fields import StreamField
from wagtail.images.blocks import ImageChooserBlock


class BlogPage(Page):
    # ... other fields

    body = StreamField([
            ('image', ImageChooserBlock())
        ],
        null=True,
        blank=True,
    )

    panels = [
        # ... other panels
        FieldPanel("body"),
    ]
```

In `blog_page.html`, add the following block of code to render each image in the page:

```html+django
{% load wagtailimages_tags %}

{% for block in page.body %}
    {% if block.block_type == "image" %}
        {% image block.value width-600 %}
    {% endif %}
{% endfor %}
```

## Customizing the image model

The built-in `Image` model can be replaced with a custom model, allowing you to add extra fields such as a caption or alt text. To do this, set the [`WAGTAILIMAGES_IMAGE_MODEL`](/advanced_topics/images/custom_image_model) setting to point to your model and use {func}`~wagtail.images.get_image_model` (rather than the `'wagtailimages.Image'` string) when referring to images in your own models.

For full instructions, see [](/advanced_topics/images/custom_image_model).

## Working with images and collections

Images in Wagtail can be organized within [collections](https://guide.wagtail.org/en-latest/how-to-guides/manage-collections/). Collections provide a way to group related images and can be used to control permissions and privacy.

Here's an example that retrieves all of the images in a chosen collection:

```python
from wagtail.images import get_image_model

class PageWithCollection(Page):
    collection = models.ForeignKey(
        "wagtailcore.Collection",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name='Image Collection',
    )

    content_panels = Page.content_panels + [
        FieldPanel("collection"),
    ]

    def get_context(self, request):
        context = super().get_context(request)
        context['images'] = get_image_model().objects.filter(collection=self.collection)
        return context
```

Here's an example template to render the images in the collection:

```html+django
{% extends "base.html" %}
{% load wagtailimages_tags %}

{% block content %}
    {% if images %}
    <ul>
        {% for image in images %}
        <li>{% image image width-300 %}</li>
        {% endfor %}
    </ul>
    {% endif %}
{% endblock %}
```

## Making images private

If you want to restrict access to certain images, you can place them in [private collections](https://guide.wagtail.org/en-latest/how-to-guides/manage-collections/#privacy-settings).

Private collections are not publicly accessible, and their contents are only available to users with the appropriate permissions. To serve images while enforcing these permissions, you can use the [dynamic image serve view](using_images_outside_wagtail).

## API access

Images in Wagtail can be accessed through the API via the `wagtail.images.api.v2.views.ImagesAPIViewSet`. This allows you to programmatically interact with images, retrieve their details, and perform various operations.

For more details, you can refer to the [API section](api_v2_configure_endpoints) that provides additional information and usage examples.
