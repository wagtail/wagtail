(wagtailsnippets_registering)=

# Registering snippets

Snippets can be registered using `register_snippet` as a decorator or as a function. The latter is recommended, but the decorator is provided for convenience and backward compatibility.

## Using `@register_snippet` as a decorator

Snippets can be registered using the `@register_snippet` decorator on the Django model. Here's an example snippet model:

```python
from django.db import models

from wagtail.admin.panels import FieldPanel
from wagtail.snippets.models import register_snippet

# ...

@register_snippet
class Advert(models.Model):
    url = models.URLField(null=True, blank=True)
    text = models.CharField(max_length=255)

    panels = [
        FieldPanel("url"),
        FieldPanel("text"),
    ]

    def __str__(self):
        return self.text
```

The `Advert` model uses the basic Django model class and defines two properties: `url` and `text`. The editing interface is very close to that provided for `Page`-derived models, with fields assigned in the `panels` (or `edit_handler`) property. Unless configured further, snippets do not use multiple tabs of fields, nor do they provide the "save as draft" or "submit for moderation" features.

`@register_snippet` tells Wagtail to treat the model as a snippet. The `panels` list defines the fields to show on the snippet editing page. It's also important to provide a string representation of the class through `def __str__(self):` so that the snippet objects make sense when listed in the Wagtail admin.

## Using `register_snippet` as a function

While the `@register_snippet` decorator is convenient, the recommended way to register snippets is to use `register_snippet` as a function in your [`wagtail_hooks.py`](admin_hooks) file. For example:

```python
# myapp/wagtail_hooks.py
from wagtail.snippets.models import register_snippet

from myapp.models import Advert

register_snippet(Advert)
```

Registering snippets in this way allows you to add further customizations using a custom {class}`~wagtail.snippets.views.snippets.SnippetViewSet` class later. This also provides a better separation between your Django model and Wagtail-specific concerns. For example, instead of defining the `panels` or `edit_handler` on the model class, they can be defined on the `SnippetViewSet` class:

```python
# myapp/wagtail_hooks.py
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet

from myapp.models import Advert


class AdvertViewSet(SnippetViewSet):
    model = Advert

    panels = [
        FieldPanel("url"),
        FieldPanel("text"),
    ]

# Instead of using @register_snippet as a decorator on the model class,
# register the snippet using register_snippet as a function and pass in
# the custom SnippetViewSet subclass.
register_snippet(AdvertViewSet)
```

If you would like to do more customizations of the panels, you can override the {meth}`~wagtail.snippets.views.snippets.SnippetViewSet.get_edit_handler` method. Further customizations will be explained later in [](wagtailsnippets_custom_admin_views).
