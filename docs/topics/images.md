(image_tag)=

# How to use images in templates

The `image` tag inserts an XHTML-compatible `img` element into the page, setting its `src`, `width`, `height` and `alt`. See also [](image_tag_alt).

The syntax for the tag is thus:

```html+django
{% image [image] [resize-rule] %}
```

**Both the image and resize rule must be passed to the template tag.**

For example:

```html+django
{% load wagtailimages_tags %}
...

<!-- Display the image scaled to a width of 400 pixels: -->
{% image page.photo width-400 %}

<!-- Display it again, but this time as a square thumbnail: -->
{% image page.photo fill-80x80 %}
```

In the above syntax example `[image]` is the Django object referring to the image. If your page model defined a field called "photo" then `[image]` would probably be `page.photo`. The `[resize-rule]` defines how the image is to be resized when inserted into the page. Various resizing methods are supported, to cater to different use cases (e.g. lead images that span the whole width of the page, or thumbnails to be cropped to a fixed size).

Note that a space separates `[image]` and `[resize-rule]`, but the resize rule must not contain spaces. The width is always specified before the height. Resized images will maintain their original aspect ratio unless the `fill` rule is used, which may result in some pixels being cropped.

## Available resizing methods

The available resizing methods are as follows:

### `max`

(takes two dimensions)

```html+django
{% image page.photo max-1000x500 %}
```

Fit **within** the given dimensions.

The longest edge will be reduced to the matching dimension specified. For example, a portrait image of width 1000 and height 2000, treated with the `max-1000x500` rule (a landscape layout) would result in the image being shrunk so the _height_ was 500 pixels and the width was 250.

![Example of max filter on an image](../_static/images/image_filter_max.png)

Example: The image will keep its proportions but fit within the max (green line) dimensions provided.

### `min`

(takes two dimensions)

```html+django
{% image page.photo min-500x200 %}
```

**Cover** the given dimensions.

This may result in an image slightly **larger** than the dimensions you specify. A square image of width 2000 and height 2000, treated with the `min-500x200` rule would have its height and width changed to 500, i.e matching the _width_ of the resize-rule, but greater than the height.

![Example of min filter on an image](../_static/images/image_filter_min.png)

Example: The image will keep its proportions while filling at least the min (green line) dimensions provided.

### `width`

(takes one dimension)

```html+django
{% image page.photo width-640 %}
```

Reduces the width of the image to the dimension specified.

### `height`

(takes one dimension)

```html+django
{% image page.photo height-480 %}
```

Reduces the height of the image to the dimension specified.

### `scale`

(takes percentage)

```html+django
{% image page.photo scale-50 %}
```

Resize the image to the percentage specified.

### `fill`

(takes two dimensions and an optional `-c` parameter)

```html+django
{% image page.photo fill-200x200 %}
```

Resize and **crop** to fill the **exact** dimensions specified.

This can be particularly useful for websites requiring square thumbnails of arbitrary images. For example, a landscape image of width 2000 and height 1000 treated with the `fill-200x200` rule would have its height reduced to 200, then its width (ordinarily 400) cropped to 200.

This resize-rule will crop to the image's focal point if it has been set. If not, it will crop to the centre of the image.

![Example of fill filter on an image](../_static/images/image_filter_fill.png)

Example: The image is scaled and also cropped (red line) to fit as much of the image as possible within the provided dimensions.

**On images that won't upscale**

It's possible to request an image with `fill` dimensions that the image can't support without upscaling. e.g. an image of width 400 and height 200 requested with `fill-400x400`. In this situation the _ratio of the requested fill_ will be matched, but the dimension will not. So that example 400x200 image (a 2:1 ratio) could become 200x200 (a 1:1 ratio, matching the resize-rule).

**Cropping closer to the focal point**

By default, Wagtail will only crop enough to change the aspect ratio of the image to match the ratio in the resize-rule.

In some cases (e.g. thumbnails), it may be preferable to crop closer to the focal point, so that the subject of the image is more prominent.

You can do this by appending `-c<percentage>` at the end of the resize-rule. For example, if you would like the image to be cropped as closely as possible to its focal point, add `-c100`:

```html+django
{% image page.photo fill-200x200-c100 %}
```

This will crop the image as much as it can, without cropping into the focal point.

If you find that `-c100` is too close, you can try `-c75` or `-c50`. Any whole number from 0 to 100 is accepted.

![Example of fill filter on an image with a focal point set](../_static/images/image_filter_fill_focal.png)

Example: The focal point is set off centre so the image is scaled and also cropped like fill, however the center point of the crop is positioned closer the focal point.

![Example of fill and closeness filter on an image with a focal point set](../_static/images/image_filter_fill_focal_close.png)

Example: With `-c75` set, the final crop will be closer to the focal point.

### `original`

(takes no dimensions)

```html+django
{% image page.photo original %}
```

Renders the image at its original size.

```{note}
Wagtail does not allow deforming or stretching images. Image dimension ratios will always be kept. Wagtail also *does not support upscaling*. Small images forced to appear at larger sizes will "max out" at their native dimensions.
```

(image_tag_alt)=

## More control over the `img` tag

Wagtail provides two shortcuts to give greater control over the `img` element:

**1. Adding attributes to the {% image %} tag**

Extra attributes can be specified with the syntax `attribute="value"`:

```html+django
{% image page.photo width-400 class="foo" id="bar" %}
```

You can set a more relevant `alt` attribute this way, overriding the one automatically generated from the title of the image. The `src`, `width`, and `height` attributes can also be overridden, if necessary.

**2. Generating the image "as foo" to access individual properties**

Wagtail can assign the image data to another variable using Django's `as` syntax:

```html+django
{% image page.photo width-400 as tmp_photo %}

<img src="{{ tmp_photo.url }}" width="{{ tmp_photo.width }}"
    height="{{ tmp_photo.height }}" alt="{{ tmp_photo.alt }}" class="my-custom-class" />
```

```{note}
The image property used for the `src` attribute is `image.url`, not `image.src`.
```

This syntax exposes the underlying image Rendition (`tmp_photo`) to the developer. A "Rendition" contains the information specific to the way you've requested to format the image using the resize-rule, i.e. dimensions and source URL. The following properties are available:

### `url`

URL to the resized version of the image. This may be a local URL (such as `/static/images/example.jpg`) or a full URL (such as `https://assets.example.com/images/example.jpg`), depending on how static files are configured.

### `width`

Image width after resizing.

### `height`

Image height after resizing.

### `alt`

Alternative text for the image, typically taken from the image title.

### `attrs`

A shorthand for outputting the attributes `src`, `width`, `height` and `alt` in one go:

```html+django
<img {{ tmp_photo.attrs }} class="my-custom-class" />
```

### `full_url`

Same as `url`, but always returns a full absolute URL. This requires `BASE_URL` to be set in the project settings.

This is useful for images that will be re-used outside of the current site, such as social share images:

```html+django
<meta name="twitter:image" content="{{ tmp_photo.full_url }}">
```

If your site defines a custom image model using `AbstractImage`, any additional fields you add to an image (e.g. a copyright holder) are **not** included in the rendition.

Therefore, if you'd added the field `author` to your AbstractImage in the above example, you'd access it using `{{ page.photo.author }}` rather than `{{ tmp_photo.author }}`.

(Due to the links in the database between renditions and their parent image, you _could_ access it as `{{ tmp_photo.image.author }}`, but that has reduced readability.)

## Alternative HTML tags

The `as` keyword allows alternative HTML image tags (such as `<picture>` or `<amp-img>`) to be used.
For example, to use the `<picture>` tag:

```html+django
<picture>
    {% image page.photo width-800 as wide_photo %}
    <source srcset="{{ wide_photo.url }}" media="(min-width: 800px)">
    {% image page.photo width-400 %}
</picture>
```

And to use the `<amp-img>` tag (based on the [Mountains example](https://amp.dev/documentation/components/amp-img/#example:-specifying-a-fallback-image) from the AMP docs):

```html+django
{% image image width-550 format-webp as webp_image %}
{% image image width-550 format-jpeg as jpeg_image %}

<amp-img alt="{{ image.alt }}"
    width="{{ webp_image.width }}"
    height="{{ webp_image.height }}"
    src="{{ webp_image.url }}">
    <amp-img alt="{{ image.alt }}"
        fallback
        width="{{ jpeg_image.width }}"
        height="{{ jpeg_image.height }}"
        src="{{ jpeg_image.url }}"></amp-img>
</amp-img>
```

## Images embedded in rich text

The information above relates to images defined via image-specific fields in your model. However, images can also be embedded arbitrarily in Rich Text fields by the page editor (see [](rich-text)).

Images embedded in Rich Text fields can't be controlled by the template developer as easily. There are no image objects to work with, so the `{% image %}` template tag can't be used. Instead, editors can choose from one of a number of image "Formats" at the point of inserting images into their text.

Wagtail comes with three pre-defined image formats, but more can be defined in Python by the developer. These formats are:

### `Full width`

Creates an image rendition using `width-800`, giving the <img> tag the CSS class `full-width`.

### `Left-aligned`

Creates an image rendition using `width-500`, giving the <img> tag the CSS class `left`.

### `Right-aligned`

Creates an image rendition using `width-500`, giving the <img> tag the CSS class `right`.

```{note}
The CSS classes added to images do **not** come with any accompanying stylesheets, or inline styles. e.g. the `left` class will do nothing, by default. The developer is expected to add these classes to their front end CSS files, to define exactly what they want `left`, `right` or `full-width` to mean.
```

For more information about image formats, including creating your own, see [](rich_text_image_formats).

(output_image_format)=

## Output image format

Wagtail may automatically change the format of some images when they are resized:

-   PNG and JPEG images don't change format
-   GIF images without animation are converted to PNGs
-   BMP images are converted to PNGs
-   WebP images are converted to PNGs

It is also possible to override the output format on a per-tag basis by using the
`format` filter after the resize rule.

For example, to make the tag always convert the image to a JPEG, use `format-jpeg`:

```html+django
{% image page.photo width-400 format-jpeg %}
```

You may also use `format-png` or `format-gif`.

### Lossless WebP

You can encode the image into lossless WebP format by using the `format-webp-lossless` filter:

```html+django
{% image page.photo width-400 format-webp-lossless %}
```

(image_background_color)=

## Background colour

The PNG and GIF image formats both support transparency, but if you want to
convert images to JPEG format, the transparency will need to be replaced with a solid background colour.

By default, Wagtail will set the background to white. But if a white background doesn't fit your design, you can specify a colour using the `bgcolor` filter.

This filter takes a single argument, which is a CSS 3 or 6 digit hex code
representing the colour you would like to use:

```html+django
{# Sets the image background to black #}
{% image page.photo width-400 bgcolor-000 format-jpeg %}
```

(image_quality)=

## Image quality

Wagtail's JPEG and WebP image quality settings default to 85 (which is quite high).
This can be changed either globally or on a per-tag basis.

### Changing globally

Use the `WAGTAILIMAGES_JPEG_QUALITY` and `WAGTAILIMAGES_WEBP_QUALITY` settings to change the global defaults of JPEG and WebP quality:

```python
# settings.py

# Make low-quality but small images
WAGTAILIMAGES_JPEG_QUALITY = 40
WAGTAILIMAGES_WEBP_QUALITY = 45
```

Note that this won't affect any previously generated images so you may want to delete all renditions so they can regenerate with the new setting. This can be done from the Django shell:

```python
# Replace this with your custom rendition model if you use one
>>> from wagtail.images.models import Rendition
>>> Rendition.objects.all().delete()
```

You can also directly use the image management command from the console for regenerating the renditions:

```console
$ ./manage.py wagtail_update_image_renditions --purge
```

You can read more about this command from [](wagtail_update_image_renditions)

### Changing per-tag

It's also possible to have different JPEG and WebP qualities on individual tags by using `jpegquality` and `webpquality` filters. This will always override the default setting:

```html+django
{% image page.photo_jpeg width-400 jpegquality-40 %}
{% image page.photo_webp width-400 webpquality-50 %}
```

Note that this will have no effect on PNG or GIF files. If you want all images to be low quality, you can use this filter with `format-jpeg` or `format-webp` (which forces all images to output in JPEG or WebP format):

```html+Django
{% image page.photo width-400 format-jpeg jpegquality-40 %}
{% image page.photo width-400 format-webp webpquality-50 %}
```

### Generating image renditions in Python

All of the image transformations mentioned above can also be used directly in Python code.
See [](image_renditions).
