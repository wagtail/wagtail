(image_file_formats)=

# Image file formats

## Using the picture element

The [picture element](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/picture)
can be used with the `format-<type>` image operation to specify different
image formats and let the browser choose the one it prefers. For example:

```python
{% load wagtailimages_tags %}

<picture>
    {% image myimage width-1000 format-avif as image_avif %}
    <source srcset="{{ image_avif.url }}" type="image/avif">

    {% image myimage width-1000 format-webp as image_webp %}
    <source srcset="{{ image_webp.url }}" type="image/webp">

    {% image myimage width-1000 format-png as image_png %}
    <source srcset="{{ image_png.url }}" type="image/png">

    {% image myimage width-1000 format-png %}
</picture>
```

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
