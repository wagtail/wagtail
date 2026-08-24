(images_overview)=

# Images overview

This page provides an overview of the basics of using the `'wagtail.images'` app in your Wagtail project.

## Including `'wagtail.images'` in `INSTALLED_APPS`

To use the `wagtail.images` app, you need to include it in the `INSTALLED_APPS` list in your Django project's settings. Simply add it to the list like this:

```python
# settings.py

INSTALLED_APPS = [
    # ...
    "wagtail.images",
    # ...
]
```

## Using images in a page

To add an image to a Wagtail page, add a `ForeignKey` to the image model and expose it with a `FieldPanel` in your page model.

Here's an example:

```python
# models.py

from django.db import models

from wagtail.admin.panels import FieldPanel
from wagtail.models import Page


class YourPage(Page):
    # ...
    image = models.ForeignKey(
        "wagtailimages.Image",
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

`on_delete=models.SET_NULL` keeps the page usable if the image is deleted from the image library, and `related_name="+"` avoids adding a reverse accessor to the image model, which is rarely useful.

If your project uses a [custom image model](/advanced_topics/images/custom_image_model), refer to it with `get_image_model_string()` rather than naming `"wagtailimages.Image"` directly. See [](custom_image_model_referring_to_image_model).

Images are not rendered directly. Instead, the [`{% image %}` tag](image_tag) generates a _rendition_ - a resized version of the original - at the size you ask for:

```html+django
{% load wagtailimages_tags %}

{% if page.image %}
    {% image page.image fill-320x240 %}
{% endif %}
```

For rendition options, alt text handling, and generating renditions in Python rather than templates, see [](image_tag) and [](image_renditions).

## Using images within `RichTextField`

Images can be inserted into a [`RichTextField`](rich_text_field) by editors. The `image` feature is enabled by default, so no configuration is needed.

If you pass an explicit `features` list, include `"image"` to keep it available:

```python
# models.py

from wagtail.fields import RichTextField


class BlogPage(Page):
    # ...other fields
    body = RichTextField(blank=True, features=["bold", "italic", "ol", "image"])

    panels = [
        # ...other panels
        FieldPanel("body"),
    ]
```

See [](rich_text_features) for the full list of features, and [Changing rich text representation](/advanced_topics/images/changing_rich_text_representation) for customizing how images are rendered.

## Using images within `StreamField`

`StreamField` provides a content editing model suitable for pages that do not follow a fixed structure. Use [`ImageBlock`](streamfield_imageblock) to add an image to a `StreamField`:

```python
# models.py

from wagtail.fields import StreamField
from wagtail.images.blocks import ImageBlock


class BlogPage(Page):
    # ... other fields

    body = StreamField(
        [("image", ImageBlock())],
        blank=True,
    )

    panels = [
        # ... other panels
        FieldPanel("body"),
    ]
```

In `blog_page.html`, render the block as you would any other image:

```html+django
{% load wagtailimages_tags %}

{% for block in page.body %}
    {% image block.value width-800 %}
{% endfor %}
```

`ImageBlock` lets editors mark an image as decorative or give it context-specific alt text, which `ImageChooserBlock` does not. Prefer it for new projects - see [Accessibility considerations](/advanced_topics/accessibility_considerations).

## Working with images and collections

Images in Wagtail can be organized within [collections](https://guide.wagtail.org/en/how-to-guides/manage-collections/). Collections provide a way to group related images, and can be used to filter images in your own views:

```python
# models.py

from wagtail.images import get_image_model


class GalleryPage(Page):
    collection = models.ForeignKey(
        "wagtailcore.Collection",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name="Image collection",
    )

    content_panels = Page.content_panels + [
        FieldPanel("collection"),
    ]

    def get_context(self, request):
        context = super().get_context(request)
        context["images"] = get_image_model().objects.filter(collection=self.collection)
        return context
```

Here's an example template to render the collection:

```html+django
{% extends "base.html" %}
{% load wagtailimages_tags %}

{% block content %}
    {% for image in images %}
        {% image image width-400 %}
    {% endfor %}
{% endblock %}
```

## Making images private

If you want to restrict access to certain images, you can place them in [private collections](private_collections).

Private collections are not publicly accessible, and their contents are only available to users with the appropriate permissions.

## Serving images outside Wagtail

Renditions are normally generated by the `{% image %}` tag or `get_rendition()`. If an external system such as a mobile app needs to request image versions by URL, Wagtail provides a dynamic serve view. It is optional and not needed by most projects - see [](using_images_outside_wagtail).

## API access

Images in Wagtail can be accessed through the API via the `wagtail.images.api.v2.views.ImagesAPIViewSet`. This allows you to programmatically interact with images, retrieve their details, and perform various operations.

For more details, you can refer to the [API section](api_v2_configure_endpoints) that provides additional information and usage examples.
