# Create a portfolio page

A portfolio page is a web page that has your resume or Curriculum Vitae (CV). The page gives potential employers access to your work experience.

This tutorial shows you how to add a portfolio page to your portfolio site using the Wagtail StreamField. 

First, let's explain what StreamField is.

## What is StreamField?

The reason for developing StreamField is to address the tension between structured content and editorial flexibility in content management.

In traditional content management systems, there's often a compromise between structured content and giving editors the freedom to create flexible layouts. Traditional solutions often relied on rich text fields to accommodate the need for more flexible and versatile content. Rich text field helps by allowing editors to use a WYSIWYG editor for formatting. However, rich text fields have limitations. These limitations include the loss of semantic value and issues with browser-based editors.

StreamField gives editors more flexibility and addresses the limitations of rich text fields. StreamField is a versatile content management solution that treats content as a sequence of blocks. Each block represents different content types like paragraphs, images, and maps. Editors can arrange and customize these blocks to create complex and flexible layouts. Also, StreamField can capture the semantic meaning of different content types.

## Create reusable custom blocks

Now that you know what StreamField is, let's guide you through using it to add a portfolio page to your site.

Start by adding a new app to your portfolio site by running the following command:

```sh
python manage.py startapp portfolio
```

Install your new portfolio app to your site by adding _"portfolio"_ to the `INSTALLED_APPS` list in your `mysite/settings/base.py` file.

Now create a `base/blocks.py` file and add the following lines of code to it:

```python
from wagtail.blocks import (
    CharBlock,
    ChoiceBlock,
    RichTextBlock,
    StreamBlock,
    StructBlock,
)
from wagtail.embeds.blocks import EmbedBlock
from wagtail.images.blocks import ImageChooserBlock


class ImageBlock(StructBlock):
    image = ImageChooserBlock(required=True)
    caption = CharBlock(required=False)
    attribution = CharBlock(required=False)

    class Meta:
        icon = "image"
        template = "base/blocks/image_block.html"


class HeadingBlock(StructBlock):
    heading_text = CharBlock(classname="title", required=True)
    size = ChoiceBlock(
        choices=[
            ("", "Select a heading size"),
            ("h2", "H2"),
            ("h3", "H3"),
            ("h4", "H4"),
        ],
        blank=True,
        required=False,
    )

    class Meta:
        icon = "title"
        template = "base/blocks/heading_block.html"


class BaseStreamBlock(StreamBlock):
    heading_block = HeadingBlock()
    paragraph_block = RichTextBlock(icon="pilcrow")
    image_block = ImageBlock()
    embed_block = EmbedBlock(
        help_text="Insert a URL to embed. For example, https://www.youtube.com/watch?v=SGJFWirQ3ks",
        icon="media",
    )
```

In the preceding code, you created reusable Wagtail custom blocks for different content types in your general-purpose app. You can use these blocks across your site in any order.

`ImageBlock` inherits from `StructBlock`. `StructBlock` allows you to group several child blocks as a single block. Your `ImageBlock` has three child blocks. The first child block, `Image`, uses the `ImageChooserBlock` field block type. `ImageChooserBlock` allows you to select an existing image, or upload a new one. Its `required` argument has a value of `true`. This means that you must provide an image. `caption` and `attribution` child blocks use the `CharBlock` field block type, which allows single-line text input. Your `caption` and `attribution` child blocks have their `required` attributes set to `false`. This means you can leave them empty in your [admin interface](https://guide.wagtail.org/en-latest/concepts/wagtail-interfaces/#admin-interface).

Just as `ImageBlock`, your `HeadingBlock` also inherits from `StructBlock`. It has two child blocks. Its first child block, `heading_text`, uses `CharBlock` for specifying the heading text, and it's required. Its second child block, `size`, uses `ChoiceBlock` for selecting the heading size. It provides options for **h2**, **h3**, and **h4**. Both `blank=True` and `required=False` make the heading text optional in your [admin interface](https://guide.wagtail.org/en-latest/concepts/wagtail-interfaces/#admin-interface).

Your `BaseStreamBlock` class inherits from `StreamBlock`. `StreamBlock` defines a set of child block types that you can mix and repeat in any sequence like StreamField. Your `BaseStreamBlock` has four child blocks. The `heading_block` uses the previously defined `HeadingBlock`. `paragraph_block` uses `RichTextBlock`, which provides a WYSIWYG editor for creating formatted text. `image_block` uses the previously defined `ImageBlock` class. `embed_block` is a block for embedding external content like videos. It uses the Wagtail `EmbedBlock`. To discover more field block types that are available for use, read the [documentation on Field block types](field_block_types).

Also, you defined a `Meta` class within your `ImageBlock` and `HeadingBlock` blocks. The `Meta` classes provide metadata for the blocks, including icons to visually represent them. The `Meta` classes also include custom templates for rendering your `ImageBlock` and `HeadingBlock` blocks.

```note
Wagtail provides built-in templates to render each block. However, you can override the built-in template with a custom template.
```

Finally, you must add the custom templates that you defined in the `Meta` classes of your `ImageBlock` and `HeadingBlock` blocks.

To add the custom template of your `ImageBlock`, create a `base/templates/base/blocks/image_block.html` file and add the following to it:

```html+django
{% load wagtailimages_tags %}

<figure>
    {% image self.image fill-600x338 loading="lazy" %}
    <figcaption>{{ self.caption }} - {{ self.attribution }}</figcaption>
</figure>
```

To add the custom template of your `HeadingBlock` block, create a `base/templates/base/blocks/heading_block.html` file and add the following to it:

```html+django
{% if self.size == 'h2' %}
    <h2>{{ self.heading_text }}</h2>
{% elif self.size == 'h3' %}
    <h3>{{ self.heading_text }}</h3>
{% elif self.size == 'h4' %}
    <h4>{{ self.heading_text }}</h4>
{% endif %}
```

You can also create a custom template for a child block. For example, to create a custom template for `embed_block`, create a `base/templates/base/blocks/embed_block.html` file and add the following to it:

```html+django
{{ self }}
```


## Use created blocks in your portfolio app

You can use the reusable custom blocks you created in your general-purpose `base` app across your site. However, it's conventional to define the blocks you wish to use in a blocks.py file of the app you intend to use them in. You can then import the blocks from your app's `blocks.py` file for use in your `models.py` file.

Now create a `portfolio/blocks.py` file and import the block you intend to use as follows:

```python
from base.blocks import BaseStreamBlock

class PortfolioStreamBlock(BaseStreamBlock):
    pass
```

The preceding code defines a custom block named `PortfolioStreamBlock`, which inherits from `BaseStreamBlock`. The pass statement indicates a starting point. Later in the tutorial, you'll add custom block definitions and configurations to the `PortfolioStreamBlock`.

Now add the following to your 
`portfolio/models.py` file:

```python
from wagtail.models import Page
from wagtail.fields import StreamField
from wagtail.admin.panels import FieldPanel

from portfolio.blocks import PortfolioStreamBlock


class PortfolioPage(Page):
    parent_page_types = ["home.HomePage"]

    body = StreamField(
        PortfolioStreamBlock(),
        blank=True,
        use_json_field=True,
        help_text="Use this section to list your projects and skills.",
    )

    content_panels = Page.content_panels + [
        FieldPanel("body"),
    ]
```

In the preceding code, you defined a Wagtail `Page` named `PortfolioPage`. `parent_page_types = ["home.HomePage"]` specifies that your Portfolio page can only be a child page of Home Page. Your `body` field is a `StreamField`, which uses the `PortfolioStreamBlock` custom block that you imported from your `portfolio/blocks.py` file. `blank=True` indicates that you can leave this field empty in your admin interface. `help_text` provides a brief description of the field to guide editors.


Your next step is to create a template for your `PortfolioPage`. To do this, add the following to your `portfolio/templates/portfolio/portfolio_page.html` file:

```html+django
{% extends "base.html" %}

{% load wagtailcore_tags wagtailimages_tags %}

{% block body_class %}template-portfolio{% endblock %}

{% block content %}
    <h1>{{ page.title }}</h1>

    {{ page.body }}
{% endblock %}
```

Now migrate your database by running `python manage.py makemigrations` and then `python manage.py migrate`.

## Add more custom blocks

To add more custom blocks to your `PortfolioPage`'s body, modify your `portfolio/blocks.py` file:

```python
# import CharBlock, ListBlock, PageChooserBlock, PageChooserBlock, RichTextBlock, and StructBlock: 
from wagtail.blocks import (
    CharBlock,
    ListBlock,
    PageChooserBlock,
    RichTextBlock,
    StructBlock,
)

# import ImageChooserBlock:
from wagtail.images.blocks import ImageChooserBlock

from base.blocks import BaseStreamBlock

# add CardBlock:
class CardBlock(StructBlock):
    heading = CharBlock()
    text = RichTextBlock(features=["bold", "italic", "link"])
    image = ImageChooserBlock(required=False)

    class Meta:
        icon = "form"
        template = "portfolio/blocks/card_block.html"

# add FeaturedPostsBlock:
class FeaturedPostsBlock(StructBlock):
    heading = CharBlock()
    text = RichTextBlock(features=["bold", "italic", "link"], required=False)
    posts = ListBlock(PageChooserBlock(page_type="blog.BlogPage"))

    class Meta:
        icon = "folder-open-inverse"
        template = "portfolio/blocks/featured_posts_block.html"

class PortfolioStreamBlock(BaseStreamBlock):
    # delete the pass statement

    card = CardBlock(group="Sections")
    featured_posts = FeaturedPostsBlock(group="Sections")
```

In the preceding code, `CardBlock` has three child blocks, `heading`, `text` and `image`. You are already familiar with the field block types used by the child pages.

However, in your `FeaturedPostsBlock`, one of the child blocks, `posts`, uses `ListBlock`. `ListBlock` is a structural block type that allows you to have multiple sub-blocks of the same type.  You used it with `PageChooserBlock` to select only the Blog Page type pages. To better understand structural block types, read the [Structural block types documentation](streamfield_staticblock).

Furthermore, `icon = "form"` and `icon = "folder-open-inverse"` define custom block icons to set your blocks apart in the admin interface. For more information about block icons, read the [documentation on block icons](block_icons).

You used `group="Sections"` in `card = CardBlock(group="Sections")` and `featured_posts = FeaturedPostsBlock(group="Sections")` to categorize your `card` and `featured_posts` child blocks together within a category named `section`.

You probably know what your next step is. You have to create templates for your `CardBlock` and `FeaturedPostsBlock`.

To create a template for `CardBlock`, create a `portfolio/templates/portfolio/blocks/card_block.html` file and add the following to it:

```html+django
{% load wagtailcore_tags wagtailimages_tags %}
<div class="card">
    <h3>{{ self.heading }}</h3>
    <div>{{ self.text|richtext }}</div>
    {% if self.image %}
        {% image self.image width-480 %}
    {% endif %}
</div>
```

To create a template for `featured_posts_block`, create a `portfolio/templates/portfolio/blocks/featured_posts_block.html` file and add the following to it:

```html+django
{% load wagtailcore_tags %}
<div>
    <h2>{{ self.heading }}</h2>
    {% if self.text %}
        <p>{{ self.text|richtext }}</p>
    {% endif %}

    <div class="grid">
        {% for page in self.posts %}
            <div class="card">
                <p><a href="{% pageurl page %}">{{ page.title }}</a></p>
                <p>{{ page.specific.date }}</p>
            </div>
        {% endfor %}
    </div>
</div>
```

Finally, migrate your changes by running `python manage.py makemigrations` and then `python manage.py migrate`.

(add_your_resume)=

## Add your resume

To add your resume to your portfolio site, follow these steps:

1. Create a **Portfolio Page** as a child page of **Home** by following these steps:  

    a. Restart your server.  
    b. Go to your admin interface.  
    c. Click `Pages` in your [Sidebar](https://guide.wagtail.org/en-latest/how-to-guides/find-your-way-around/#the-sidebar).  
    d. Click `Home`.  
    e. Click the `...` icon at the top of the resulting page.  
    f. Click `add child page`.  
    g. Click `Portfolio Page`.  

2. Add the necessary data.
3. Publish your `Portfolio Page`.

Congratulations🎉! You now understand how to create complex flexible layouts with Wagtail StreamField. In the next tutorial, you'll learn how to add search functionality to your site.