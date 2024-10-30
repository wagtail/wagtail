(customizing_richtext_output)=

# Customizing richtext output
In some cases, it might be necessary to customize the output of a [RichTextField](rich_text_field), or a `RichTextBlock` within a [StreamField](streamfield_topic).

This can be done through a simple [Django template filter](https://docs.djangoproject.com/en/5.0/howto/custom-template-tags/).

## Add a class to HTML tags

This example shows how to add a class to all `<p>` tags in a RichTextField or a RichTextBlock.

In your templatetag library file, add a new filter:

```python
from bs4 import BeautifulSoup
from django import template
from django.utils.html import mark_safe
from wagtail.rich_text import RichText

register = template.Library()

# [...]

@register.filter
def richtext_p_add_class(value, class_name: str):
    """
    Adds a CSS class to a Richtext-generated paragraph.

    Intended to be used right after a `| richext` filter in case of a RichTextField
    (not necessary for a RichTextBlock)
    """

    if not class_name:
        return value

    if isinstance(value, RichText):
        # In case of a RichTextBlock, first render it
        value = str(value)

    soup = BeautifulSoup(value, "html.parser")

    paragraphs = soup.find_all("p")

    for p in paragraphs:
        p["class"] = p.get("class", []) + [class_name]

    return mark_safe(str(soup))
```

Now, in your templates, you can add the following (don't forget to load your templatetag library):

For a RichTextField:

```html+django
{{ page.sample_richtext_fied | richtext | richtext_p_add_class:"new_class" }}
```

For a RichTextBlock:

```html+django
{{ value.sample_richtext_block | richtext_p_add_class:"new_class" }}
```
