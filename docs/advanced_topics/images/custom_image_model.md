(custom_image_model)=

# Custom image models

The `Image` model can be customized, allowing additional fields to be added
to images.

To do this, you need to add two models to your project:

-   The image model itself that inherits from `wagtail.images.models.AbstractImage`. This is where you would add your additional fields
-   The renditions model that inherits from `wagtail.images.models.AbstractRendition`. This is used to store renditions for the new model.

Here's an example:

```python
# models.py
from django.db import models

from wagtail.images.models import Image, AbstractImage, AbstractRendition


class CustomImage(AbstractImage):
    # Add any extra fields to image here

    # To add a caption field:
    # caption = models.CharField(max_length=255, blank=True)

    admin_form_fields = Image.admin_form_fields + (
        # Then add the field names here to make them appear in the form:
        # 'caption',
    )

    @property
    def default_alt_text(self):
        # Force editors to add specific alt text if description is empty.
        # Do not use image title which is typically derived from file name.
        return getattr(self, "description", None)

class CustomRendition(AbstractRendition):
    image = models.ForeignKey(CustomImage, on_delete=models.CASCADE, related_name='renditions')

    class Meta:
       constraints = [
            models.UniqueConstraint(
                fields=("image", "filter_spec", "focal_point_key"),
                name="unique_rendition",
            )
        ]
```

Then set the `WAGTAILIMAGES_IMAGE_MODEL` setting to point to it:

```python
WAGTAILIMAGES_IMAGE_MODEL = 'images.CustomImage'
```

## Migrating from the builtin image model

When changing an existing site to use a custom image model, no images will
be copied to the new model automatically. Copying old images to the new
model would need to be done manually with a
{ref}`data migration <django:data-migrations>`.

Any templates that reference the builtin image model will still continue to
work as before but would need to be updated in order to see any new images.

(custom_image_model_referring_to_image_model)=

## Referring to the image model

```{eval-rst}
.. module:: wagtail.images

.. autofunction:: get_image_model

.. autofunction:: get_image_model_string
```

(custom_image_model_upload_location)=

## Overriding the upload location

The following methods can be overridden on your custom `Image` or `Rendition` models to customize how the original and rendition image files get stored.

```{eval-rst}
.. automodule:: wagtail.images.models
    :no-index:

.. class:: AbstractImage
    :no-index-entry:

    .. automethod:: get_upload_to

.. class:: AbstractRendition
    :no-index-entry:

    .. automethod:: get_upload_to
```

Refer to the Django [`FileField.upload_to`](django.db.models.FileField.upload_to) function to further understand how the function works.
