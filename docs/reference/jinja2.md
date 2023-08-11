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

See [](image_tag) for more information

### `srcset_image()`

Resize an image, and render an `<img>` tag including `srcset` with multiple sizes.
Browsers will select the most appropriate image to load based on [responsive image rules](https://developer.mozilla.org/en-US/docs/Learn/HTML/Multimedia_and_embedding/Responsive_images).
The `sizes` attribute is mandatory unless you store the output of `srcset_image` for later use.

```html+jinja
{{ srcset_image(page.header_image, "fill-{512x100,1024x200}", sizes="100vw", class="header-image") }}
```

Or resize an image and retrieve the renditions for more bespoke use:

```html+jinja
{% set bg=srcset_image(page.background_image, "max-{512x512,1024x1024}") %}
<div class="wrapper" style="background-image: image-set(url({{ bg.renditions[0].url }}) 1x, url({{ bg.renditions[1].url }}) 2x);"></div>
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
The ``{% include_block %}`` tag is designed to closely follow the syntax and behaviour
of Jinja's ``{% include %}``, so it does not implement the Django version's feature of
only passing specified variables into the context.
```
