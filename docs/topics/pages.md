# Page models

Each page type (a.k.a. content type) in Wagtail is represented by a Django model. All page models must inherit from the {class}`wagtail.models.Page` class.

As all page types are Django models, you can use any field type that Django provides. See [Model field reference](inv:django#ref/models/fields) for a complete list of field types you can use. Wagtail also provides `wagtail.fields.RichTextField` which provides a WYSIWYG editor for editing rich-text content.

```{note}
If you're not yet familiar with Django models, have a quick look at the following links to get you started:

* {ref}`Creating models <django:creating-models>`
* {doc}`Model syntax <django:topics/db/models>`
```

## An example Wagtail page model

This example represents a typical blog post:

```python
from django.db import models

from modelcluster.fields import ParentalKey

from wagtail.models import Page, Orderable
from wagtail.fields import RichTextField
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, InlinePanel
from wagtail.search import index


class BlogPage(Page):

    # Database fields

    body = RichTextField()
    date = models.DateField("Post date")
    feed_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )


    # Search index configuration

    search_fields = Page.search_fields + [
        index.SearchField('body'),
        index.FilterField('date'),
    ]


    # Editor panels configuration

    content_panels = Page.content_panels + [
        FieldPanel('date'),
        FieldPanel('body'),
        InlinePanel('related_links', heading="Related links", label="Related link"),
    ]

    promote_panels = [
        MultiFieldPanel(Page.promote_panels, "Common page configuration"),
        FieldPanel('feed_image'),
    ]


    # Parent page / subpage type rules

    parent_page_types = ['blog.BlogIndex']
    subpage_types = []


class BlogPageRelatedLink(Orderable):
    page = ParentalKey(BlogPage, on_delete=models.CASCADE, related_name='related_links')
    name = models.CharField(max_length=255)
    url = models.URLField()

    panels = [
        FieldPanel('name'),
        FieldPanel('url'),
    ]
```

```{note}
Ensure that none of your field names are the same as your class names. This will cause errors due to the way Django handles relations ([read more](https://github.com/wagtail/wagtail/issues/503)). In our examples we have avoided this by appending "Page" to each model name.
```

## Writing page models

Here, we'll describe each section of the above example to help you create your own page models.

### Database fields

Each Wagtail page type is a Django model, represented in the database as a separate table.

Each page type can have its own set of fields. For example, a news article may have body text and a published date, whereas an event page may need separate fields for venue and start/finish times.

In Wagtail, you can use any Django field class. Most field classes provided by third party apps should work as well.

Wagtail also provides a couple of field classes of its own:

-   `RichTextField` - For rich text content
-   `StreamField` - A block-based content field (see: [Freeform page content using StreamField](./streamfield))

For tagging, Wagtail fully supports [django-taggit](https://django-taggit.readthedocs.org/en/latest/) so we recommend using that.

### Search

The `search_fields` attribute defines which fields are added to the search index and how they are indexed.

This should be a list of `SearchField` and `FilterField` objects. `SearchField` adds a field for full-text search. `FilterField` adds a field for filtering the results. A field can be indexed with both `SearchField` and `FilterField` at the same time (but only one instance of each).

In the above example, we've indexed `body` for full-text search and `date` for filtering.

The arguments that these field types accept are documented in [indexing extra fields](wagtailsearch_indexing_fields).

### Editor panels

There are a few attributes for defining how the page's fields will be arranged in the page editor interface:

-   `content_panels` - For content, such as main body text
-   `promote_panels` - For metadata, such as tags, thumbnail image and SEO title
-   `settings_panels` - For settings, such as publish date

Each of these attributes is set to a list of `Panel` objects, which defines which fields appear on which tabs and how they are structured on each tab.

Here's a summary of the `Panel` classes that Wagtail provides out of the box. See [Panel types](/reference/panels) for full descriptions.

**Basic**

These allow editing of model fields. The `FieldPanel` class will choose the correct widget based on the type of the field, such as a rich text editor for `RichTextField`, or an image chooser for a `ForeignKey` to an image model. `FieldPanel` also provides a page chooser interface for `ForeignKey`s to page models, but for more fine-grained control over which page types can be chosen, `PageChooserPanel` provides additional configuration options.

-   {class}`~wagtail.admin.panels.FieldPanel`
-   {class}`~wagtail.admin.panels.PageChooserPanel`

**Structural**

These are used for structuring fields in the interface.

-   {class}`~wagtail.admin.panels.MultiFieldPanel`
-   {class}`~wagtail.admin.panels.InlinePanel`
-   {class}`~wagtail.admin.panels.FieldRowPanel`

#### Customizing the page editor interface

The page editor can be customized further. See [Customizing the editing interface](/advanced_topics/customization/page_editing_interface).

(page_type_business_rules)=

### Parent page / subpage type rules

These two attributes allow you to control where page types may be used in your site. They allow you to define rules like "blog entries may only be created under a blog index".

Both parent and subpage types take a list of model classes or model names. Model names are of the format `app_label.ModelName`. If the `app_label` is omitted, the same app is assumed.

-   `parent_page_types` limits which page types this type can be created under
-   `subpage_types` limits which page types can be created under this type

By default, any page type can be created under any page type and it is not necessary to set these attributes if that's the desired behavior.

Setting `parent_page_types` to an empty list is a good way of preventing a particular page type from being created in the editor interface.

(page_descriptions)=

### Page descriptions

With every Wagtail Page you are able to add a helpful description text, similar to a `help_text` model attribute. By adding `page_description` to your Page model you'll be adding a short description that can be seen when you create a new page, edit an existing page or when you're prompted to select a child page type.

```python
class LandingPage(Page):

    page_description = "Use this page for converting users"
```

(page_urls)=

### Page URLs

The most common method of retrieving page URLs is by using the [`{% pageurl %}`](pageurl_tag) or [`{% fullpageurl %}`](fullpageurl_tag) template tags. Since it's called from a template, these automatically includes the optimizations mentioned below.

Page models also include several low-level methods for overriding or accessing page URLs.

#### Customizing URL patterns for a page model

The `Page.get_url_parts(request)` method will not typically be called directly, but may be overridden to define custom URL routing for a given page model. It should return a tuple of `(site_id, root_url, page_path)`, which are used by `get_url` and `get_full_url` (see below) to construct the given type of page URL.

When overriding `get_url_parts()`, you should accept `*args, **kwargs`:

```python
def get_url_parts(self, *args, **kwargs):
```

and pass those through at the point where you are calling `get_url_parts` on `super` (if applicable), for example:

```python
super().get_url_parts(*args, **kwargs)
```

While you could pass only the `request` keyword argument, passing all arguments as-is ensures compatibility with any
future changes to these method signatures.

For more information, please see {meth}`wagtail.models.Page.get_url_parts`.

#### Obtaining URLs for page instances

You can call the `Page.get_url(request)` method whenever you need a page URL. It defaults to returning local URLs (not including the protocol or domain) if it determines that the page is on the current site (via the hostname in `request`); otherwise, it would return a full URL including the protocol and domain. Whenever possible, you should include the optional `request` argument to enable per-request caching of site-level URL information and facilitate the generation of local URLs.

A common use case for `get_url(request)` is in any custom template tag your project may include for generating navigation menus. When writing such a custom template tag, ensure that it includes `takes_context=True` and uses `context.get('request')` to safely pass the
request or `None` if no request exists in the context.

For more information, please see {meth}`wagtail.models.Page.get_url`.

To retrieve the full URL (including the protocol and domain), use `Page.get_full_url(request)`. Whenever possible, the optional `request` argument should be included to enable per-request caching of site-level URL information.

For more information, please see {meth}`wagtail.models.Page.get_full_url`.

## Template rendering

Each page model can be given an HTML template which is rendered when a user browses to a page on the site frontend. This is the simplest and most common way to get Wagtail content to end users (but not the only way).

### Adding a template for a page model

Wagtail automatically chooses a name for the template based on the app label and model class name.

Format: `<app_label>/<model_name (snake cased)>.html`

For example, the template for the above blog page will be: `blog/blog_page.html`

You just need to create a template in a location where it can be accessed with this name.

### Template context

Wagtail renders templates with the `page` variable bound to the page instance being rendered. Use this to access the content of the page. For example, to get the title of the current page, use `{{ page.title }}`. All variables provided by [context processors](inv:django#subclassing-context-requestcontext) are also available.

#### Customizing template context

All pages have a `get_context` method that is called whenever the template is rendered and returns a dictionary of variables to bind into the template.

To add more variables to the template context, you can override this method:

```python
class BlogIndexPage(Page):
    ...

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)

        # Add extra variables and return the updated context
        context['blog_entries'] = BlogPage.objects.child_of(self).live()
        return context
```

The variables can then be used in the template:

```html+django
{{ page.title }}

{% for entry in blog_entries %}
    {{ entry.title }}
{% endfor %}
```

### Changing the template

Set the `template` attribute on the class to use a different template file:

```python
class BlogPage(Page):
    ...

    template = 'other_template.html'
```

#### Dynamically choosing the template

The template can be changed on a per-instance basis by defining a `get_template` method on the page class. This method is called every time the page is rendered:

```python
class BlogPage(Page):
    ...

    use_other_template = models.BooleanField()

    def get_template(self, request, *args, **kwargs):
        if self.use_other_template:
            return 'blog/other_blog_page.html'

        return 'blog/blog_page.html'
```

In this example, pages that have the `use_other_template` boolean field set will use the `blog/other_blog_page.html` template. All other pages will use the default `blog/blog_page.html`.

#### Ajax Templates

If you want to add AJAX functionality to a page, such as a paginated listing that updates in-place on the page rather than triggering a full page reload, you can set the `ajax_template` attribute to specify an alternative template to be used when the page is requested via an AJAX call (as indicated by the `X-Requested-With: XMLHttpRequest` HTTP header):

```python
class BlogPage(Page):
    ...

    ajax_template = 'other_template_fragment.html'
    template = 'other_template.html'
```

### More control over page rendering

All page classes have a `serve()` method that internally calls the `get_context` and `get_template` methods and renders the template. This method is similar to a Django view function, taking a Django `Request` object and returning a Django `Response` object.

This method can also be overridden for complete control over page rendering.

For example, here's a way to make a page respond with a JSON representation of itself:

```python
from django.http import JsonResponse


class BlogPage(Page):
    ...

    def serve(self, request):
        return JsonResponse({
            'title': self.title,
            'body': self.body,
            'date': self.date,

            # Resizes the image to 300px width and gets a URL to it
            'feed_image': self.feed_image.get_rendition('width-300').url,
        })
```

(inline_models)=

## Inline models

Wagtail allows the nesting of other models within a page. This is useful for creating repeated fields, such as related links or items to display in a carousel. Inline model content is also versioned with the rest of the page.

An inline model must have a `ParentalKey` pointing to the parent model. It can also inherit from {class}`wagtail.models.Orderable` to allow reordering of items in the admin interface.

````{note}
The model inlining feature is provided by [django-modelcluster](https://github.com/wagtail/django-modelcluster) and the `ParentalKey` field type must be imported from there:

```python
from modelcluster.fields import ParentalKey
```

`ParentalKey` is a subclass of Django's `ForeignKey`, and takes the same arguments.

````

For example, the following inline model can be used to add related links (a list of name, url pairs) to the `BlogPage` model:

```python
from django.db import models
from modelcluster.fields import ParentalKey
from wagtail.models import Orderable


class BlogPageRelatedLink(Orderable):
    page = ParentalKey(BlogPage, on_delete=models.CASCADE, related_name='related_links')
    name = models.CharField(max_length=255)
    url = models.URLField()

    panels = [
        FieldPanel('name'),
        FieldPanel('url'),
    ]
```

To add this to the admin interface, use the `InlinePanel` edit panel class:

```python
content_panels = [
    ...

    InlinePanel('related_links', label="Related links"),
]
```

The first argument must match the value of the `related_name` attribute of the `ParentalKey`.
For a brief description of parameters taken by `InlinePanel`, see {ref}`inline_panels`.

## Re-using inline models across multiple page types

In the above example, related links are defined as a child object on the `BlogPage` page type. Often, the same kind of inline child object will appear on several page types, and in these cases, it's undesirable to repeat the entire model definition. This can be avoided by refactoring the common fields into an abstract model:

```python
from django.db import models
from modelcluster.fields import ParentalKey
from wagtail.models import Orderable

# The abstract model for related links, complete with panels
class RelatedLink(models.Model):
    name = models.CharField(max_length=255)
    url = models.URLField()

    panels = [
        FieldPanel('name'),
        FieldPanel('url'),
    ]

    class Meta:
        abstract = True

# The real model which extends the abstract model with a ParentalKey relation back to the page model.
# This can be repeated for each page type where the relation is to be added
# (for example, NewsPageRelatedLink, PublicationPageRelatedLink and so on).
class BlogPageRelatedLink(Orderable,RelatedLink):
    page = ParentalKey(BlogPage, on_delete=models.CASCADE, related_name='related_links')
```

Alternatively, if RelatedLink is going to appear on a significant number of the page types defined in your project, it may be more appropriate to set up a single `RelatedLink` model pointing to the base `wagtailcore.Page` model:

```python
class RelatedLink(Orderable):
    page = ParentalKey("wagtailcore.Page", on_delete=models.CASCADE, related_name='related_links')
    name = models.CharField(max_length=255)
    url = models.URLField()
    panels = [
        FieldPanel('name'),
        FieldPanel('url'),
    ]
```

This will then make `related_links` available as a relation across all page types, although it will still only be editable on page types that include the `InlinePanel` in their panel definitions - for other page types, the set of related links will remain empty.

## Working with pages

Wagtail uses Django's [multi-table inheritance](inv:django#meta-and-multi-table-inheritance) feature to allow multiple page models to be used in the same tree.

Each page is added to both Wagtail's built-in {class}`~wagtail.models.Page` model as well as its user-defined model (such as the `BlogPage` model created earlier).

Pages can exist in Python code in two forms, an instance of `Page` or an instance of the page model.

When working with multiple page types together, you will typically use instances of Wagtail's `Page` model, which don't give you access to any fields specific to their type.

```python
# Get all pages in the database
>>> from wagtail.models import Page
>>> Page.objects.all()
[<Page: Homepage>, <Page: About us>, <Page: Blog>, <Page: A Blog post>, <Page: Another Blog post>]
```

When working with a single page type, you can work with instances of the user-defined model. These give access to all the fields available in `Page`, along with any user-defined fields for that type.

```python
# Get all blog entries in the database
>>> BlogPage.objects.all()
[<BlogPage: A Blog post>, <BlogPage: Another Blog post>]
```

You can convert a `Page` object to its more specific user-defined equivalent using the `.specific` property. This may cause an additional database lookup.

```python
>>> page = Page.objects.get(title="A Blog post")
>>> page
<Page: A Blog post>

# Note: the blog post is an instance of Page so we cannot access body, date or feed_image

>>> page.specific
<BlogPage: A Blog post>
```

## Tips

### Friendly model names

You can make your model names more friendly to users of Wagtail by using Django's internal `Meta` class with a `verbose_name`, for example:

```python
class HomePage(Page):
    ...

    class Meta:
        verbose_name = "homepage"
```

When users are given a choice of pages to create, the list of page types is generated by splitting your model names on each of their capital letters. Thus a `HomePage` model would be named "Home Page" which is a little clumsy. Defining `verbose_name` as in the example above would change this to read "Homepage", which is slightly more conventional.

### Page QuerySet ordering

`Page`-derived models _cannot_ be given a default ordering by using the standard Django approach of adding an `ordering` attribute to the internal `Meta` class.

```python
class NewsItemPage(Page):
    publication_date = models.DateField()
    ...

    class Meta:
        ordering = ('-publication_date', )  # will not work
```

This is because `Page` enforces ordering QuerySets by path. Instead, you must apply the ordering explicitly when constructing a QuerySet:

```python
news_items = NewsItemPage.objects.live().order_by('-publication_date')
```

(custom_page_managers)=

### Custom Page managers

You can add a custom `Manager` to your `Page` class. Any custom Managers should inherit from `wagtail.models.PageManager`:

```python
from django.db import models
from wagtail.models import Page, PageManager

class EventPageManager(PageManager):
    """ Custom manager for Event pages """

class EventPage(Page):
    start_date = models.DateField()

    objects = EventPageManager()
```

Alternately, if you only need to add extra `QuerySet` methods, you can inherit from `wagtail.models.PageQuerySet` to build a custom `Manager`:

```python
from django.db import models
from django.utils import timezone
from wagtail.models import Page, PageManager, PageQuerySet

class EventPageQuerySet(PageQuerySet):
    def future(self):
        today = timezone.localtime(timezone.now()).date()
        return self.filter(start_date__gte=today)

EventPageManager = PageManager.from_queryset(EventPageQuerySet)

class EventPage(Page):
    start_date = models.DateField()

    objects = EventPageManager()
```
