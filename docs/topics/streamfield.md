(streamfield_topic)=

# How to use StreamField for mixed content

StreamField provides a content editing model suitable for pages that do not follow a fixed structure -- such as blog posts or news stories -- where the text may be interspersed with subheadings, images, pull quotes and video. It's also suitable for more specialised content types, such as maps and charts (or, for a programming blog, code snippets). In this model, these different content types are represented as a sequence of 'blocks', which can be repeated and arranged in any order.

For further background on StreamField, and why you would use it instead of a rich text field for the article body, see the blog post [Rich text fields and faster horses](https://torchbox.com/blog/rich-text-fields-and-faster-horses/).

StreamField also offers a rich API to define your own block types, ranging from simple collections of sub-blocks (such as a 'person' block consisting of first name, surname and photograph) to completely custom components with their own editing interface. Within the database, the StreamField content is stored as JSON, ensuring that the full informational content of the field is preserved, rather than just an HTML representation of it.

## Using StreamField

`StreamField` is a model field that can be defined within your page model like any other field:

```python
from django.db import models

from wagtail.models import Page
from wagtail.fields import StreamField
from wagtail import blocks
from wagtail.admin.panels import FieldPanel
from wagtail.images.blocks import ImageChooserBlock

class BlogPage(Page):
    author = models.CharField(max_length=255)
    date = models.DateField("Post date")
    body = StreamField([
        ('heading', blocks.CharBlock(form_classname="full title")),
        ('paragraph', blocks.RichTextBlock()),
        ('image', ImageChooserBlock()),
    ], use_json_field=True)

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

```{versionchanged} 3.0
The `use_json_field=True` argument was added. This indicates that the database's native JSONField support should be used for this field, and is a temporary measure to assist in migrating StreamFields created on earlier Wagtail versions; it will become the default in a future release.
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
        ('photo', ImageChooserBlock(required=False)),
        ('biography', blocks.RichTextBlock()),
    ])),
    ('heading', blocks.CharBlock(form_classname="full title")),
    ('paragraph', blocks.RichTextBlock()),
    ('image', ImageChooserBlock()),
], use_json_field=True)
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
    photo = ImageChooserBlock(required=False)
    biography = blocks.RichTextBlock()
```

`PersonBlock` can then be used in a `StreamField` definition in the same way as the built-in block types:

```python
body = StreamField([
    ('person', PersonBlock()),
    ('heading', blocks.CharBlock(form_classname="full title")),
    ('paragraph', blocks.RichTextBlock()),
    ('image', ImageChooserBlock()),
], use_json_field=True)
```

### Block icons

In the menu that content authors use to add new blocks to a StreamField, each block type has an associated icon. For StructBlock and other structural block types, a placeholder icon is used, since the purpose of these blocks is specific to your project. To set a custom icon, pass the option `icon` as either a keyword argument to `StructBlock`, or an attribute on a `Meta` class:

```{code-block} python
:emphasize-lines: 7

body = StreamField([
    ('person', blocks.StructBlock([
        ('first_name', blocks.CharBlock()),
        ('surname', blocks.CharBlock()),
        ('photo', ImageChooserBlock(required=False)),
        ('biography', blocks.RichTextBlock()),
    ], icon='user')),
    ('heading', blocks.CharBlock(form_classname="full title")),
    ('paragraph', blocks.RichTextBlock()),
    ('image', ImageChooserBlock()),
], use_json_field=True)
```

```{code-block} python
:emphasize-lines: 7-8

class PersonBlock(blocks.StructBlock):
    first_name = blocks.CharBlock()
    surname = blocks.CharBlock()
    photo = ImageChooserBlock(required=False)
    biography = blocks.RichTextBlock()

    class Meta:
        icon = 'user'
```

For a list of the recognised icon identifiers, see the [](styleguide).

### ListBlock

`ListBlock` defines a repeating block, allowing content authors to insert as many instances of a particular block type as they like. For example, a 'gallery' block consisting of multiple images can be defined as follows:

```{code-block} python
:emphasize-lines: 2

body = StreamField([
    ('gallery', blocks.ListBlock(ImageChooserBlock())),
    ('heading', blocks.CharBlock(form_classname="full title")),
    ('paragraph', blocks.RichTextBlock()),
    ('image', ImageChooserBlock()),
], use_json_field=True)
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
        ('image', ImageChooserBlock()),
        ('video', EmbedBlock()),
    ])),
    ('heading', blocks.CharBlock(form_classname="full title")),
    ('paragraph', blocks.RichTextBlock()),
    ('image', ImageChooserBlock()),
], use_json_field=True)
```

`StreamBlock` can also be subclassed in the same way as `StructBlock`, with the child blocks being specified as attributes on the class:

```python
class CarouselBlock(blocks.StreamBlock):
    image = ImageChooserBlock()
    video = EmbedBlock()

    class Meta:
        icon = 'image'
```

A StreamBlock subclass defined in this way can also be passed to a `StreamField` definition, instead of passing a list of block types. This allows setting up a common set of block types to be used on multiple page types:

```python
class CommonContentBlock(blocks.StreamBlock):
    heading = blocks.CharBlock(form_classname="full title")
    paragraph = blocks.RichTextBlock()
    image = ImageChooserBlock()


class BlogPage(Page):
    body = StreamField(CommonContentBlock(), use_json_field=True)
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

By default, a StreamField can contain an unlimited number of blocks. The `min_num` and `max_num` options on `StreamField` or `StreamBlock` allow you to set a minimum or maximum number of blocks:

```python
body = StreamField([
    ('heading', blocks.CharBlock(form_classname="full title")),
    ('paragraph', blocks.RichTextBlock()),
    ('image', ImageChooserBlock()),
], min_num=2, max_num=5, use_json_field=True)
```

Or equivalently:

```python
class CommonContentBlock(blocks.StreamBlock):
    heading = blocks.CharBlock(form_classname="full title")
    paragraph = blocks.RichTextBlock()
    image = ImageChooserBlock()

    class Meta:
        min_num = 2
        max_num = 5
```

The `block_counts` option can be used to set a minimum or maximum count for specific block types. This accepts a dict, mapping block names to a dict containing either or both of `min_num` and `max_num`. For example, to permit between 1 and 3 'heading' blocks:

```python
body = StreamField([
    ('heading', blocks.CharBlock(form_classname="full title")),
    ('paragraph', blocks.RichTextBlock()),
    ('image', ImageChooserBlock()),
], block_counts={
    'heading': {'min_num': 1, 'max_num': 3},
}, use_json_field=True)
```

Or equivalently:

```python
class CommonContentBlock(blocks.StreamBlock):
    heading = blocks.CharBlock(form_classname="full title")
    paragraph = blocks.RichTextBlock()
    image = ImageChooserBlock()

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
        ('photo', ImageChooserBlock(required=False)),
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
    photo = ImageChooserBlock(required=False)
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

Since `first_name`, `surname`, `photo` and `biography` are defined as blocks in their own right, this could also be written as:

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

All block types, not just `StructBlock`, support the `template` property. However, for blocks that handle basic Python data types, such as `CharBlock` and `IntegerBlock`, there are some limitations on where the template will take effect. For further details, see [](boundblocks_and_values).

## Customisations

All block types implement a common API for rendering their front-end and form representations, and storing and retrieving values to and from the database. By subclassing the various block classes and overriding these methods, all kinds of customisations are possible, from modifying the layout of StructBlock form fields to implementing completely new ways of combining blocks. For further details, see [](custom_streamfield_blocks).

(modifying_streamfield_data)=

## Modifying StreamField data

A StreamField's value behaves as a list, and blocks can be inserted, overwritten and deleted before saving the instance back to the database. A new item can be written to the list as a tuple of _(block_type, value)_ - when read back, it will be returned as a `BoundBlock` object.

```python
# Replace the first block with a new block of type 'heading'
my_page.body[0] = ('heading', "My story")

# Delete the last block
del my_page.body[-1]

# Append a rich text block to the stream
from wagtail.rich_text import RichText
my_page.body.append(('paragraph', RichText("<p>And they all lived happily ever after.</p>")))

# Save the updated data back to the database
my_page.save()
```

(streamfield_migrating_richtext)=

## Migrating RichTextFields to StreamField

If you change an existing RichTextField to a StreamField, the database migration will complete with no errors, since both fields use a text column within the database. However, StreamField uses a JSON representation for its data, so the existing text requires an extra conversion step in order to become accessible again. For this to work, the StreamField needs to include a RichTextBlock as one of the available block types. Create the migration as normal using `./manage.py makemigrations`, then edit it as follows (in this example, the 'body' field of the `demo.BlogPage` model is being converted to a StreamField with a RichTextBlock named `rich_text`):

```{note}
This migration cannot be used if the StreamField has the `use_json_field` argument set to `True`. To migrate, set the `use_json_field` argument to `False` first, migrate the data, then set it back to `True`.
```

```python
# -*- coding: utf-8 -*-
from django.db import models, migrations
from wagtail.rich_text import RichText


def convert_to_streamfield(apps, schema_editor):
    BlogPage = apps.get_model("demo", "BlogPage")
    for page in BlogPage.objects.all():
        if page.body.raw_text and not page.body:
            page.body = [('rich_text', RichText(page.body.raw_text))]
            page.save()


def convert_to_richtext(apps, schema_editor):
    BlogPage = apps.get_model("demo", "BlogPage")
    for page in BlogPage.objects.all():
        if page.body.raw_text is None:
            raw_text = ''.join([
                child.value.source for child in page.body
                if child.block_type == 'rich_text'
            ])
            page.body = raw_text
            page.save()


class Migration(migrations.Migration):

    dependencies = [
        # leave the dependency line from the generated migration intact!
        ('demo', '0001_initial'),
    ]

    operations = [
        # leave the generated AlterField intact!
        migrations.AlterField(
            model_name='BlogPage',
            name='body',
            field=wagtail.fields.StreamField([('rich_text', wagtail.blocks.RichTextBlock())]),
        ),

        migrations.RunPython(
            convert_to_streamfield,
            convert_to_richtext,
        ),
    ]
```

Note that the above migration will work on published Page objects only. If you also need to migrate draft pages and page revisions, then edit the migration as in the following example instead:

```python
# -*- coding: utf-8 -*-
import json

from django.core.serializers.json import DjangoJSONEncoder
from django.db import migrations, models

from wagtail.rich_text import RichText


def page_to_streamfield(page):
    changed = False
    if page.body.raw_text and not page.body:
        page.body = [('rich_text', {'rich_text': RichText(page.body.raw_text)})]
        changed = True
    return page, changed


def pagerevision_to_streamfield(revision_data):
    changed = False
    body = revision_data.get('body')
    if body:
        try:
            json.loads(body)
        except ValueError:
            revision_data['body'] = json.dumps(
                [{
                    "value": {"rich_text": body},
                    "type": "rich_text"
                }],
                cls=DjangoJSONEncoder)
            changed = True
        else:
            # It's already valid JSON. Leave it.
            pass
    return revision_data, changed


def page_to_richtext(page):
    changed = False
    if page.body.raw_text is None:
        raw_text = ''.join([
            child.value['rich_text'].source for child in page.body
            if child.block_type == 'rich_text'
        ])
        page.body = raw_text
        changed = True
    return page, changed


def pagerevision_to_richtext(revision_data):
    changed = False
    body = revision_data.get('body', 'definitely non-JSON string')
    if body:
        try:
            body_data = json.loads(body)
        except ValueError:
            # It's not apparently a StreamField. Leave it.
            pass
        else:
            raw_text = ''.join([
                child['value']['rich_text'] for child in body_data
                if child['type'] == 'rich_text'
            ])
            revision_data['body'] = raw_text
            changed = True
    return revision_data, changed


def convert(apps, schema_editor, page_converter, pagerevision_converter):
    BlogPage = apps.get_model("demo", "BlogPage")
    for page in BlogPage.objects.all():

        page, changed = page_converter(page)
        if changed:
            page.save()

        for revision in page.revisions.all():
            revision_data = revision.content
            revision_data, changed = pagerevision_converter(revision_data)
            if changed:
                revision.content = revision_data
                revision.save()


def convert_to_streamfield(apps, schema_editor):
    return convert(apps, schema_editor, page_to_streamfield, pagerevision_to_streamfield)


def convert_to_richtext(apps, schema_editor):
    return convert(apps, schema_editor, page_to_richtext, pagerevision_to_richtext)


class Migration(migrations.Migration):

    dependencies = [
        # leave the dependency line from the generated migration intact!
        ('demo', '0001_initial'),
    ]

    operations = [
        # leave the generated AlterField intact!
        migrations.AlterField(
            model_name='BlogPage',
            name='body',
            field=wagtail.fields.StreamField([('rich_text', wagtail.blocks.RichTextBlock())]),
        ),

        migrations.RunPython(
            convert_to_streamfield,
            convert_to_richtext,
        ),
    ]
```
