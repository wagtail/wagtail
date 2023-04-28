(wagtailsnippets_registering)=

# Registering snippets

Snippets can be registered using the `register_snippet` decorator or function. Here's an example snippet model:

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
        FieldPanel('url'),
        FieldPanel('text'),
    ]

    def __str__(self):
        return self.text
```

The `Advert` model uses the basic Django model class and defines two properties: `url` and `text`. The editing interface is very close to that provided for `Page`-derived models, with fields assigned in the `panels` (or `edit_handler`) property. Unless configured further, snippets do not use multiple tabs of fields, nor do they provide the "save as draft" or "submit for moderation" features.

`@register_snippet` tells Wagtail to treat the model as a snippet. The `panels` list defines the fields to show on the snippet editing page. It's also important to provide a string representation of the class through `def __str__(self):` so that the snippet objects make sense when listed in the Wagtail admin.
