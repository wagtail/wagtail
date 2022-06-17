# Typed table block

The `typed_table_block` module provides a StreamField block type for building tables consisting of mixed data types. Developers can specify a set of block types (such as `RichTextBlock` or `FloatBlock`) to be available as column types; page authors can then build up tables of any size by choosing column types from that list, in much the same way that they would insert blocks into a StreamField. Within each column, authors enter data using the standard editing control for that field (such as the Draftail editor for rich text cells).

## Installation

Add `"wagtail.contrib.typed_table_block"` to your INSTALLED_APPS:

```python
INSTALLED_APPS = [
    ...
    "wagtail.contrib.typed_table_block",
]
```

## Usage

`TypedTableBlock` can be imported from the module `wagtail.contrib.typed_table_block.blocks` and used within a StreamField definition. Just like `StructBlock` and `StreamBlock`, it accepts a list of `(name, block_type)` tuples to use as child blocks:

```python
from wagtail.contrib.typed_table_block.blocks import TypedTableBlock
from wagtail import blocks
from wagtail.images.blocks import ImageChooserBlock

class DemoStreamBlock(blocks.StreamBlock):
    title = blocks.CharBlock()
    paragraph = blocks.RichTextBlock()
    table = TypedTableBlock([
        ('text', blocks.CharBlock()),
        ('numeric', blocks.FloatBlock()),
        ('rich_text', blocks.RichTextBlock()),
        ('image', ImageChooserBlock())
    ])
```

To keep the UI as simple as possible for authors, it's generally recommended to use Wagtail's basic built-in block types as column types, as above. However, all custom block types and parameters are supported. For example, to define a 'country' column type consisting of a dropdown of country choices:

```python
    table = TypedTableBlock([
        ('text', blocks.CharBlock()),
        ('numeric', blocks.FloatBlock()),
        ('rich_text', blocks.RichTextBlock()),
        ('image', ImageChooserBlock()),
        ('country', ChoiceBlock(choices=[
            ('be', 'Belgium'),
            ('fr', 'France'),
            ('de', 'Germany'),
            ('nl', 'Netherlands'),
            ('pl', 'Poland'),
            ('uk', 'United Kingdom'),
        ])),
    ])
```

On your page template, the `{% include_block %}` tag (called on either the individual block, or the StreamField value as a whole) will render any typed table blocks as an HTML `<table>` element.

```html+django
{% load wagtailcore_tags %}

{% include_block page.body %}
```

Or:

```html+django
{% load wagtailcore_tags %}

{% for block in page.body %}
    {% if block.block_type == 'table' %}
        {% include_block block %}
    {% else %}
        {# rendering for other block types #}
    {% endif %}
{% endfor %}
```
