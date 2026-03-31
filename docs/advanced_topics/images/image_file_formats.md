(image_file_formats)=

# Image file formats

## Using the picture element

Wagtail provides the `picture` tag to render a [picture element](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/picture) with multiple image formats, letting the browser choose the one it prefers. For example:

```html+django
{% load wagtailimages_tags %}

{% picture myimage format-{avif,webp,jpeg} width-1000 %}
```

This outputs:

```html
<picture>
    <source srcset="/media/images/myimage.width-1000.avif" type="image/avif">
    <source srcset="/media/images/myimage.width-1000.webp" type="image/webp">
    <img src="/media/images/myimage.width-1000.jpg" alt="My image" width="1000" height="750">
</picture>
```

The browser [picks the first format it supports](https://web.dev/learn/design/picture-element/#source), or falls back to the `<img>` element. See [](multiple_formats) for full documentation.

(customizing_output_formats)=

### Customizing output formats

By default, all `avif`, `bmp` and `webp` images are converted to the `png` format
when no image output format is given, and `heic` images are converted to `jpeg`.

The default conversion mapping can be changed by setting the
`WAGTAILIMAGES_FORMAT_CONVERSIONS` to a dictionary, which maps the input type
to an output type.

For example:

```python
    WAGTAILIMAGES_FORMAT_CONVERSIONS = {
        'avif': 'avif',
        'bmp': 'jpeg',
        'webp': 'webp',
    }
```

will convert `bmp` images to `jpeg` and disable the default `avif` and `webp`
to `png` conversion.
