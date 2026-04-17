# Signals

Wagtail implements [Signals](inv:django#topics/signals) from `django.dispatch` when managing models such as [`Revision`](revision_model_ref), [`Page`](page_model_ref), and [snippets](snippets).
Signals are useful for creating side-effects from Wagtail events such as publishing, unpublishing, and workflow progress.

For example, you could use signals to send publish notifications to a messaging service, or `POST` messages to another app that's consuming the API, such as a static site generator.

## Using Wagtail's signals

To listen to a signal, register a signal receiver using the [`Signal.connect()`](django.dispatch.Signal.connect) method. Here's an
example showing how you might use the [`page_published`](signal_page_published) signal to notify your team when a page is published:

```python
from wagtail.signals import page_published
import requests


# Let everyone know when a new page is published
def send_to_slack(sender, **kwargs):
    instance = kwargs['instance']
    url = 'https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX'
    values = {
        "text" : "%s was published by %s " % (instance.title, instance.owner.username),
        "channel": "#publish-notifications",
        "username": "the squid of content",
        "icon_emoji": ":octopus:"
    }

    response = requests.post(url, values)

# Register a receiver
page_published.connect(send_to_slack)
```

### Receiving specific model events

Sometimes you're not interested in receiving signals for every model, or you want
to handle signals for specific models in different ways. You can specify the
`sender` argument when connecting to a signal to only receive signals from a
specific model. For instance, you may wish to do something when a new blog post
is published:

```python
from wagtail.signals import page_published
from mysite.models import BlogPostPage

# Do something clever for each model type
def receiver(sender, **kwargs):
    # Do something with blog posts
    pass

# Register listeners for each page model class
page_published.connect(receiver, sender=BlogPostPage)
```

Wagtail provides access to a list of registered page types through the `get_page_models()` function in `wagtail.models`.

Read the [Django documentation](inv:django#connecting-to-specific-signals) for more information about specifying senders.

## Publishing signals

(signal_published)=

### `published`

This signal is emitted from a `Revision` when a revision of any model (including pages) is published.

-   `sender` - The model `class` of the published object.
-   `instance` - The specific `model` instance that was published.
-   `revision` - The `Revision` that was published.
-   `kwargs` - Any other arguments passed to `published.send().`

(signal_page_published)=

### `page_published`

This signal is emitted from a `Revision` when a page revision is published, similar to [`published`](signal_published).
It is useful if you want to receive signals only for page publishing events, without having to specify the sender for each page model class.

-   `sender` - The page `class`.
-   `instance` - The specific `Page` instance.
-   `revision` - The `Revision` that was published.
-   `kwargs` - Any other arguments passed to `page_published.send()`.

(signal_unpublished)=

### `unpublished`

This signal is emitted when any model instance (including pages) is unpublished.

-   `sender` - The model `class` of the unpublished object.
-   `instance` - The specific `model` instance that was unpublished.
-   `kwargs` - Any other arguments passed to `unpublished.send()`.

(signal_page_unpublished)=

### `page_unpublished`

This signal is emitted from a `Page` when the page is unpublished, similar to [`unpublished`](signal_unpublished).
It is useful if you want to receive signals only for page unpublishing events, without having to specify the sender for each page model class.

-   `sender` - The page `class`.
-   `instance` - The specific `Page` instance.
-   `kwargs` - Any other arguments passed to `page_unpublished.send()`

## Page operation signals

### `pre_page_move` and `post_page_move`

These signals are emitted from a `Page` immediately before and after it is moved.

Subscribe to `pre_page_move` if you need to know values BEFORE any database changes are applied. For example: Getting the page's previous URL, or that of its descendants.

Subscribe to `post_page_move` if you need to know values AFTER database changes have been applied. For example: Getting the page's new URL, or that of its descendants.

The following arguments are emitted for both signals:

-   `sender` - The page `class`.
-   `instance` - The specific `Page` instance.
-   `parent_page_before` - The parent page of `instance` **before** moving.
-   `parent_page_after` - The parent page of `instance` **after** moving.
-   `url_path_before` - The value of `instance.url_path` **before** moving.
-   `url_path_after` - The value of `instance.url_path` **after** moving.
-   `kwargs` - Any other arguments passed to `pre_page_move.send()` or `post_page_move.send()`.

#### Distinguishing between a 'move' and a 'reorder'

The signal can be emitted as a result of a page being moved to a different section (a 'move'), or as a result of a page being moved to a different position within the same section (a 'reorder'). Knowing the difference between the two can be particularly useful, because only a 'move' affects a page's URL (and that of its descendants), whereas a 'reorder' only affects the natural page order; which is probably less impactful.

The best way to distinguish between a 'move' and 'reorder' is to compare the `url_path_before` and `url_path_after` values. For example:

```python
from wagtail.signals import pre_page_move
from wagtail.contrib.frontend_cache.utils import purge_page_from_cache

# Clear a page's old URLs from the cache when it moves to a different section
def clear_page_url_from_cache_on_move(sender, **kwargs):

    if kwargs['url_path_before'] == kwargs['url_path_after']:
        # No URLs are changing :) nothing to do here!
        return

    # The page is moving to a new section (possibly even a new site)
    # so clear old URL(s) from the cache
    purge_page_from_cache(kwargs['instance'])

# Register a receiver
pre_page_move.connect(clear_old_page_urls_from_cache)
```

(page_slug_changed)=

### `page_slug_changed`

This signal is emitted from a `Page` when a change to its slug is published.

The following arguments are emitted by this signal:

-   `sender` - The page `class`.
-   `instance` - The updated (and saved), specific `Page` instance.
-   `instance_before` - A copy of the specific `Page` instance from **before** the changes were saved.

(init_new_page_signal)=

### `init_new_page`

This signal is emitted from a `CreateView` when a new page is initialized in the admin interface. In other words, it's emitted when a user navigates to a form to create a new page.

It's useful for pre-populating the page form programmatically when default values are not sufficient.

-   `sender` - `CreateView`
-   `page` - The new page instance
-   `parent_page` - The parent page of the new page

Here's an example of how to use this signal to pre-populate a new page's title using the page's parent's title as a prefix:

```python
from wagtail.signals import init_new_page

def prepopulate_page(sender, page, parent, **kwargs):
    if parent:
        page.title = f"{parent.title}: New Page Title"

init_new_page.connect(prepopulate_page)
```

For more complex customizations of the page creation and editing forms, see [](custom_edit_handler_forms).


## Workflow signals

The following signals apply to pages and [snippets with workflows enabled](wagtailsnippets_enabling_workflows).

### `workflow_submitted`

This signal is emitted from a `WorkflowState` when a model is submitted to a workflow.

-   `sender` - `WorkflowState`
-   `instance` - The specific `WorkflowState` instance.
-   `user` - The user who submitted the workflow
-   `kwargs` - Any other arguments passed to `workflow_submitted.send()`

### `workflow_rejected`

This signal is emitted from a `WorkflowState` when a model is rejected from a workflow.

-   `sender` - `WorkflowState`
-   `instance` - The specific `WorkflowState` instance.
-   `user` - The user who rejected the workflow
-   `kwargs` - Any other arguments passed to `workflow_rejected.send()`

### `workflow_approved`

This signal is emitted from a `WorkflowState` when a model's workflow completes successfully.

-   `sender` - `WorkflowState`
-   `instance` - The specific `WorkflowState` instance.
-   `user` - The user who last approved the workflow
-   `kwargs` - Any other arguments passed to `workflow_approved.send()`

### `workflow_cancelled`

This signal is emitted from a `WorkflowState` when a model's workflow is cancelled.

-   `sender` - `WorkflowState`
-   `instance` - The specific `WorkflowState` instance.
-   `user` - The user who cancelled the workflow
-   `kwargs` - Any other arguments passed to `workflow_cancelled.send()`

### `task_submitted`

This signal is emitted from a `TaskState` when a model is submitted to a task.

-   `sender` - `TaskState`
-   `instance` - The specific `TaskState` instance.
-   `user` - The user who submitted the page to the task
-   `kwargs` - Any other arguments passed to `task_submitted.send()`

### `task_rejected`

This signal is emitted from a `TaskState` when a model is rejected from a task.

-   `sender` - `TaskState`
-   `instance` - The specific `TaskState` instance.
-   `user` - The user who rejected the task
-   `kwargs` - Any other arguments passed to `task_rejected.send()`

### `task_approved`

This signal is emitted from a `TaskState` when a model's task is approved

-   `sender` - `TaskState`
-   `instance` - The specific `TaskState` instance.
-   `user` - The user who approved the task
-   `kwargs` - Any other arguments passed to `task_approved.send()`

### `task_cancelled`

This signal is emitted from a `TaskState` when a model's task is cancelled.

-   `sender` - `TaskState`
-   `instance` - The specific `TaskState` instance.
-   `user` - The user who cancelled the task
-   `kwargs` - Any other arguments passed to `task_cancelled.send()`

## Translation signals

### `copy_for_translation_done`

This signal is emitted from `CopyForTranslationAction` or `CopyPageForTranslationAction` when a translatable model or page is copied to a new locale (translated).

A translatable model is a model that implements the [TranslatableMixin](wagtail.models.TranslatableMixin).

-   `sender` - `CopyForTranslationAction` or `CopyPageForTranslationAction`
-   `source_obj` - The source object
-   `target_obj` - The copy of the source object in the new locale
