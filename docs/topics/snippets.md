(snippets)=

# Snippets

Snippets are pieces of content which do not necessitate a full webpage to render. They could be used for making secondary content, such as headers, footers, and sidebars, editable in the Wagtail admin. Snippets are Django models which do not inherit the {class}`~wagtail.models.Page` class and are thus not organised into the Wagtail tree. However, they can still be made editable by assigning panels and identifying the model as a snippet with the `register_snippet` class decorator.

Snippets lack many of the features of pages, such as being orderable in the Wagtail admin or having a defined URL. Decide carefully if the content type you would want to build into a snippet might be more suited to a page.

## Snippet models

Here's an example snippet model:

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

The `Advert` model uses the basic Django model class and defines two properties: text and URL. The editing interface is very close to that provided for `Page`-derived models, with fields assigned in the `panels` property. Snippets do not use multiple tabs of fields, nor do they provide the "save as draft" or "submit for moderation" features.

`@register_snippet` tells Wagtail to treat the model as a snippet. The `panels` list defines the fields to show on the snippet editing page. It's also important to provide a string representation of the class through `def __str__(self):` so that the snippet objects make sense when listed in the Wagtail admin.

## Including snippets in template tags

The simplest way to make your snippets available to templates is with a template tag. This is mostly done with vanilla Django, so perhaps reviewing Django's documentation for [custom template tags](django:howto/custom-template-tags) will be more helpful. We'll go over the basics, though, and point out any considerations to make for Wagtail.

First, add a new python file to a `templatetags` folder within your app - for example, `myproject/demo/templatetags/demo_tags.py`. We'll need to load some Django modules and our app's models, and ready the `register` decorator:

```python
from django import template
from demo.models import Advert

register = template.Library()

# ...

# Advert snippets
@register.inclusion_tag('demo/tags/adverts.html', takes_context=True)
def adverts(context):
    return {
        'adverts': Advert.objects.all(),
        'request': context['request'],
    }
```

`@register.inclusion_tag()` takes two variables: a template and a boolean on whether that template should be passed a request context. It's a good idea to include request contexts in your custom template tags, since some Wagtail-specific template tags like `pageurl` need the context to work properly. The template tag function could take arguments and filter the adverts to return a specific instance of the model, but for brevity, we'll just use `Advert.objects.all()`.

Here's what's in the template used by this template tag:

```html+django
{% for advert in adverts %}
    <p>
        <a href="{{ advert.url }}">
            {{ advert.text }}
        </a>
    </p>
{% endfor %}
```

Then, in your own page templates, you can include your snippet template tag with:

```html+django
{% load wagtailcore_tags demo_tags %}

...

{% block content %}

    ...

    {% adverts %}

{% endblock %}
```

## Binding pages to snippets

In the above example, the list of adverts is a fixed list that is displayed via the custom template tag independent of any other content on the page. This might be what you want for a common panel in a sidebar, but, in another scenario, you might wish to display just one specific instance of a snippet on a particular page. This can be accomplished by defining a foreign key to the snippet model within your page model and adding a {class}`~wagtail.admin.panels.FieldPanel` to the page's `content_panels` list. For example, if you wanted to display a specific advert on a `BookPage` instance:

```python
  # ...
  class BookPage(Page):
      advert = models.ForeignKey(
          'demo.Advert',
          null=True,
          blank=True,
          on_delete=models.SET_NULL,
          related_name='+'
      )

      content_panels = Page.content_panels + [
          FieldPanel('advert'),
          # ...
      ]
```

The snippet could then be accessed within your template as `page.advert`.

To attach multiple adverts to a page, the `FieldPanel` can be placed on an inline child object of `BookPage` rather than on `BookPage` itself. Here, this child model is named `BookPageAdvertPlacement` (so-called because there is one such object for each time that an advert is placed on a BookPage):

```python
from django.db import models

from wagtail.models import Page, Orderable

from modelcluster.fields import ParentalKey

# ...

class BookPageAdvertPlacement(Orderable, models.Model):
    page = ParentalKey('demo.BookPage', on_delete=models.CASCADE, related_name='advert_placements')
    advert = models.ForeignKey('demo.Advert', on_delete=models.CASCADE, related_name='+')

    class Meta(Orderable.Meta):
        verbose_name = "advert placement"
        verbose_name_plural = "advert placements"

    panels = [
        FieldPanel('advert'),
    ]

    def __str__(self):
        return self.page.title + " -> " + self.advert.text


class BookPage(Page):
    # ...

    content_panels = Page.content_panels + [
        InlinePanel('advert_placements', label="Adverts"),
        # ...
    ]
```

These child objects are now accessible through the page's `advert_placements` property, and from there we can access the linked `Advert` snippet as `advert`. In the template for `BookPage`, we could include the following:

```html+django
{% for advert_placement in page.advert_placements.all %}
    <p>
        <a href="{{ advert_placement.advert.url }}">
            {{ advert_placement.advert.text }}
        </a>
    </p>
{% endfor %}
```

(wagtailsnippets_making_snippets_previewable)=

## Making snippets previewable

```{versionadded} 4.0
The `PreviewableMixin` class was introduced.
```

If a snippet model inherits from {class}`~wagtail.models.PreviewableMixin`, Wagtail will automatically add a live preview panel in the editor. In addition to inheriting the mixin, the model must also override {meth}`~wagtail.models.PreviewableMixin.get_preview_template` or {meth}`~wagtail.models.PreviewableMixin.serve_preview`. For example, the `Advert` snippet could be made previewable as follows:

```python
# ...

from wagtail.models import PreviewableMixin

# ...

@register_snippet
class Advert(PreviewableMixin, models.Model):
    url = models.URLField(null=True, blank=True)
    text = models.CharField(max_length=255)

    panels = [
        FieldPanel('url'),
        FieldPanel('text'),
    ]

    def get_preview_template(self, request, mode_name):
        return "demo/previews/advert.html"
```

With the following `demo/previews/advert.html` template:

```html+django
<!DOCTYPE html>
<html>
    <head>
        <title>{{ object.text }}</title>
    </head>
    <body>
        <a href="{{ object.url }}">{{ object.text }}</a>
    </body>
</html>
```

The variables available in the default context are `request` (a fake {class}`~django.http.HttpRequest` object) and `object` (the snippet instance). To customise the context, you can override the {meth}`~wagtail.models.PreviewableMixin.get_preview_context` method.

By default, the `serve_preview` method returns a {class}`~django.template.response.TemplateResponse` that is rendered using the request object, the template returned by `get_preview_template`, and the context object returned by `get_preview_context`. You can override the `serve_preview` method to customise the rendering and/or routing logic.

Similar to pages, you can define multiple preview modes by overriding the {attr}`~wagtail.models.PreviewableMixin.preview_modes` property. For example, the following `Advert` snippet has two preview modes:

```python
# ...

from wagtail.models import PreviewableMixin

# ...

@register_snippet
class Advert(PreviewableMixin, models.Model):
    url = models.URLField(null=True, blank=True)
    text = models.CharField(max_length=255)

    panels = [
        FieldPanel('url'),
        FieldPanel('text'),
    ]

    @property
    def preview_modes(self):
        return PreviewableMixin.DEFAULT_PREVIEW_MODES + [("alt", "Alternate")]

    def get_preview_template(self, request, mode_name):
        templates = {
            "": "demo/previews/advert.html",  # Default preview mode
            "alt": "demo/previews/advert_alt.html",  # Alternate preview mode
        }
        return templates.get(mode_name, templates[""])

    def get_preview_context(self, request, mode_name):
        context = super().get_preview_context(request, mode_name)
        if mode_name == "alt":
            context["extra_context"] = "Alternate preview mode"
        return context
```

(wagtailsnippets_making_snippets_searchable)=

## Making snippets searchable

If a snippet model inherits from {class}`wagtail.search.index.Indexed`, as described in [](wagtailsearch_indexing_models), Wagtail will automatically add a search box to the chooser interface for that snippet type. For example, the `Advert` snippet could be made searchable as follows:

```python
# ...

from wagtail.search import index

# ...

@register_snippet
class Advert(index.Indexed, models.Model):
    url = models.URLField(null=True, blank=True)
    text = models.CharField(max_length=255)

    panels = [
        FieldPanel('url'),
        FieldPanel('text'),
    ]

    search_fields = [
        index.SearchField('text', partial_match=True),
    ]
```

(wagtailsnippets_saving_revisions_of_snippets)=

## Saving revisions of snippets

```{versionadded} 4.0
The `RevisionMixin` class was introduced.
```

If a snippet model inherits from {class}`~wagtail.models.RevisionMixin`, Wagtail will automatically save revisions when you save any changes in the snippets admin.
In addition to inheriting the mixin, it is recommended to define a {class}`~django.contrib.contenttypes.fields.GenericRelation` to the {class}`~wagtail.models.Revision` model and override the {attr}`~wagtail.models.RevisionMixin.revisions` property to return the `GenericRelation`. For example, the `Advert` snippet could be made revisable as follows:

```python
# ...

from django.contrib.contenttypes.fields import GenericRelation
from wagtail.models import RevisionMixin

# ...

@register_snippet
class Advert(RevisionMixin, models.Model):
    url = models.URLField(null=True, blank=True)
    text = models.CharField(max_length=255)
    _revisions = GenericRelation("wagtailcore.Revision", related_query_name="advert")

    panels = [
        FieldPanel('url'),
        FieldPanel('text'),
    ]

    @property
    def revisions(self):
        return self._revisions
```

If your snippet model defines relations using Django's {class}`~django.db.models.ForeignKey` or {class}`~django.db.models.ManyToManyField`, you need to change the model class to inherit from `modelcluster.models.ClusterableModel` instead of `django.models.Model` and replace the `ForeignKey` and `ManyToManyField` with `ParentalKey` and `ParentalManyToManyField`, respectively. This is necessary in order to allow the relations to be stored in the revisions. For example:

```python
from django.db import models
from modelcluster.fields import ParentalKey, ParentalManyToManyField
from modelcluster.models import ClusterableModel
from wagtail.models import RevisionMixin


class ShirtColour(models.Model):
    name = models.CharField(max_length=255)

    panels = [FieldPanel("name")]


class ShirtCategory(models.Model):
    name = models.CharField(max_length=255)

    panels = [FieldPanel("name")]


@register_snippet
class Shirt(RevisionMixin, ClusterableModel):
    name = models.CharField(max_length=255)
    colour = ParentalKey("shirts.ShirtColour")
    categories = ParentalManyToManyField("shirts.ShirtCategory", blank=True)
    _revisions = GenericRelation("wagtailcore.Revision", related_query_name="shirt")

    panels = [
        FieldPanel("name"),
        FieldPanel("colour"),
        FieldPanel("categories", widget=forms.CheckboxSelectMultiple),
    ]

    @property
    def revisions(self):
        return self._revisions
```

The `RevisionMixin` includes a `latest_revision` field that needs to be added to your database table. Make sure to run the `makemigrations` and `migrate` management commands after making the above changes to apply the changes to your database.

With the `RevisionMixin` applied, any changes made from the snippets admin will create an instance of the `Revision` model that contains the state of the snippet instance. The revision instance is attached to the [audit log](audit_log) entry of the edit action, allowing you to revert to a previous revision or compare the changes between revisions from the snippet history page.

You can also save revisions programmatically by calling the {meth}`~wagtail.models.RevisionMixin.save_revision` method. After applying the mixin, it is recommended to call this method (or save the snippet in the admin) at least once for each instance of the snippet that already exists (if any), so that the `latest_revision` field is populated in the database table.

(wagtailsnippets_saving_draft_changes_of_snippets)=

## Saving draft changes of snippets

```{versionadded} 4.0
The `DraftStateMixin` class was introduced.
```

```{versionadded} 4.1
Support for scheduled publishing via `PublishingPanel` was introduced.
```

If a snippet model inherits from {class}`~wagtail.models.DraftStateMixin`, Wagtail will automatically add a live/draft status column to the listing view, change the "Save" action menu to "Save draft", and add a new "Publish" action menu in the editor. Any changes you save in the snippets admin will be saved as revisions and will not be reflected in the "live" snippet instance until you publish the changes.

As the `DraftStateMixin` works by saving draft changes as revisions, inheriting from this mixin also requires inheriting from `RevisionMixin`. See [](wagtailsnippets_saving_revisions_of_snippets) above for more details.

Wagtail will also allow you to set publishing schedules for instances of the model if there is a `PublishingPanel` in the model's panels definition.

For example, the `Advert` snippet could save draft changes and publishing schedules by defining it as follows:

```python
# ...

from django.contrib.contenttypes.fields import GenericRelation
from wagtail.admin.panels import PublishingPanel
from wagtail.models import DraftStateMixin, RevisionMixin

# ...

@register_snippet
class Advert(DraftStateMixin, RevisionMixin, models.Model):
    url = models.URLField(null=True, blank=True)
    text = models.CharField(max_length=255)
    _revisions = GenericRelation("wagtailcore.Revision", related_query_name="advert")

    panels = [
        FieldPanel('url'),
        FieldPanel('text'),
        PublishingPanel(),
    ]

    @property
    def revisions(self):
        return self._revisions
```

The `DraftStateMixin` includes additional fields that need to be added to your database table. Make sure to run the `makemigrations` and `migrate` management commands after making the above changes to apply the changes to your database.

You can publish revisions programmatically by calling {meth}`instance.publish(revision) <wagtail.models.DraftStateMixin.publish>` or by calling {meth}`revision.publish() <wagtail.models.Revision.publish>`. After applying the mixin, it is recommended to publish at least one revision for each instance of the snippet that already exists (if any), so that the `latest_revision` and `live_revision` fields are populated in the database table.

If you use the scheduled publishing feature, make sure that you run the [`publish_scheduled`](publish_scheduled) management command periodically. For more details, see [](scheduled_publishing).

```{versionadded} 4.2
For models that extend `DraftStateMixin`, `publish` permissions are automatically created.
```

Publishing a snippet instance requires `publish` permission on the snippet model. For models with `DraftStateMixin` applied, Wagtail automatically creates the corresponding `publish` permissions and display them in the 'Groups' area of the Wagtail admin interface. For more details on how to configure the permission, see [](permissions_overview).

```{warning}
Wagtail does not yet have a mechanism to prevent editors from including unpublished ("draft") snippets in pages. When including a `DraftStateMixin`-enabled snippet in pages, make sure that you add necessary checks to handle how a draft snippet should be rendered (e.g. by checking its `live` field). We are planning to improve this in the future.
```

(wagtailsnippets_locking_snippets)=

## Locking snippets

```{versionadded} 4.2
The `LockableMixin` class was introduced.
```

If a snippet model inherits from {class}`~wagtail.models.LockableMixin`, Wagtail will automatically add the ability to lock instances of the model. When editing, Wagtail will show the locking information in the "Status" side panel, and a button to lock/unlock the instance if the user has the permission to do so.

If the model is also configured to have scheduled publishing (as shown in [](wagtailsnippets_saving_draft_changes_of_snippets) above), Wagtail will lock any instances that are scheduled for publishing.

Similar to pages, users who locked a snippet can still edit it, unless [`WAGTAILADMIN_GLOBAL_EDIT_LOCK`](wagtailadmin_global_edit_lock) is set to `True`.

For example, instances of the `Advert` snippet could be locked by defining it as follows:

```python
# ...

from wagtail.models import LockableMixin

# ...

@register_snippet
class Advert(LockableMixin, models.Model):
    url = models.URLField(null=True, blank=True)
    text = models.CharField(max_length=255)

    panels = [
        FieldPanel('url'),
        FieldPanel('text'),
    ]
```

The `LockableMixin` includes additional fields that need to be added to your database table. Make sure to run the `makemigrations` and `migrate` management commands after making the above changes to apply the changes to your database.

Locking and unlocking a snippet instance requires `lock` and `unlock` permissions on the snippet model, respectively. For models with `LockableMixin` applied, Wagtail automatically creates the corresponding `lock` and `unlock` permissions and display them in the 'Groups' area of the Wagtail admin interface. For more details on how to configure the permission, see [](permissions).

## Tagging snippets

Adding tags to snippets is very similar to adding tags to pages. The only difference is that {class}`taggit.manager.TaggableManager` should be used in the place of {class}`~modelcluster.contrib.taggit.ClusterTaggableManager`.

```python
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from taggit.models import TaggedItemBase
from taggit.managers import TaggableManager

class AdvertTag(TaggedItemBase):
    content_object = ParentalKey('demo.Advert', on_delete=models.CASCADE, related_name='tagged_items')

@register_snippet
class Advert(ClusterableModel):
    # ...
    tags = TaggableManager(through=AdvertTag, blank=True)

    panels = [
        # ...
        FieldPanel('tags'),
    ]
```

The [documentation on tagging pages](tagging) has more information on how to use tags in views.

(wagtailsnippets_custom_admin_views)=

## Customising snippets admin views

You can customise the admin views for snippets by specifying a custom subclass of {class}`~wagtail.snippets.views.snippets.SnippetViewSet` to `register_snippet`.

This can be done by removing the `@register_snippet` decorator on your model class and calling `register_snippet` (as a function, not a decorator) in your `wagtail_hooks.py` file instead as follows:

```
register_snippet(MyModel, viewset=MyModelViewSet)
```

For example, with the following `Member` model and a `MemberFilterSet` class:

```python
# models.py
from django.db import models
from wagtail.admin.filters import WagtailFilterSet


class Member(models.Model):
    class ShirtSize(models.TextChoices):
        SMALL = "S", "Small"
        MEDIUM = "M", "Medium"
        LARGE = "L", "Large"
        EXTRA_LARGE = "XL", "Extra Large"

    name = models.CharField(max_length=255)
    shirt_size = models.CharField(max_length=5, choices=ShirtSize.choices, default=ShirtSize.MEDIUM)

    def get_shirt_size_display(self):
        return self.ShirtSize(self.shirt_size).label

    get_shirt_size_display.admin_order_field = "shirt_size"
    get_shirt_size_display.short_description = "Size description"


class MemberFilterSet(WagtailFilterSet):
    class Meta:
        model = Member
        fields = ["shirt_size"]
```

You can define a {attr}`~wagtail.snippets.views.snippets.SnippetViewSet.list_display` attribute to specify the columns shown on the listing view. You can also add the ability to filter the listing view by defining a {attr}`~wagtail.snippets.views.snippets.SnippetViewSet.filterset_class` attribute on a subclass of `SnippetViewSet`. For example:

```python
# views.py
from wagtail.admin.ui.tables import UpdatedAtColumn
from wagtail.snippets.views.snippets import SnippetViewSet

from myapp.models import MemberFilterSet


class MemberViewSet(SnippetViewSet):
    list_display = ["name", "shirt_size", "get_shirt_size_display", UpdatedAtColumn()]
    filterset_class = MemberFilterSet
```

Then, pass the viewset to the `register_snippet` call.

```python
# wagtail_hooks.py
from wagtail.snippets.models import register_snippet

from myapp.models import Member
from myapp.views import MemberViewSet


register_snippet(Member, viewset=MemberViewSet)
```

The `viewset` parameter of `register_snippet` also accepts a dotted module path to the subclass, e.g. `"myapp.views.MemberViewSet"`.

Various additional attributes are available to customise the viewset - see {class}`~wagtail.snippets.views.snippets.SnippetViewSet`.
