(image_file_formats)=

# Image file formats

## Using the picture element

Wagtail provides the [`picture` template tag](multiple_formats) to render a [picture element](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/picture) with multiple image formats, letting the browser choose the one it prefers. For example:

```html+django
{% load wagtailimages_tags %}

{% picture myimage format-{avif,webp,jpeg} width-1000 %}
```

(customizing_output_formats)=

### Customizing output formats

By default, `bmp` images are converted to the `png` format and `heic` images
are converted to `jpeg` when no image output format is given. `avif` and `webp`
images are served as-is, as these formats are widely supported by browsers.

The default conversion mapping can be changed by setting the
`WAGTAILIMAGES_FORMAT_CONVERSIONS` to a dictionary, which maps the input type
to an output type.

For example:

```python
    WAGTAILIMAGES_FORMAT_CONVERSIONS = {
        'avif': 'png',
        'bmp': 'jpeg',
        'webp': 'png',
    }
```

will convert `avif` and `webp` images to `png` and `bmp` images to `jpeg`.
