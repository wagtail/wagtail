(wagtailsnippets_features)=

# Optional features

By default, snippets lack many of the features of pages, such as previews, revisions, and workflows. These features can individually be added to each snippet model by inheriting from the appropriate mixin classes.

(wagtailsnippets_making_snippets_previewable)=

## Making snippets previewable

If a snippet model inherits from {class}`~wagtail.models.PreviewableMixin`, Wagtail will automatically add a live preview panel in the editor. In addition to inheriting the mixin, the model must also override {meth}`~wagtail.models.PreviewableMixin.get_preview_template` or {meth}`~wagtail.models.PreviewableMixin.serve_preview`. For example, the `Advert` snippet could be made previewable as follows:

```python
# ...
from wagtail.models import PreviewableMixin
# ...


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

The variables available in the default context are `request` (a fake {class}`~django.http.HttpRequest` object) and `object` (the snippet instance). To customize the context, you can override the {meth}`~wagtail.models.PreviewableMixin.get_preview_context` method.

By default, the `serve_preview` method returns a {class}`~django.template.response.TemplateResponse` that is rendered using the request object, the template returned by `get_preview_template`, and the context object returned by `get_preview_context`. You can override the `serve_preview` method to customize the rendering and/or routing logic.

Similar to pages, you can define multiple preview modes by overriding the {attr}`~wagtail.models.PreviewableMixin.preview_modes` property. For example, the following `Advert` snippet has two preview modes:

```python
# ...
from wagtail.models import PreviewableMixin
# ...


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

If a snippet model inherits from `wagtail.search.index.Indexed`, as described in [](wagtailsearch_indexing_models), Wagtail will automatically add a search box to the chooser interface for that snippet type. For example, the `Advert` snippet could be made searchable as follows:

```python
# ...
from wagtail.search import index
# ...


class Advert(index.Indexed, models.Model):
    url = models.URLField(null=True, blank=True)
    text = models.CharField(max_length=255)

    panels = [
        FieldPanel('url'),
        FieldPanel('text'),
    ]

    search_fields = [
        index.SearchField('text'),
        index.AutocompleteField('text'),
    ]
```

(wagtailsnippets_saving_revisions_of_snippets)=

## Saving revisions of snippets

If a snippet model inherits from {class}`~wagtail.models.RevisionMixin`, Wagtail will automatically save revisions when you save any changes in the snippets admin.

The mixin defines a `revisions` property that gives you a queryset of all revisions for the snippet instance. It also comes with a default {class}`~django.contrib.contenttypes.fields.GenericRelation` to the {class}`~wagtail.models.Revision` model so that the revisions are properly cleaned up when the snippet instance is deleted.

The default `GenericRelation` does not have a {attr}`~django.contrib.contenttypes.fields.GenericRelation.related_query_name`, so it does not give you the ability to query and filter from the `Revision` model back to the snippet model. If you would like this feature, you can define your own `GenericRelation` with a custom `related_query_name`.

For more details, see the default `GenericRelation` {attr}`~wagtail.models.RevisionMixin._revisions` and the property {attr}`~wagtail.models.RevisionMixin.revisions`.

```{versionadded} 7.1
The default `GenericRelation` {attr}`~wagtail.models.RevisionMixin._revisions` was added.
```

For example, the `Advert` snippet could be made revisable as follows:

```python
# ...
from django.contrib.contenttypes.fields import GenericRelation
from wagtail.models import RevisionMixin
# ...


class Advert(RevisionMixin, models.Model):
    url = models.URLField(null=True, blank=True)
    text = models.CharField(max_length=255)
    # If no custom logic is required, this can be defined as `revisions` directly
    _revisions = GenericRelation("wagtailcore.Revision", related_query_name="advert")

    panels = [
        FieldPanel('url'),
        FieldPanel('text'),
    ]

    @property
    def revisions(self):
        # Some custom logic here if necessary, e.g. to handle multi-table inheritance.
        # The mixin already handles inheritance, so this is optional.
        return self._revisions.all()
```

If your snippet model defines relations using Django's {class}`~django.db.models.ManyToManyField`, you need to change the model class to inherit from `modelcluster.models.ClusterableModel` instead of `django.models.Model` and replace the `ManyToManyField` with `ParentalManyToManyField`. Inline models should continue to use `ParentalKey` instead of `ForeignKey`. This is necessary in order to allow the relations to be stored in the revisions. See the [](tutorial_categories) section of the tutorial for more details. For example:

```python
# ...
from django.db import models
from modelcluster.fields import ParentalKey, ParentalManyToManyField
from modelcluster.models import ClusterableModel
from wagtail.models import RevisionMixin
# ...


class ShirtColour(models.Model):
    name = models.CharField(max_length=255)

    panels = [FieldPanel("name")]


class ShirtCategory(models.Model):
    name = models.CharField(max_length=255)

    panels = [FieldPanel("name")]


class Shirt(RevisionMixin, ClusterableModel):
    name = models.CharField(max_length=255)
    colour = models.ForeignKey("shirts.ShirtColour", on_delete=models.SET_NULL, blank=True, null=True)
    categories = ParentalManyToManyField("shirts.ShirtCategory", blank=True)
    revisions = GenericRelation("wagtailcore.Revision", related_query_name="shirt")

    panels = [
        FieldPanel("name"),
        FieldPanel("colour"),
        FieldPanel("categories", widget=forms.CheckboxSelectMultiple),
        InlinePanel("images", label="Images"),
    ]


class ShirtImage(models.Model):
    shirt = ParentalKey("shirts.Shirt", related_name="images")
    image = models.ForeignKey("wagtailimages.Image", on_delete=models.CASCADE, related_name="+")
    caption = models.CharField(max_length=255, blank=True)
    panels = [
        FieldPanel("image"),
        FieldPanel("caption"),
    ]
```

The `RevisionMixin` includes a `latest_revision` field that needs to be added to your database table. Make sure to run the `makemigrations` and `migrate` management commands after making the above changes to apply the changes to your database.

With the `RevisionMixin` applied, any changes made from the snippets admin will create an instance of the `Revision` model that contains the state of the snippet instance. The revision instance is attached to the [audit log](audit_log) entry of the edit action, allowing you to revert to a previous revision or compare the changes between revisions from the snippet history page.

You can also save revisions programmatically by calling the {meth}`~wagtail.models.RevisionMixin.save_revision` method. After applying the mixin, it is recommended to call this method (or save the snippet in the admin) at least once for each instance of the snippet that already exists (if any), so that the `latest_revision` field is populated in the database table.

(wagtailsnippets_saving_draft_changes_of_snippets)=

## Saving draft changes of snippets

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

Publishing a snippet instance requires `publish` permission on the snippet model. For models with `DraftStateMixin` applied, Wagtail automatically creates the corresponding `publish` permissions and displays them in the 'Groups' area of the Wagtail admin interface. For more details on how to configure the permission, see [](permissions_overview).

```{warning}
Wagtail does not yet have a mechanism to prevent editors from including unpublished ("draft") snippets in pages. When including a `DraftStateMixin`-enabled snippet in pages, make sure that you add necessary checks to handle how a draft snippet should be rendered (for example, by checking its `live` field). We are planning to improve this in the future.
```

(wagtailsnippets_locking_snippets)=

## Locking snippets

If a snippet model inherits from {class}`~wagtail.models.LockableMixin`, Wagtail will automatically add the ability to lock instances of the model. When editing, Wagtail will show the locking information in the "Status" side panel, and a button to lock/unlock the instance if the user has the permission to do so.

If the model is also configured to have scheduled publishing (as shown in [](wagtailsnippets_saving_draft_changes_of_snippets) above), Wagtail will lock any instances that are scheduled for publishing.

Similar to pages, users who locked a snippet can still edit it, unless [`WAGTAILADMIN_GLOBAL_EDIT_LOCK`](wagtailadmin_global_edit_lock) is set to `True`.

For example, instances of the `Advert` snippet could be locked by defining it as follows:

```python
# ...
from wagtail.models import LockableMixin
# ...


class Advert(LockableMixin, models.Model):
    url = models.URLField(null=True, blank=True)
    text = models.CharField(max_length=255)

    panels = [
        FieldPanel('url'),
        FieldPanel('text'),
    ]
```

If you use the other mixins, make sure to apply `LockableMixin` after the other mixins, but before the `RevisionMixin` (in left-to-right order). For example, with `DraftStateMixin` and `RevisionMixin`, the correct inheritance of the model would be `class MyModel(DraftStateMixin, LockableMixin, RevisionMixin)`. There is a system check to enforce the ordering of the mixins.

The `LockableMixin` includes additional fields that need to be added to your database table. Make sure to run the `makemigrations` and `migrate` management commands after making the above changes to apply the changes to your database.

Locking and unlocking a snippet instance requires `lock` and `unlock` permissions on the snippet model, respectively. For models with `LockableMixin` applied, Wagtail automatically creates the corresponding `lock` and `unlock` permissions and displays them in the 'Groups' area of the Wagtail admin interface. For more details on how to configure the permission, see [](permissions_overview).

(wagtailsnippets_enabling_workflows)=

## Enabling workflows for snippets

If a snippet model inherits from {class}`~wagtail.models.WorkflowMixin`, Wagtail will automatically add the ability to assign a workflow to the model. With a workflow assigned to the snippet model, a "Submit for moderation" and other workflow action menu items will be shown in the editor. The status side panel will also show the information on the current workflow.

Since the `WorkflowMixin` utilizes revisions and publishing mechanisms in Wagtail, inheriting from this mixin also requires inheriting from `RevisionMixin` and `DraftStateMixin`. It is also recommended to enable locking by inheriting from `LockableMixin`, so that the snippet instance can be locked and only editable by reviewers when it is in a workflow. See the above sections for more details.

The mixin defines a `workflow_states` property that gives you a queryset of all workflow states for the snippet instance. It also comes with a default {class}`~django.contrib.contenttypes.fields.GenericRelation` to the {class}`~wagtail.models.WorkflowState` model so that the workflow states are properly cleaned up when the snippet instance is deleted.

The default `GenericRelation` does not have a {attr}`~django.contrib.contenttypes.fields.GenericRelation.related_query_name`, so it does not give you the ability to query and filter from the `WorkflowState` model back to the snippet model. If you would like this feature, you can define your own `GenericRelation` with a custom `related_query_name`.

For more details, see the default `GenericRelation` {attr}`~wagtail.models.WorkflowMixin._workflow_states` and the property {attr}`~wagtail.models.WorkflowMixin.workflow_states`.

```{versionadded} 7.1
The default `GenericRelation` {attr}`~wagtail.models.WorkflowMixin._workflow_states` was added.
```

For example, workflows (with locking) can be enabled for the `Advert` snippet by defining it as follows:

```python
# ...
from wagtail.models import DraftStateMixin, LockableMixin, RevisionMixin, WorkflowMixin
# ...


class Advert(WorkflowMixin, DraftStateMixin, LockableMixin, RevisionMixin, models.Model):
    url = models.URLField(null=True, blank=True)
    text = models.CharField(max_length=255)
    _revisions = GenericRelation("wagtailcore.Revision", related_query_name="advert")
    workflow_states = GenericRelation(
        "wagtailcore.WorkflowState",
        content_type_field="base_content_type",
        object_id_field="object_id",
        related_query_name="advert",
        for_concrete_model=False,
    )

    panels = [
        FieldPanel('url'),
        FieldPanel('text'),
    ]

    @property
    def revisions(self):
        return self._revisions
```

The other mixins required by `WorkflowMixin` includes additional fields that need to be added to your database table. Make sure to run the `makemigrations` and `migrate` management commands after making the above changes to apply the changes to your database.

After enabling the mixin, you can assign a workflow to the snippet models through the workflow settings. For more information, see how to [configure workflows for moderation](https://guide.wagtail.org/en-latest/how-to-guides/configure-workflows-for-moderation/).

The admin dashboard and workflow reports will also show you snippets (alongside pages) that have been submitted to workflows.

## Tagging snippets

Adding tags to snippets is very similar to adding tags to pages. The only difference is that if `RevisionMixin` is not applied, then `taggit.manager.TaggableManager` should be used in the place of `modelcluster.contrib.taggit.ClusterTaggableManager`.

```python
# ...
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from taggit.models import TaggedItemBase
from taggit.managers import TaggableManager
# ...


class AdvertTag(TaggedItemBase):
    content_object = ParentalKey('demo.Advert', on_delete=models.CASCADE, related_name='tagged_items')


class Advert(ClusterableModel):
    # ...
    tags = TaggableManager(through=AdvertTag, blank=True)

    panels = [
        # ...
        FieldPanel('tags'),
    ]
```

The [documentation on tagging pages](tagging) has more information on how to use tags in views.

(wagtailsnippets_inline_models)=

## Inline models within snippets

Similar to pages, you can nest other models within a snippet. This requires the snippet model to inherit from `modelcluster.models.ClusterableModel` instead of `django.models.Model`.

```python
from django.db import models
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail.models import Orderable


class BandMember(Orderable):
    band = ParentalKey("music.Band", related_name="members", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)


@register_snippet
class Band(ClusterableModel):
    name = models.CharField(max_length=255)
    panels = [
        FieldPanel("name"),
        InlinePanel("members")
    ]
```

The [documentation on how to use inline models with pages](inline_models) provides more information that is also applicable to snippets.
