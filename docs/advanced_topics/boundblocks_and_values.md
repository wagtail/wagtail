(boundblocks_and_values)=

# About StreamField BoundBlocks and values

All StreamField block types accept a `template` parameter to determine how they will be rendered on a page. However, for blocks that handle basic Python data types, such as `CharBlock` and `IntegerBlock`, there are some limitations on where the template will take effect, since those built-in types (`str`, `int` and so on) cannot be 'taught' about their template rendering. As an example of this, consider the following block definition:

```python
class HeadingBlock(blocks.CharBlock):
    class Meta:
        template = 'blocks/heading.html'
```

where `blocks/heading.html` consists of:

```html+django
<h1>{{ value }}</h1>
```

This gives us a block that behaves as an ordinary text field, but wraps its output in `<h1>` tags whenever it is rendered:

```python
class BlogPage(Page):
    body = StreamField([
        # ...
        ('heading', HeadingBlock()),
        # ...
    ], use_json_field=True)
```

```html+django
{% load wagtailcore_tags %}

{% for block in page.body %}
    {% if block.block_type == 'heading' %}
        {% include_block block %}  {# This block will output its own <h1>...</h1> tags. #}
    {% endif %}
{% endfor %}
```

This kind of arrangement - a value that supposedly represents a plain text string, but has its own custom HTML representation when output on a template - would normally be a very messy thing to achieve in Python, but it works here because the items you get when iterating over a StreamField are not actually the 'native' values of the blocks. Instead, each item is returned as an instance of `BoundBlock` - an object that represents the pairing of a value and its block definition. By keeping track of the block definition, a `BoundBlock` always knows which template to render. To get to the underlying value - in this case, the text content of the heading - you would need to access `block.value`. Indeed, if you were to output `{% include_block block.value %}` on the page, you would find that it renders as plain text, without the `<h1>` tags.

(More precisely, the items returned when iterating over a StreamField are instances of a class `StreamChild`, which provides the `block_type` property as well as `value`.)

Experienced Django developers may find it helpful to compare this to the `BoundField` class in Django's forms framework, which represents the pairing of a form field value with its corresponding form field definition, and therefore knows how to render the value as an HTML form field.

Most of the time, you won't need to worry about these internal details; Wagtail will use the template rendering wherever you would expect it to. However, there are certain cases where the illusion isn't quite complete - namely, when accessing children of a `ListBlock` or `StructBlock`. In these cases, there is no `BoundBlock` wrapper, and so the item cannot be relied upon to know its own template rendering. For example, consider the following setup, where our `HeadingBlock` is a child of a StructBlock:

```python
class EventBlock(blocks.StructBlock):
    heading = HeadingBlock()
    description = blocks.TextBlock()
    # ...

    class Meta:
        template = 'blocks/event.html'
```

In `blocks/event.html`:

```html+django
{% load wagtailcore_tags %}

<div class="event {% if value.heading == 'Party!' %}lots-of-balloons{% endif %}">
    {% include_block value.heading %}
    - {% include_block value.description %}
</div>
```

In this case, `value.heading` returns the plain string value rather than a `BoundBlock`; this is necessary because otherwise the comparison in `{% if value.heading == 'Party!' %}` would never succeed. This in turn means that `{% include_block value.heading %}` renders as the plain string, without the `<h1>` tags. To get the HTML rendering, you need to explicitly access the `BoundBlock` instance through `value.bound_blocks.heading`:

```html+django
{% load wagtailcore_tags %}

<div class="event {% if value.heading == 'Party!' %}lots-of-balloons{% endif %}">
    {% include_block value.bound_blocks.heading %}
    - {% include_block value.description %}
</div>
```

In practice, it would probably be more natural and readable to make the `<h1>` tag explicit in the EventBlock's template:

```html+django
{% load wagtailcore_tags %}

<div class="event {% if value.heading == 'Party!' %}lots-of-balloons{% endif %}">
    <h1>{{ value.heading }}</h1>
    - {% include_block value.description %}
</div>
```

This limitation does not apply to StructBlock and StreamBlock values as children of a StructBlock, because Wagtail implements these as complex objects that know their own template rendering, even when not wrapped in a `BoundBlock`. For example, if a StructBlock is nested in another StructBlock, as in:

```python
class EventBlock(blocks.StructBlock):
    heading = HeadingBlock()
    description = blocks.TextBlock()
    guest_speaker = blocks.StructBlock([
        ('first_name', blocks.CharBlock()),
        ('surname', blocks.CharBlock()),
        ('photo', ImageChooserBlock()),
    ], template='blocks/speaker.html')
```

then `{% include_block value.guest_speaker %}` within the EventBlock's template will pick up the template rendering from `blocks/speaker.html` as intended.

In summary, interactions between BoundBlocks and plain values work according to the following rules:

1. When iterating over the value of a StreamField or StreamBlock (as in `{% for block in page.body %}`), you will get back a sequence of BoundBlocks.
2. If you have a BoundBlock instance, you can access the plain value as `block.value`.
3. Accessing a child of a StructBlock (as in `value.heading`) will return a plain value; to retrieve the BoundBlock instead, use `value.bound_blocks.heading`.
4. Likewise, accessing children of a ListBlock (e.g. `for item in value`) will return plain values; to retrieve BoundBlocks instead, use `value.bound_blocks`.
5. StructBlock and StreamBlock values always know how to render their own templates, even if you only have the plain value rather than the BoundBlock.

```{versionchanged} 2.16
The value of a ListBlock now provides a `bound_blocks` property; previously it was a plain Python list of child values.
```
