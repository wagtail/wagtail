(changing_rich_text_representation)=

# Changing rich text representation

The HTML representation of an image in rich text can be customised - for example, to display captions or custom fields.

To do this requires subclassing `Format` (see [](rich_text_image_formats)), and overriding its `image_to_html` method.

You may then register formats of your subclass using `register_image_format` as usual.

```python
# image_formats.py
from wagtail.images.formats import Format, register_image_format


class SubclassedImageFormat(Format):

    def image_to_html(self, image, alt_text, extra_attributes=None):

        custom_html = # the custom HTML representation of your image here
                        # in Format, the image's rendition.img_tag(extra_attributes) is used to generate the HTML
                        # representation

        return custom_html


register_image_format(
    SubclassedImageFormat('subclassed_format', 'Subclassed Format', classnames, filter_spec)
)
```

As an example, let's say you want the alt text to be displayed as a caption for the image as well:

```python
# image_formats.py
from django.utils.html import format_html
from wagtail.images.formats import Format, register_image_format


class CaptionedImageFormat(Format):

    def image_to_html(self, image, alt_text, extra_attributes=None):

        default_html = super().image_to_html(image, alt_text, extra_attributes)

        return format_html("{}<figcaption>{}</figcaption>", default_html, alt_text)


register_image_format(
    CaptionedImageFormat('captioned_fullwidth', 'Full width captioned', 'bodytext-image', 'width-750')
)
```

```{note}
Any custom HTML image features will not be displayed in the Draftail editor, only on the published page.
```
