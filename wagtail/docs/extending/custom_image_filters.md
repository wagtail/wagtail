(custom_image_filters)=

# Custom image filters

Wagtail comes with [various image operations](image_tag). To add custom image operation, add `register_image_operations` hook to your `wagtail_hooks.py` file.

In this example, the `willow.image` is a Pillow Image instance. If you use another image library, or like to support multiple image libraries, you need to update the filter code accordingly. See the [Willow documentation](https://willow.wagtail.org/stable/) for more information.

```python
from PIL import ImageFilter

from wagtail import hooks
from wagtail.images.image_operations import FilterOperation


class BlurOperation(FilterOperation):
    def construct(self, radius):
        self.radius = int(radius)

    def run(self, willow, image, env):
        willow.image = willow.image.filter(ImageFilter.GaussianBlur(radius=self.radius))
        return willow


@hooks.register("register_image_operations")
def register_image_operations():
    return [
        ("blur", BlurOperation),
    ]
```

Use the filter in a template, like so:

```html+Django
{% load wagtailimages_tags %}

{% image page.photo width-400 blur-7 %}
```

If your custom image filter depends on fields within the `Image`, for instance those defining the focal point, add a `vary_fields` property listing those field names to the subclassed `FilterOperation`. This ensures that a new rendition is created whenever the focal point is changed:

```python
class BlurOutsideFocusPointOperation(FilterOperation):
    vary_fields = (
        "focal_point_width",
        "focal_point_height",
        "focal_point_x",
        "focal_point_y",
    )
    # ...
```
