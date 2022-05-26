(image_file_formats)=

# Image file formats

## Using the picture element

The [picture element](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/picture)
can be used with the `format-<type>` image operation to specify different
image formats and let the browser choose the one it prefers. For example:

```python
{% load wagtailimages_tags %}

<picture>
    {% image myimage width-1000 format-webp as image_webp %}
    <source srcset="{{ image_webp.url }}" type="image/webp">

    {% image myimage width-1000 format-png as image_png %}
    <source srcset="{{ image_png.url }}" type="image/png">

    {% image myimage width-1000 format-png %}
</picture>
```

### Customising output formats

By default all `bmp` and `webp` images are converted to the `png` format
when no image output format is given.

The default conversion mapping can be changed by setting the
`WAGTAILIMAGES_FORMAT_CONVERSIONS` to a dictionary which maps the input type
to an output type.

For example:

```python
    WAGTAILIMAGES_FORMAT_CONVERSIONS = {
        'bmp': 'jpeg',
        'webp': 'webp',
    }
```

will convert `bmp` images to `jpeg` and disable the default `webp`
to `png` conversion.
