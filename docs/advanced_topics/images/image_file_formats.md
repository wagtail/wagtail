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

We recommend using the [`picture` template tag](multiple_formats) or `format-*` filter to intentionally decide on correct output formats. Wagtail provides default format conversions that are only intended as a fallback. With this fallback conversion, `bmp` images are converted to `png` and `heic` images are converted to `jpeg`. Other image formats are served as-is.

The default conversion mapping can be changed by setting the `WAGTAILIMAGES_FORMAT_CONVERSIONS` setting to a dictionary, which maps the input type to an output type. For example:

```python
WAGTAILIMAGES_FORMAT_CONVERSIONS = {
    "bmp": "png",
    "avif": "png",
    "webp": "png",
}
```
