(jinja2)=

# Jinja2 template support

Wagtail supports Jinja2 templating for all front end features. More information on each of the template tags below can be found in the [](writing_templates) documentation.

## Configuring Django

Django needs to be configured to support Jinja2 templates. As the Wagtail admin is written using standard Django templates, Django has to be configured to use **both** templating engines. Add the Jinja2 template backend configuration to the `TEMPLATES` setting for your app as shown here:

```python
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # ... the rest of the existing Django template configuration ...
    },
    {
        'BACKEND': 'django.template.backends.jinja2.Jinja2',
        'APP_DIRS': True,
        'OPTIONS': {
            'extensions': [
                'wagtail.jinja2tags.core',
                'wagtail.admin.jinja2tags.userbar',
                'wagtail.images.jinja2tags.images',
            ],
        },
    }
]
```

Jinja templates must be placed in a `jinja2/` directory in your app. For example, the standard template location for an `EventPage` model in an `events` app would be `events/jinja2/events/event_page.html`.

By default, the Jinja environment does not have any Django functions or filters. The Django documentation has more information on {class}`django.template.backends.jinja2.Jinja2` (configuring Jinja for Django).

## `self` in templates

In Django templates, `self` can be used to refer to the current page, stream block, or field panel. In Jinja, `self` is reserved for internal use. When writing Jinja templates, use `page` to refer to pages, `value` for stream blocks, and `field_panel` for field panels.

## Template tags, functions & filters

### `fullpageurl()`

Generate an absolute URL (`http://example.com/foo/bar/`) for a Page instance:

```html+jinja
<meta property="og:url" content="{{ fullpageurl(page) }}" />
```

See [](fullpageurl_tag) for more information.

### `pageurl()`

Generate a URL (`/foo/bar/`) for a Page instance:

```html+jinja
<a href="{{ pageurl(page.more_information) }}">More information</a>
```

See [](pageurl_tag) for more information

### `slugurl()`

Generate a URL for a Page with a slug:

```html+jinja
<a href="{{ slugurl("about") }}">About us</a>
```

See [](slugurl_tag) for more information

### `image()`

Resize an image, and render an `<img>` tag:

```html+jinja
{{ image(page.header_image, "fill-1024x200", class="header-image") }}
```

Or resize an image and retrieve the resized image object (rendition) for more bespoke use:

```html+jinja
{% set background=image(page.background_image, "max-1024x1024") %}
<div class="wrapper" style="background-image: url({{ background.url }});"></div>
```

When working with SVG images, you can use `preserve_svg` in the filter string to prevent operations that would require rasterizing the SVG. When preserve_svg is set to True and the image is an SVG, operations that would require rasterization (like format conversion) will be automatically filtered out, ensuring SVGs remain as vector graphics. This is especially useful in loops processing both raster images and SVGs.

```html+jinja
{{ image(page.svg_image, "width-400|format-webp|preserve_svg") }}
```

See [](image_tag) for more information

### `srcset_image()`

Resize an image, and render an `<img>` tag including `srcset` with multiple sizes.
Browsers will select the most appropriate image to load based on [responsive image rules](https://developer.mozilla.org/en-US/docs/Learn/HTML/Multimedia_and_embedding/Responsive_images).
The [`sizes`](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/img#sizes) attribute is essential unless you store the output of `srcset_image` for later use.

```html+jinja
{{ srcset_image(page.photo, "width-{400,800}", sizes="(max-width: 600px) 400px, 80vw") }}
```

This outputs:

```html
<img srcset="/media/images/pied-wagtail.width-400.jpg 400w, /media/images/pied-wagtail.width-800.jpg 800w" src="/media/images/pied-wagtail.width-400.jpg" alt="A pied Wagtail" sizes="(max-width: 600px) 400px, 80vw" width="400" height="300">
```

Or resize an image and retrieve the renditions for more bespoke use:

```html+jinja
{% set bg=srcset_image(page.background_image, "max-{512x512,1024x1024}") %}
<div class="wrapper" style="background-image: image-set(url({{ bg.renditions[0].url }}) 1x, url({{ bg.renditions[1].url }}) 2x);"></div>
```

When working with SVG images, you can use `preserve_svg` in the filter string to prevent operations that would require rasterizing the SVG.

```html+jinja
{{ srcset_image(page.svg_image, "width-400|format-webp|preserve_svg") }}
```

### `picture()`

Resize or convert an image, rendering a `<picture>` tag including multiple `source` formats with `srcset` for multiple sizes, and a fallback `<img>` tag.
Browsers will select the [first supported image format](https://web.dev/learn/design/picture-element/#image_formats), and pick a size based on [responsive image rules](https://developer.mozilla.org/en-US/docs/Learn/HTML/Multimedia_and_embedding/Responsive_images).

`picture` can render an image in multiple formats:

```html+jinja
{{ picture(page.photo, "format-{avif,webp,jpeg}|width-400") }}
```

This outputs:

```html
<picture>
    <source srcset="/media/images/pied-wagtail.width-400.avif" type="image/avif">
    <source srcset="/media/images/pied-wagtail.width-400.webp" type="image/webp">
    <img src="/media/images/pied-wagtail.width-400.jpg" alt="A pied Wagtail" width="400" height="300">
</picture>
```

Or render multiple formats and multiple sizes like `srcset_image` does. The [`sizes`](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/img#sizes) attribute is essential when the picture tag renders images in multiple sizes:

```html+jinja
{{ picture(page.header_image, "format-{avif,webp,jpeg}|width-{400,800}", sizes="80vw") }}
```

This outputs:

```html
<picture>
    <source sizes="80vw" srcset="/media/images/pied-wagtail.width-400.avif 400w, /media/images/pied-wagtail.width-800.avif 800w" type="image/avif">
    <source sizes="80vw" srcset="/media/images/pied-wagtail.width-400.webp 400w, /media/images/pied-wagtail.width-800.webp 800w" type="image/webp">
    <img sizes="80vw" srcset="/media/images/pied-wagtail.width-400.jpg 400w, /media/images/pied-wagtail.width-800.jpg 800w" src="/media/images/pied-wagtail.width-400.jpg" alt="A pied Wagtail" width="400" height="300">
</picture>
```

Or resize an image and retrieve the renditions for more bespoke use:

```html+jinja
{% set bg=picture(page.background_image, "format-{avif,jpeg}|max-{512x512,1024x1024}") %}
<div class="wrapper" style="background-image: image-set(url({{ bg.formats['avif'][0].url }}) 1x type('image/avif'), url({{ bg.formats['avif'][1].url }}) 2x type('image/avif'), url({{ bg.formats['jpeg'][0].url }}) 1x type('image/jpeg'), url({{ bg.formats['jpeg'][1].url }}) 2x type('image/jpeg'));"></div>
```

For SVG images, you can use `preserve_svg` in the filter string to ensure they remain as vector graphics:

```html+jinja
{{ picture(page.header_image, "format-{avif,webp,jpeg}|width-{400,800}|preserve_svg", sizes="80vw") }}
```

### `|richtext`

Transform Wagtail's internal HTML representation, expanding internal references to pages and images.

```html+jinja
{{ page.body|richtext }}
```

See [](rich_text_filter) for more information

### `wagtail_site`

Returns the Site object corresponding to the current request.

```html+jinja
{{ wagtail_site().site_name }}
```

See [](wagtail_site_tag) for more information

### `wagtailuserbar()`

Output the Wagtail contextual flyout menu for editing pages from the front end

```html+jinja
{{ wagtailuserbar() }}
```

See [](wagtailuserbar_tag) for more information

### `{% include_block %}`

Output the HTML representation for the stream content as a whole, as well as for each individual block.

Allows to pass template context (by default) to the StreamField template.

```html+jinja
{% include_block page.body %}
{% include_block page.body with context %} {# The same as the previous #}
{% include_block page.body without context %}
```

See [StreamField template rendering](streamfield_template_rendering) for more information.

```{note}
The ``{% include_block %}`` tag is designed to closely follow the syntax and behavior
of Jinja's ``{% include %}``, so it does not implement the Django version's feature of
only passing specified variables into the context.
```
