(tagging)=

# Tagging

Wagtail provides tagging capabilities through the combination of two Django modules.

1. [django-taggit](https://django-taggit.readthedocs.io/) - Which provides a general-purpose tagging implementation.
2. [django-modelcluster](https://github.com/wagtail/django-modelcluster) - Which extends django-taggit's `TaggableManager` to allow tag relations to be managed in memory without writing to the database, necessary for handling previews and revisions.

## Adding tags to a page model

To add tagging to a page model, you'll need to define a 'through' model inheriting from `TaggedItemBase` to set up the many-to-many relationship between django-taggit's `Tag` model and your page model, and add a `ClusterTaggableManager` accessor to your page model to present this relation as a single tag field.

In this example, we set up tagging on `BlogPage` through a `BlogPageTag` model:

```python
# models.py

from modelcluster.fields import ParentalKey
from modelcluster.contrib.taggit import ClusterTaggableManager
from taggit.models import TaggedItemBase

class BlogPageTag(TaggedItemBase):
    content_object = ParentalKey('demo.BlogPage', on_delete=models.CASCADE, related_name='tagged_items')

class BlogPage(Page):
    ...
    tags = ClusterTaggableManager(through=BlogPageTag, blank=True)

    promote_panels = Page.promote_panels + [
        ...
        FieldPanel('tags'),
    ]
```

Wagtail's admin provides a nice interface for inputting tags into your content, with typeahead tag completion and friendly tag icons.

We can now make use of the many-to-many tag relationship in our views and templates. For example, we can set up the blog's index page to accept a `?tag=...` query parameter to filter the `BlogPage` listing by tag:

```python
from django.shortcuts import render

class BlogIndexPage(Page):
    ...
    def get_context(self, request):
        context = super().get_context(request)

        # Get blog entries
        blog_entries = BlogPage.objects.child_of(self).live()

        # Filter by tag
        tag = request.GET.get('tag')
        if tag:
            blog_entries = blog_entries.filter(tags__name=tag)

        context['blog_entries'] = blog_entries
        return context
```

Here, `blog_entries.filter(tags__name=tag)` follows the `tags` relation on `BlogPage`, to filter the listing to only those pages with a matching tag name before passing this to the template for rendering. We can now update the `blog_page.html` template to show a list of tags associated with the page, with links back to the filtered index page:

```html+django
{% for tag in page.tags.all %}
    <a href="{% pageurl page.blog_index %}?tag={{ tag }}">{{ tag }}</a>
{% endfor %}
```

Iterating through `page.tags.all` will display each tag associated with `page`, while the links back to the index make use of the filter option added to the `BlogIndexPage` model. A Django query could also use the `tagged_items` related name field to get `BlogPage` objects associated with a tag.

The same approach can be used to add tagging to non-page models managed through [](snippets). In this case, the model must inherit from `modelcluster.models.ClusterableModel` to be compatible with `ClusterTaggableManager`.

## Custom tag models

In the above example, any newly-created tags will be added to django-taggit's default `Tag` model, which will be shared by all other models using the same recipe as well as Wagtail's image and document models. In particular, this means that the autocompletion suggestions on tag fields will include tags previously added to other models. To avoid this, you can set up a custom tag model inheriting from `TagBase`, along with a 'through' model inheriting from `ItemBase`, which will provide an independent pool of tags for that page model.

```python
from django.db import models
from modelcluster.contrib.taggit import ClusterTaggableManager
from modelcluster.fields import ParentalKey
from taggit.models import TagBase, ItemBase

class BlogTag(TagBase):
    class Meta:
        verbose_name = "blog tag"
        verbose_name_plural = "blog tags"


class TaggedBlog(ItemBase):
    tag = models.ForeignKey(
        BlogTag, related_name="tagged_blogs", on_delete=models.CASCADE
    )
    content_object = ParentalKey(
        to='demo.BlogPage',
        on_delete=models.CASCADE,
        related_name='tagged_items'
    )

class BlogPage(Page):
    ...
    tags = ClusterTaggableManager(through='demo.TaggedBlog', blank=True)
```

Within the admin, the tag field will automatically recognize the custom tag model being used and will offer autocomplete suggestions taken from that tag model.

## Disabling free tagging

By default, tag fields work on a "free tagging" basis: editors can enter anything into the field, and upon saving, any tag text not recognized as an existing tag will be created automatically. To disable this behavior, and only allow editors to enter tags that already exist in the database, custom tag models accept a `free_tagging = False` option:

```python
from taggit.models import TagBase
from wagtail.snippets.models import register_snippet

@register_snippet
class BlogTag(TagBase):
    free_tagging = False

    class Meta:
        verbose_name = "blog tag"
        verbose_name_plural = "blog tags"
```

Here we have registered `BlogTag` as a snippet, to provide an interface for administrators (and other users with the appropriate permissions) to manage the allowed set of tags. With the `free_tagging = False` option set, editors can no longer enter arbitrary text into the tag field, and must instead select existing tags from the autocomplete dropdown.

## Managing tags as snippets

To manage all the tags used in a project, you can register the `Tag` model as a snippet to be managed via the Wagtail admin. This will allow you to have a tag admin interface within the main menu in which you can add, edit or delete your tags.

Tags that are removed from a content don't get deleted from the `Tag` model and will still be shown in typeahead tag completion. So having a tag interface is a great way to completely get rid of tags you don't need.

To add the tag interface, add the following block of code to a `wagtail_hooks.py` file within any of your project’s apps:

```python
from wagtail.admin.panels import FieldPanel
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet
from taggit.models import Tag


class TagsSnippetViewSet(SnippetViewSet):
    panels = [FieldPanel("name")]  # only show the name field
    model = Tag
    icon = "tag"  # change as required
    add_to_admin_menu = True
    menu_label = "Tags"
    menu_order = 200  # will put in 3rd place (000 being 1st, 100 2nd)
    list_display = ["name", "slug"]
    search_fields = ("name",)

register_snippet(TagsSnippetViewSet)
```

A `Tag` model has a `name` and `slug` required fields. If you decide to add a tag, it is recommended to only display the `name` field panel as the slug field is automatically populated when the `name` field is filled and you don't need to enter the same name in both fields.
