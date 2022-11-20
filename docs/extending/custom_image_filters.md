(custom_image_filters)=

# Custom image filters

Wagtail comes with [various image operations](image_tag). To add custom image operation, add `register_image_operations` hook to your `wagtail_hooks.py` file.

In this example, the `willow.image` is a Pillow Image instance. If you use another image library, or like to support multiple image libraries, you need to update the filter code accordingly. See the [Willow documentation](https://willow.readthedocs.io/en/latest/index.html) for more information.

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
