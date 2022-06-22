(audit_log)=

# Audit log

Wagtail provides a mechanism to log actions performed on its objects. Common activities such as page creation, update, deletion, locking and unlocking, revision scheduling and privacy changes are automatically logged at the model level.

The Wagtail admin uses the action log entries to provide a site-wide and page specific history of changes. It uses a
registry of 'actions' that provide additional context for the logged action.

The audit log-driven Page history replaces the revisions list page, but provide a filter for revision-specific entries.

```{note}
The audit log does not replace revisions.
```

The `wagtail.log_actions.log` function can be used to add logging to your own code.

```{eval-rst}
.. function:: log(instance, action, user=None, uuid=None, title=None, data=None)

   Adds an entry to the audit log.

   :param instance: The model instance that the action is performed on
   :param action: The code name for the action being performed. This can be one of the names listed below, or a custom action defined through the :ref:`register_log_actions` hook.
   :param user: Optional - the user initiating the action. For actions logged within an admin view, this defaults to the logged-in user.
   :param uuid: Optional - log entries given the same UUID indicates that they occurred as part of the same user action (e.g. a page being immediately published on creation).
   :param title: The string representation of the instance being logged. By default, Wagtail will attempt to use the instance's ``str`` representation, or ``get_admin_display_title`` for page objects.
   :param data: Optional - a dictionary of additional JSON-serialisable data to store against the log entry
```

```{note}
When adding logging, you need to log the action or actions that happen to the object. For example, if the user creates and publishes a page, there should be a "create" entry and a "publish" entry. Or, if the user copies a published page and chooses to keep it published, there should be a "copy" and a "publish" entry for new page.
```

```python

    # mypackage/views.py
    from wagtail.log_actions import log

    def copy_for_translation(page):
        # ...
        page.copy(log_action='mypackage.copy_for_translation')

    def my_method(request, page):
        # ..
        # Manually log an action
        data = {
            'make': {'it': 'so'}
        }
        log(
            instance=page, action='mypackage.custom_action', data=data
        )
```

```{versionchanged} 2.15
The `log` function was added. Previously, logging was only implemented for pages, and invoked through the `PageLogEntry.objects.log_action` method.
```

## Log actions provided by Wagtail

| Action                            | Notes                                                                            |
| --------------------------------- | -------------------------------------------------------------------------------- |
| `wagtail.create`                  | The object was created                                                           |
| `wagtail.edit`                    | The object was edited (for pages, saved as draft)                                |
| `wagtail.delete`                  | The object was deleted. Will only surface in the Site History for administrators |
| `wagtail.publish`                 | The page was published                                                           |
| `wagtail.publish.schedule`        | Draft is scheduled for publishing                                                |
| `wagtail.publish.scheduled`       | Draft published via `publish_scheduled_pages` management command                 |
| `wagtail.schedule.cancel`         | Draft scheduled for publishing cancelled via "Cancel scheduled publish"          |
| `wagtail.unpublish`               | The page was unpublished                                                         |
| `wagtail.unpublish.scheduled`     | Page unpublished via `publish_scheduled_pages` management command                |
| `wagtail.lock`                    | Page was locked                                                                  |
| `wagtail.unlock`                  | Page was unlocked                                                                |
| `wagtail.moderation.approve`      | The revision was approved for moderation                                         |
| `wagtail.moderation.reject`       | The revision was rejected                                                        |
| `wagtail.rename`                  | A page was renamed                                                               |
| `wagtail.revert`                  | The page was reverted to a previous draft                                        |
| `wagtail.copy`                    | The page was copied to a new location                                            |
| `wagtail.copy_for_translation`    | The page was copied into a new locale for translation                            |
| `wagtail.move`                    | The page was moved to a new location                                             |
| `wagtail.reorder`                 | The order of the page under it's parent was changed                              |
| `wagtail.view_restriction.create` | The page was restricted                                                          |
| `wagtail.view_restriction.edit`   | The page restrictions were updated                                               |
| `wagtail.view_restriction.delete` | The page restrictions were removed                                               |
| `wagtail.workflow.start`          | The page was submitted for moderation in a Workflow                              |
| `wagtail.workflow.approve`        | The draft was approved at a Workflow Task                                        |
| `wagtail.workflow.reject`         | The draft was rejected, and changes requested at a Workflow Task                 |
| `wagtail.workflow.resume`         | The draft was resubmitted to the workflow                                        |
| `wagtail.workflow.cancel`         | The workflow was cancelled                                                       |

## Log context

The `wagtail.log_actions` module provides a context manager to simplify code that logs a large number of actions,
such as import scripts:

```python
from wagtail.log_actions import LogContext

with LogContext(user=User.objects.get(username='admin')):
    # ...
    log(page, 'wagtail.edit')
    # ...
    log(page, 'wagtail.publish')
```

All `log` calls within the block will then be attributed to the specified user, and assigned a common UUID. A log context is created automatically for views within the Wagtail admin.

## Log models

Logs are stored in the database via the models `wagtail.models.PageLogEntry` (for actions on Page instances) and
`wagtail.models.ModelLogEntry` (for actions on all other models). Page logs are stored in their own model to
ensure that reports can be filtered according to the current user's permissions, which could not be done efficiently
with a generic foreign key.

If your own models have complex reporting requirements that would make `ModelLogEntry` unsuitable, you can configure
them to be logged to their own log model; this is done by subclassing the abstract `wagtail.models.BaseLogEntry`
model, and registering that model with the log registry's `register_model` method:

```python
from myapp.models import Sprocket, SprocketLogEntry
# here SprocketLogEntry is a subclass of BaseLogEntry

@hooks.register('register_log_actions')
def sprocket_log_model(actions):
    actions.register_model(Sprocket, SprocketLogEntry)
```
