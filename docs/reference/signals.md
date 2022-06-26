# Signals

Wagtail's [](revision_model_ref) and [](page_model_ref) implement [Signals](django:topics/signals) from `django.dispatch`.
Signals are useful for creating side-effects from page publish/unpublish events.

For example, you could use signals to send publish notifications to a messaging service, or `POST` messages to another app that's consuming the API, such as a static site generator.

## `page_published`

This signal is emitted from a `Revision` when a page revision is set to `published`.

-   `sender` - The page `class`.
-   `instance` - The specific `Page` instance.
-   `revision` - The `Revision` that was published.
-   `kwargs` - Any other arguments passed to `page_published.send()`.

To listen to a signal, implement `page_published.connect(receiver, sender, **kwargs)`. Here's a simple
example showing how you might notify your team when something is published:

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
to handle signals for specific models in different ways. For instance, you may
wish to do something when a new blog post is published:

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

Read the [Django documentation](django:topics/signals) for more information about specifying senders.

## `page_unpublished`

This signal is emitted from a `Page` when the page is unpublished.

-   `sender` - The page `class`.
-   `instance` - The specific `Page` instance.
-   `kwargs` - Any other arguments passed to `page_unpublished.send()`

## `pre_page_move` and `post_page_move`

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

### Distinguishing between a 'move' and a 'reorder'

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

## `page_slug_changed`

This signal is emitted from a `Page` when a change to its slug is published.

The following arguments are emitted by this signal:

-   `sender` - The page `class`.
-   `instance` - The updated (and saved), specific `Page` instance.
-   `instance_before` - A copy of the specific `Page` instance from **before** the changes were saved.

## workflow_submitted

This signal is emitted from a `WorkflowState` when a page is submitted to a workflow.

-   `sender` - `WorkflowState`
-   `instance` - The specific `WorkflowState` instance.
-   `user` - The user who submitted the workflow
-   `kwargs` - Any other arguments passed to `workflow_submitted.send()`

## workflow_rejected

This signal is emitted from a `WorkflowState` when a page is rejected from a workflow.

-   `sender` - `WorkflowState`
-   `instance` - The specific `WorkflowState` instance.
-   `user` - The user who rejected the workflow
-   `kwargs` - Any other arguments passed to `workflow_rejected.send()`

## workflow_approved

This signal is emitted from a `WorkflowState` when a page's workflow completes successfully

-   `sender` - `WorkflowState`
-   `instance` - The specific `WorkflowState` instance.
-   `user` - The user who last approved the workflow
-   `kwargs` - Any other arguments passed to `workflow_approved.send()`

## workflow_cancelled

This signal is emitted from a `WorkflowState` when a page's workflow is cancelled

-   `sender` - `WorkflowState`
-   `instance` - The specific `WorkflowState` instance.
-   `user` - The user who cancelled the workflow
-   `kwargs` - Any other arguments passed to `workflow_cancelled.send()`

## task_submitted

This signal is emitted from a `TaskState` when a page is submitted to a task.

-   `sender` - `TaskState`
-   `instance` - The specific `TaskState` instance.
-   `user` - The user who submitted the page to the task
-   `kwargs` - Any other arguments passed to `task_submitted.send()`

## task_rejected

This signal is emitted from a `TaskState` when a page is rejected from a task.

-   `sender` - `TaskState`
-   `instance` - The specific `TaskState` instance.
-   `user` - The user who rejected the task
-   `kwargs` - Any other arguments passed to `task_rejected.send()`

## task_approved

This signal is emitted from a `TaskState` when a page's task is approved

-   `sender` - `TaskState`
-   `instance` - The specific `TaskState` instance.
-   `user` - The user who approved the task
-   `kwargs` - Any other arguments passed to `task_approved.send()`

## task_cancelled

This signal is emitted from a `TaskState` when a page's task is cancelled.

-   `sender` - `TaskState`
-   `instance` - The specific `TaskState` instance.
-   `user` - The user who cancelled the task
-   `kwargs` - Any other arguments passed to `task_cancelled.send()`
