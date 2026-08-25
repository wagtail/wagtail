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

To add an image to a Wagtail page, add a `ForeignKey` to the image model and expose it with a [`FieldPanel`](wagtail.admin.panels.FieldPanel) in your page model.

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

If your project uses a [custom image model](custom_image_model), refer to it with `get_image_model_string()` instead of `"wagtailimages.Image"`. See [](custom_image_model_referring_to_image_model).

## Using images in templates

Wagtail provides a set of opinionated [image template tags](image_tag) to automatically convert source images into [multiple formats](multiple_formats) and [multiple sizes](responsive_images). Those generated images are called _renditions_, re-processed versions of an image for size, format, quality, or other transformations. 

For example, the [`picture` template tag](multiple_formats) will automatically create a `<picture>` element with multiple formats and sizes, letting the browser choose the one it prefers. For example:

```html+django
{% load wagtailimages_tags %}

{% picture myimage format-{avif,webp,jpeg} width-1000 %}
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

See [](rich_text_features) for the full list of features, and [](changing_rich_text_representation) for customizing how images are rendered.

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
    {% picture block.value format-{avif,webp,jpeg} width-800 %}
{% endfor %}
```

`ImageBlock` lets editors mark an image as decorative or give it context-specific alt text, which `ImageChooserBlock` does not. See our content modeling guidance, [Alt text for images](content_modeling).

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
{% load wagtailimages_tags %}

{% block content %}
    {% for img in images %}
        {% image img width-400 %}
    {% endfor %}
{% endblock %}
```

## Making images private

If you want to restrict access to certain images, you can place them in [private collections](private_collections).

Private collections are not publicly accessible, and their contents are only available to users with the appropriate permissions.

## Serving images outside Wagtail

For server-rendered sites, renditions are normally generated by Wagtail’s image template tags or `get_rendition()`. If an external system such as a mobile app or headless front-end needs to request image versions by URL, Wagtail provides a dynamic serve view. See [](using_images_outside_wagtail).

## API access

Images can also be accessed via Wagtail’s built-in API support. You can directly [access images as part of pages data](api_v2_images).

To access images directly, you can also [configure image endpoints for the v2 API](api_v2_configure_endpoints).

```{versionadded} 8.0
Wagtail’s new v3 API is based on Django Ninja and provides OpenAPI schemas.
```

The [v3 images API endpoints](api_v3_images) are also available whenever the v3 API is enabled, and provide more advanced features such as "write" operations.
