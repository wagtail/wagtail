(streamfield_topic)=

# How to use StreamField for mixed content

StreamField provides a content editing model suitable for pages that do not follow a fixed structure -- such as blog posts or news stories -- where the text may be interspersed with subheadings, images, pull quotes and video. It's also suitable for more specialized content types, such as maps and charts (or, for a programming blog, code snippets). In this model, these different content types are represented as a sequence of 'blocks', which can be repeated and arranged in any order.

For further background on StreamField, and why you would use it instead of a rich text field for the article body, see the blog post [Rich text fields and faster horses](https://torchbox.com/blog/rich-text-fields-and-faster-horses/).

StreamField also offers a rich API to define your own block types, ranging from simple collections of sub-blocks (such as a 'person' block consisting of first name, surname, and photograph) to completely custom components with their own editing interface. Within the database, the StreamField content is stored as JSON, ensuring that the full informational content of the field is preserved, rather than just an HTML representation of it.

## Using StreamField

`StreamField` is a model field that can be defined within your page model like any other field:

```python
from django.db import models

from wagtail.models import Page
from wagtail.fields import StreamField
from wagtail import blocks
from wagtail.admin.panels import FieldPanel
from wagtail.images.blocks import ImageBlock

class BlogPage(Page):
    author = models.CharField(max_length=255)
    date = models.DateField("Post date")
    body = StreamField([
        ('heading', blocks.CharBlock(form_classname="title")),
        ('paragraph', blocks.RichTextBlock()),
        ('image', ImageBlock()),
    ])

    content_panels = Page.content_panels + [
        FieldPanel('author'),
        FieldPanel('date'),
        FieldPanel('body'),
    ]
```

In this example, the body field of `BlogPage` is defined as a `StreamField` where authors can compose content from three different block types: headings, paragraphs, and images, which can be used and repeated in any order. The block types available to authors are defined as a list of `(name, block_type)` tuples: 'name' is used to identify the block type within templates, and should follow the standard Python conventions for variable names: lower-case and underscores, no spaces.

You can find the complete list of available block types in the [](streamfield_block_reference).

```{note}
   StreamField is not a direct replacement for other field types such as RichTextField. If you need to migrate an existing field to StreamField, refer to [](streamfield_migrating_richtext).
```

```{note}
   While block definitions look similar to model fields, they are not the same thing. Blocks are only valid within a StreamField - using them in place of a model field will not work.
```

(streamfield_template_rendering)=

## Template rendering

StreamField provides an HTML representation for the stream content as a whole, as well as for each individual block. To include this HTML into your page, use the `{% include_block %}` tag:

```html+django
{% load wagtailcore_tags %}

    ...

{% include_block page.body %}
```

In the default rendering, each block of the stream is wrapped in a `<div class="block-my_block_name">` element (where `my_block_name` is the block name given in the StreamField definition). If you wish to provide your own HTML markup, you can instead iterate over the field's value, and invoke `{% include_block %}` on each block in turn:

```html+django
{% load wagtailcore_tags %}

    ...

<article>
    {% for block in page.body %}
        <section>{% include_block block %}</section>
    {% endfor %}
</article>
```

For more control over the rendering of specific block types, each block object provides `block_type` and `value` properties:

```html+django
{% load wagtailcore_tags %}

    ...

<article>
    {% for block in page.body %}
        {% if block.block_type == 'heading' %}
            <h1>{{ block.value }}</h1>
        {% else %}
            <section class="block-{{ block.block_type }}">
                {% include_block block %}
            </section>
        {% endif %}
    {% endfor %}
</article>
```

## Combining blocks

In addition to using the built-in block types directly within StreamField, it's possible to construct new block types by combining sub-blocks in various ways. Examples of this could include:

-   An "image with caption" block consisting of an image chooser and a text field
-   A "related links" section, where an author can provide any number of links to other pages
-   A slideshow block, where each slide may be an image, text or video, arranged in any order

Once a new block type has been built up in this way, you can use it anywhere where a built-in block type would be used - including using it as a component for yet another block type. For example, you could define an image gallery block where each item is an "image with caption" block.

### StructBlock

`StructBlock` allows you to group several 'child' blocks together to be presented as a single block. The child blocks are passed to `StructBlock` as a list of `(name, block_type)` tuples:

```{code-block} python
:emphasize-lines: 2-7

body = StreamField([
    ('person', blocks.StructBlock([
        ('first_name', blocks.CharBlock()),
        ('surname', blocks.CharBlock()),
        ('photo', ImageBlock(required=False)),
        ('biography', blocks.RichTextBlock()),
    ])),
    ('heading', blocks.CharBlock(form_classname="title")),
    ('paragraph', blocks.RichTextBlock()),
    ('image', ImageBlock()),
])
```

When reading back the content of a StreamField (such as when rendering a template), the value of a StructBlock is a dict-like object with keys corresponding to the block names given in the definition:

```html+django
<article>
    {% for block in page.body %}
        {% if block.block_type == 'person' %}
            <div class="person">
                {% image block.value.photo width-400 %}
                <h2>{{ block.value.first_name }} {{ block.value.surname }}</h2>
                {{ block.value.biography }}
            </div>
        {% else %}
            (rendering for other block types)
        {% endif %}
    {% endfor %}
</article>
```

### Subclassing `StructBlock`

Placing a StructBlock's list of child blocks inside a `StreamField` definition can often be hard to read, and makes it difficult for the same block to be reused in multiple places. As an alternative, `StructBlock` can be subclassed, with the child blocks defined as attributes on the subclass. The 'person' block in the above example could be rewritten as:

```python
class PersonBlock(blocks.StructBlock):
    first_name = blocks.CharBlock()
    surname = blocks.CharBlock()
    photo = ImageBlock(required=False)
    biography = blocks.RichTextBlock()
```

`PersonBlock` can then be used in a `StreamField` definition in the same way as the built-in block types:

```python
body = StreamField([
    ('person', PersonBlock()),
    ('heading', blocks.CharBlock(form_classname="title")),
    ('paragraph', blocks.RichTextBlock()),
    ('image', ImageBlock()),
])
```

(block_icons)=

### Block icons

In the menu that content authors use to add new blocks to a StreamField, each block type has an associated icon. For StructBlock and other structural block types, a placeholder icon is used, since the purpose of these blocks is specific to your project. To set a custom icon, pass the option `icon` as either a keyword argument to `StructBlock`, or an attribute on a `Meta` class:

```{code-block} python
:emphasize-lines: 7

body = StreamField([
    ('person', blocks.StructBlock([
        ('first_name', blocks.CharBlock()),
        ('surname', blocks.CharBlock()),
        ('photo', ImageBlock(required=False)),
        ('biography', blocks.RichTextBlock()),
    ], icon='user')),
    ('heading', blocks.CharBlock(form_classname="title")),
    ('paragraph', blocks.RichTextBlock()),
    ('image', ImageBlock()),
])
```

```{code-block} python
:emphasize-lines: 7-8

class PersonBlock(blocks.StructBlock):
    first_name = blocks.CharBlock()
    surname = blocks.CharBlock()
    photo = ImageBlock(required=False)
    biography = blocks.RichTextBlock()

    class Meta:
        icon = 'user'
```

For a list of icons available out of the box, see our [icons overview](icons). Project-specific icons are also displayed in the [styleguide](styleguide).

### ListBlock

`ListBlock` defines a repeating block, allowing content authors to insert as many instances of a particular block type as they like. For example, a 'gallery' block consisting of multiple images can be defined as follows:

```{code-block} python
:emphasize-lines: 2

body = StreamField([
    ('gallery', blocks.ListBlock(ImageBlock())),
    ('heading', blocks.CharBlock(form_classname="title")),
    ('paragraph', blocks.RichTextBlock()),
    ('image', ImageBlock()),
])
```

When reading back the content of a StreamField (such as when rendering a template), the value of a ListBlock is a list of child values:

```html+django
<article>
    {% for block in page.body %}
        {% if block.block_type == 'gallery' %}
            <ul class="gallery">
                {% for img in block.value %}
                    <li>{% image img width-400 %}</li>
                {% endfor %}
            </ul>
        {% else %}
            (rendering for other block types)
        {% endif %}
    {% endfor %}
</article>
```

### StreamBlock

`StreamBlock` defines a set of child block types that can be mixed and repeated in any sequence, via the same mechanism as StreamField itself. For example, a carousel that supports both image and video slides could be defined as follows:

```{code-block} python
:emphasize-lines: 2-5

body = StreamField([
    ('carousel', blocks.StreamBlock([
        ('image', ImageBlock()),
        ('video', EmbedBlock()),
    ])),
    ('heading', blocks.CharBlock(form_classname="title")),
    ('paragraph', blocks.RichTextBlock()),
    ('image', ImageBlock()),
])
```

`StreamBlock` can also be subclassed in the same way as `StructBlock`, with the child blocks being specified as attributes on the class:

```python
class CarouselBlock(blocks.StreamBlock):
    image = ImageBlock()
    video = EmbedBlock()

    class Meta:
        icon = 'image'
```

A StreamBlock subclass defined in this way can also be passed to a `StreamField` definition, instead of passing a list of block types. This allows setting up a common set of block types to be used on multiple page types:

```python
class CommonContentBlock(blocks.StreamBlock):
    heading = blocks.CharBlock(form_classname="title")
    paragraph = blocks.RichTextBlock()
    image = ImageBlock()


class BlogPage(Page):
    body = StreamField(CommonContentBlock())
```

When reading back the content of a StreamField, the value of a StreamBlock is a sequence of block objects with `block_type` and `value` properties, just like the top-level value of the StreamField itself.

```html+django
<article>
    {% for block in page.body %}
        {% if block.block_type == 'carousel' %}
            <ul class="carousel">
                {% for slide in block.value %}
                    {% if slide.block_type == 'image' %}
                        <li class="image">{% image slide.value width-200 %}</li>
                    {% else %}
                        <li class="video">{% include_block slide %}</li>
                    {% endif %}
                {% endfor %}
            </ul>
        {% else %}
            (rendering for other block types)
        {% endif %}
    {% endfor %}
</article>
```

### Limiting block counts

By default, a StreamField can contain an unlimited number of blocks. The `min_num` and `max_num` options on `StreamField` or `StreamBlock` allow you to set a minimum or a maximum number of blocks:

```python
body = StreamField([
    ('heading', blocks.CharBlock(form_classname="title")),
    ('paragraph', blocks.RichTextBlock()),
    ('image', ImageBlock()),
], min_num=2, max_num=5)
```

Or equivalently:

```python
class CommonContentBlock(blocks.StreamBlock):
    heading = blocks.CharBlock(form_classname="title")
    paragraph = blocks.RichTextBlock()
    image = ImageBlock()

    class Meta:
        min_num = 2
        max_num = 5
```

The `block_counts` option can be used to set a minimum or maximum count for specific block types. This accepts a dict, mapping block names to a dict containing either or both `min_num` and `max_num`. For example, to permit between 1 and 3 'heading' blocks:

```python
body = StreamField([
    ('heading', blocks.CharBlock(form_classname="title")),
    ('paragraph', blocks.RichTextBlock()),
    ('image', ImageBlock()),
], block_counts={
    'heading': {'min_num': 1, 'max_num': 3},
})
```

Or equivalently:

```python
class CommonContentBlock(blocks.StreamBlock):
    heading = blocks.CharBlock(form_classname="title")
    paragraph = blocks.RichTextBlock()
    image = ImageBlock()

    class Meta:
        block_counts = {
            'heading': {'min_num': 1, 'max_num': 3},
        }
```

(streamfield_per_block_templates)=

## Per-block templates

By default, each block is rendered using simple, minimal HTML markup, or no markup at all. For example, a CharBlock value is rendered as plain text, while a ListBlock outputs its child blocks in a `<ul>` wrapper. To override this with your own custom HTML rendering, you can pass a `template` argument to the block, giving the filename of a template file to be rendered. This is particularly useful for custom block types derived from StructBlock:

```python
('person', blocks.StructBlock(
    [
        ('first_name', blocks.CharBlock()),
        ('surname', blocks.CharBlock()),
        ('photo', ImageBlock(required=False)),
        ('biography', blocks.RichTextBlock()),
    ],
    template='myapp/blocks/person.html',
    icon='user'
))
```

Or, when defined as a subclass of StructBlock:

```python
class PersonBlock(blocks.StructBlock):
    first_name = blocks.CharBlock()
    surname = blocks.CharBlock()
    photo = ImageBlock(required=False)
    biography = blocks.RichTextBlock()

    class Meta:
        template = 'myapp/blocks/person.html'
        icon = 'user'
```

Within the template, the block value is accessible as the variable `value`:

```html+django
{% load wagtailimages_tags %}

<div class="person">
    {% image value.photo width-400 %}
    <h2>{{ value.first_name }} {{ value.surname }}</h2>
    {{ value.biography }}
</div>
```

Since `first_name`, `surname`, `photo`, and `biography` are defined as blocks in their own right, this could also be written as:

```html+django
{% load wagtailcore_tags wagtailimages_tags %}

<div class="person">
    {% image value.photo width-400 %}
    <h2>{% include_block value.first_name %} {% include_block value.surname %}</h2>
    {% include_block value.biography %}
</div>
```

Writing `{{ my_block }}` is roughly equivalent to `{% include_block my_block %}`, but the short form is more restrictive, as it does not pass variables from the calling template such as `request` or `page`; for this reason, it is recommended that you only use it for simple values that do not render HTML of their own. For example, if our PersonBlock used the template:

```html+django
{% load wagtailimages_tags %}

<div class="person">
    {% image value.photo width-400 %}
    <h2>{{ value.first_name }} {{ value.surname }}</h2>

    {% if request.user.is_authenticated %}
        <a href="#">Contact this person</a>
    {% endif %}

    {{ value.biography }}
</div>
```

then the `request.user.is_authenticated` test would not work correctly when rendering the block through a `{{ ... }}` tag:

```html+django
{# Incorrect: #}

{% for block in page.body %}
    {% if block.block_type == 'person' %}
        <div>
            {{ block }}
        </div>
    {% endif %}
{% endfor %}

{# Correct: #}

{% for block in page.body %}
    {% if block.block_type == 'person' %}
        <div>
            {% include_block block %}
        </div>
    {% endif %}
{% endfor %}
```

Like Django's `{% include %}` tag, `{% include_block %}` also allows passing additional variables to the included template, through the syntax `{% include_block my_block with foo="bar" %}`:

```html+django

{# In page template: #}

{% for block in page.body %}
    {% if block.block_type == 'person' %}
        {% include_block block with classname="important" %}
    {% endif %}
{% endfor %}

{# In PersonBlock template: #}

<div class="{{ classname }}">
    ...
</div>
```

The syntax `{% include_block my_block with foo="bar" only %}` is also supported, to specify that no variables from the parent template other than `foo` will be passed to the child template.

(streamfield_get_context)=

As well as passing variables from the parent template, block subclasses can pass additional template variables of their own by overriding the `get_context` method:

```python
import datetime

class EventBlock(blocks.StructBlock):
    title = blocks.CharBlock()
    date = blocks.DateBlock()

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context=parent_context)
        context['is_happening_today'] = (value['date'] == datetime.date.today())
        return context

    class Meta:
        template = 'myapp/blocks/event.html'
```

In this example, the variable `is_happening_today` will be made available within the block template. The `parent_context` keyword argument is available when the block is rendered through an `{% include_block %}` tag, and is a dict of variables passed from the calling template.

(streamfield_get_template)=

Similarly, a `get_template` method can be defined to dynamically select a template based on the block value:

```python
import datetime

class EventBlock(blocks.StructBlock):
    title = blocks.CharBlock()
    date = blocks.DateBlock()

    def get_template(self, value, context=None):
        if value["date"] > datetime.date.today():
            return "myapp/blocks/future_event.html"
        else:
            return "myapp/blocks/event.html"
```

All block types, not just `StructBlock`, support the `template` property. However, for blocks that handle basic Python data types, such as `CharBlock` and `IntegerBlock`, there are some limitations on where the template will take effect. For further details, see [](boundblocks_and_values).

(configuring_block_previews)=

## Configuring block previews

StreamField blocks can have previews that will be shown inside the block picker when you add a block in the editor. To enable this feature, you must configure the preview value and template. You can also add a description to help users pick the right block for their content.

You can do so by [passing the keyword arguments](block_preview_arguments) `preview_value`, `preview_template`, and `description` when instantiating a block:

```{code-block} python
:emphasize-lines: 6-8

("quote", blocks.StructBlock(
    [
        ("text", blocks.TextBlock()),
        ("source", blocks.CharBlock()),
    ],
    preview_value={"text": "This is the coolest CMS ever.", "source": "Willie Wagtail"},
    preview_template="myapp/previews/blocks/quote.html",
    description="A quote with attribution to the source, rendered as a blockquote.",
))
```

You can also set `preview_value`, `preview_template`, and `description` as attributes in the `Meta` class of the block. For example:

```{code-block} python
:emphasize-lines: 6-8

class QuoteBlock(blocks.StructBlock):
    text = blocks.TextBlock()
    source = blocks.CharBlock()

    class Meta:
        preview_value = {"text": "This is the coolest CMS ever.", "source": "Willie Wagtail"}
        preview_template = "myapp/previews/blocks/quote.html"
        description = "A quote with attribution to the source, rendered as a blockquote."
```

For more details on the preview options, see the corresponding {meth}`~wagtail.blocks.Block.get_preview_value`, {meth}`~wagtail.blocks.Block.get_preview_template`, and {meth}`~wagtail.blocks.Block.get_description` methods, as well as the {meth}`~wagtail.blocks.Block.get_preview_context` method.

In particular, the `get_preview_value()` method can be overridden to provide a dynamic preview value, such as from the database:

```python
from myapp.models import Quote


class QuoteBlock(blocks.StructBlock):
    ...

    def get_preview_value(self, value):
        quote = Quote.objects.first()
        return {"text": quote.text, "source": quote.source}
```

(streamfield_global_preview_template)=

### Overriding the global preview template

In many cases, you likely want to use the block's real template that you already configure via `template` or `get_template` as described in [](streamfield_per_block_templates). However, such templates are only an HTML fragment for the block, whereas the preview requires a complete HTML document as the template.

To avoid having to specify `preview_template` for each block, Wagtail provides a default preview template for all blocks. This template makes use of the `{% include_block %}` tag (as described in [](streamfield_template_rendering)), which will reuse your block's specific template.

Note that the default preview template does not include any static assets that may be necessary to render your blocks properly. If you only need to add static assets to the default preview template, you can skip specifying `preview_template` for each block and instead override the default template globally. You can do so by creating a `wagtailcore/shared/block_preview.html` template inside one of your `templates` directories (with a higher precedence than the `wagtail` app) with the following content:

```html+django
{% extends "wagtailcore/shared/block_preview.html" %}
{% load static %}

{% block css %}
    {{ block.super }}
    <link rel="stylesheet" href="{% static 'css/my-styles.css' %}">
{% endblock %}

{% block js %}
    {{ block.super }}
    <script src="{% static 'js/my-script.js' %}"></script>
{% endblock %}
```

For more details on overriding templates, see Django's guide on [](inv:django#howto/overriding-templates).

The global `wagtailcore/shared/block_preview.html` override will be used for all blocks by default. If you want to use a different template for a particular block, you can still specify `preview_template`, which will take precedence.

## Customizations

All block types implement a common API for rendering their front-end and form representations, and storing and retrieving values to and from the database. By subclassing the various block classes and overriding these methods, all kinds of customizations are possible, from modifying the layout of StructBlock form fields to implementing completely new ways of combining blocks. For further details, see [](custom_streamfield_blocks).

(modifying_streamfield_data)=

## Modifying StreamField data

A StreamField's value behaves as a list, and blocks can be inserted, overwritten, and deleted before saving the instance back to the database. A new item can be written to the list as a tuple of _(block_type, value)_ - when read back, it will be returned as a `BoundBlock` object.

```python
# Replace the first block with a new block of type 'heading'
my_page.body[0] = ('heading', "My story")

# Delete the last block
del my_page.body[-1]

# Append a rich text block to the stream
my_page.body.append(('paragraph', "<p>And they all lived happily ever after.</p>"))

# Save the updated data back to the database
my_page.save()
```

If a block extending a StructBlock is to be used inside of the StreamField's value, the value of this block can be provided as a Python dict (similar to what is accepted by the block's `.to_python` method).

```python

from wagtail import blocks

class UrlWithTextBlock(blocks.StructBlock):
   url = blocks.URLBlock()
   text = blocks.TextBlock()

# using this block inside the content

data = {
    'url': 'https://github.com/wagtail/',
    'text': 'A very interesting and useful repo'
}

# append the new block to the stream as a tuple with the defined index for this block type
my_page.body.append(('url', data))
my_page.save()

```

(streamfield_retrieving_blocks_by_name)=

## Retrieving blocks by name

StreamField values provide a `blocks_by_name` method for retrieving all blocks of a given name:

```python
my_page.body.blocks_by_name('heading')  # returns a list of 'heading' blocks
```

Calling `blocks_by_name` with no arguments returns a `dict`-like object, mapping block names to the list of blocks of that name. This is particularly useful in template code, where passing arguments isn't possible:

```html+django
<h2>Table of contents</h2>
<ol>
    {% for heading_block in page.body.blocks_by_name.heading %}
        <li>{{ heading_block.value }}</li>
    {% endfor %}
</ol>
```

The `first_block_by_name` method returns the first block of the given name in the stream, or `None` if no matching block is found:

```
hero_image = my_page.body.first_block_by_name('image')
```

`first_block_by_name` can also be called without arguments to return a `dict`-like mapping:

```html+django
<div class="hero-image">{{ page.body.first_block_by_name.image }}</div>
```

(streamfield_search)=

## Search considerations

Like any other field, content in a StreamField can be made searchable by adding the field to the model's search_fields definition - see {ref}`wagtailsearch_indexing_fields`. By default, all text content from the stream will be added to the search index. If you wish to exclude certain block types from being indexed, pass the keyword argument `search_index=False` as part of the block's definition. For example:

```python
body = StreamField([
    ('normal_text', blocks.RichTextBlock()),
    ('pull_quote', blocks.RichTextBlock(search_index=False)),
    ('footnotes', blocks.ListBlock(blocks.CharBlock(), search_index=False)),
])
```

## Custom validation

Custom validation logic can be added to blocks by overriding the block's `clean` method. For more information, see [](streamfield_validation).

## Migrations

Since StreamField data is stored as a single JSON field, rather than being arranged in a formal database structure, it will often be necessary to write data migrations when changing the data structure of a StreamField or converting to or from other field types. For more information on how StreamField interacts with Django's migration system, and a guide to migrating rich text to StreamFields, see [](streamfield_migrations).
