# Adding new Task types

The Workflow system allows users to create tasks, which represent stages of moderation.

Wagtail provides one built-in task type: `GroupApprovalTask`, which allows any user in specific groups to approve or reject moderation.

However, it is possible to implement your own task types. Instances of your custom task can then be created in the `Tasks` section of the Wagtail Admin.

## Task models

All custom tasks must be models inheriting from `wagtailcore.Task`. In this set of examples, we'll set up a task that can be approved by only one specific user.

```python
# <project>/models.py

from wagtail.models import Task


class UserApprovalTask(Task):
    pass
```

Subclassed Tasks follow the same approach as Pages: they are concrete models, with the specific subclass instance accessible by calling `Task.specific()`.

You can now add any custom fields. To make these editable in the admin, add the names of the fields into the `admin_form_fields` attribute:

For example:

```python
# <project>/models.py

from django.conf import settings
from django.db import models
from wagtail.models import Task


class UserApprovalTask(Task):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=False)

    admin_form_fields = Task.admin_form_fields + ['user']
```

Any fields that shouldn't be edited after task creation - for example, anything that would fundamentally change the meaning of the task in any history logs - can be added to `admin_form_readonly_on_edit_fields`. For example:

```python
# <project>/models.py

from django.conf import settings
from django.db import models
from wagtail.models import Task


class UserApprovalTask(Task):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=False)

    admin_form_fields = Task.admin_form_fields + ['user']

    # prevent editing of `user` after the task is created
    # by default, this attribute contains the 'name' field to prevent tasks from being renamed
    admin_form_readonly_on_edit_fields = Task.admin_form_readonly_on_edit_fields + ['user']
```

Wagtail will choose a default form widget to use based on the field type. But you can override the form widget using the `admin_form_widgets` attribute:

```python
# <project>/models.py

from django.conf import settings
from django.db import models
from wagtail.models import Task

from .widgets import CustomUserChooserWidget


class UserApprovalTask(Task):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=False)

    admin_form_fields = Task.admin_form_fields + ['user']

    admin_form_widgets = {
        'user': CustomUserChooserWidget,
    }
```

## Custom TaskState models

You might also need to store custom state information for the task: for example, a rating left by an approving user.
Normally, this is done on an instance of `TaskState`, which is created when a page starts the task. However, this can
also be subclassed equivalently to `Task`:

```python
# <project>/models.py

from wagtail.models import TaskState


class UserApprovalTaskState(TaskState):
    pass
```

Your custom task must then be instructed to generate an instance of your custom task state on start instead of a plain `TaskState` instance:

```python
# <project>/models.py

from django.conf import settings
from django.db import models
from wagtail.models import Task, TaskState


class UserApprovalTaskState(TaskState):
    pass


class UserApprovalTask(Task):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=False)

    admin_form_fields = Task.admin_form_fields + ['user']

    task_state_class = UserApprovalTaskState
```

## Customising behaviour

Both `Task` and `TaskState` have a number of methods that can be overridden to implement custom behaviour. Here are some of the most useful:

`Task.user_can_access_editor(page, user)`, `Task.user_can_lock(page, user)`, `Task.user_can_unlock(page, user)`:

These methods determine if users usually without permission can access the editor, and lock, or unlock the page, by returning True or False.
Note that returning `False` will not prevent users who would normally be able to perform those actions. For example, for our `UserApprovalTask`:

```python
def user_can_access_editor(self, page, user):
    return user == self.user
```

`Task.page_locked_for_user(page, user)`:

This returns `True` if the page should be locked and uneditable by the user. It is used by `GroupApprovalTask` to lock the page to any users not in the approval group.

```python
def page_locked_for_user(self, page, user):
    return user != self.user
```

`Task.get_actions(page, user)`:

This returns a list of `(action_name, action_verbose_name, action_requires_additional_data_from_modal)` tuples, corresponding to the actions available for the task in the edit view menu.
`action_requires_additional_data_from_modal` should be a boolean, returning `True` if choosing the action should open a modal for additional data input - for example, entering a comment.

For example:

```python
def get_actions(self, page, user):
    if user == self.user:
        return [
            ('approve', "Approve", False),
            ('reject', "Reject", False),
            ('cancel', "Cancel", False),
        ]
    else:
        return []
```

`Task.get_form_for_action(action)`:

Returns a form to be used for additional data input for the given action modal. By default, returns `TaskStateCommentForm`, with a single comment field. The form data returned in `form.cleaned_data` must be fully serializable as JSON.

`Task.get_template_for_action(action)`:

Returns the name of a custom template to be used in rendering the data entry modal for that action.

`Task.on_action(task_state, user, action_name, **kwargs)`:

This performs the actions specified in `Task.get_actions(page, user)`: it is passed an action name, for example, `approve`, and the relevant task state. By default, it calls `approve` and `reject` methods on the task state when the corresponding action names are passed through. Any additional data entered in a modal (see `get_form_for_action` and `get_actions`) is supplied as kwargs.

For example, let's say we wanted to add an additional option: cancelling the entire workflow:

```python
def on_action(self, task_state, user, action_name):
    if action_name == 'cancel':
        return task_state.workflow_state.cancel(user=user)
    else:
        return super().on_action(task_state, user, workflow_state)
```

`Task.get_task_states_user_can_moderate(user, **kwargs)`:

This returns a QuerySet of `TaskStates` (or subclasses) the given user can moderate - this is currently used to select pages to display on the user's dashboard.

For example:

```python
def get_task_states_user_can_moderate(self, user, **kwargs):
    if user == self.user:
        # get all task states linked to the (base class of) current task
        return TaskState.objects.filter(status=TaskState.STATUS_IN_PROGRESS, task=self.task_ptr)
    else:
        return TaskState.objects.none()
```

`Task.get_description()`

A class method that returns the human-readable description for the task.

For example:

```python
@classmethod
def get_description(cls):
    return _("Members of the chosen Wagtail Groups can approve this task")
```

## Adding notifications

Wagtail's notifications are sent by `wagtail.admin.mail.Notifier` subclasses: callables intended to be connected to a signal.

By default, email notifications are sent upon workflow submission, approval and rejection, and upon submission to a group approval task.

As an example, we'll add email notifications for when our new task is started.

```python
# <project>/mail.py

from wagtail.admin.mail import EmailNotificationMixin, Notifier
from wagtail.models import TaskState

from .models import UserApprovalTaskState


class BaseUserApprovalTaskStateEmailNotifier(EmailNotificationMixin, Notifier):
    """A base notifier to send updates for UserApprovalTask events"""

    def __init__(self):
        # Allow UserApprovalTaskState and TaskState to send notifications
        super().__init__((UserApprovalTaskState, TaskState))

    def can_handle(self, instance, **kwargs):
        if super().can_handle(instance, **kwargs) and isinstance(instance.task.specific, UserApprovalTask):
            # Don't send notifications if a Task has been cancelled and then resumed - when page was updated to a new revision
            return not TaskState.objects.filter(workflow_state=instance.workflow_state, task=instance.task, status=TaskState.STATUS_CANCELLED).exists()
        return False

    def get_context(self, task_state, **kwargs):
        context = super().get_context(task_state, **kwargs)
        context['page'] = task_state.workflow_state.page
        context['task'] = task_state.task.specific
        return context

    def get_recipient_users(self, task_state, **kwargs):

        # Send emails to the user assigned to the task
        approving_user = task_state.task.specific.user

        recipients = {approving_user}

        return recipients


class UserApprovalTaskStateSubmissionEmailNotifier(BaseUserApprovalTaskStateEmailNotifier):
    """A notifier to send updates for UserApprovalTask submission events"""

    notification = 'submitted'
```

Similarly, you could define notifier subclasses for approval and rejection notifications.

Next, you need to instantiate the notifier and connect it to the `task_submitted` signal.

```python
# <project>/signal_handlers.py

from wagtail.signals import task_submitted
from .mail import UserApprovalTaskStateSubmissionEmailNotifier


task_submission_email_notifier = UserApprovalTaskStateSubmissionEmailNotifier()

def register_signal_handlers():
    task_submitted.connect(user_approval_task_submission_email_notifier, dispatch_uid='user_approval_task_submitted_email_notification')
```

`register_signal_handlers()` should then be run on loading the app: for example, by adding it to the `ready()` method in your `AppConfig`.

```python
# <project>/apps.py
from django.apps import AppConfig


class MyAppConfig(AppConfig):
    name = 'myappname'
    label = 'myapplabel'
    verbose_name = 'My verbose app name'

    def ready(self):
        from .signal_handlers import register_signal_handlers
        register_signal_handlers()
```

```{note}
In Django versions before 3.2 your `AppConfig` subclass needs to be set as `default_app_config` in `<project>/__init__.py`.
See the [relevant section in the Django docs](https://docs.djangoproject.com/en/3.1/ref/applications/#for-application-authors) for the version you are using.
```
