from warnings import warn

from django.conf import settings
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.text import capfirst
from django.utils.translation import gettext as _

from wagtail.admin.utils import get_latest_str, get_user_display_name
from wagtail.utils.deprecation import RemovedInWagtail60Warning
from wagtail.utils.timestamps import render_timestamp


class BaseLock:
    """
    Holds information about a lock on an object.

    Returned by LockableMixin.get_lock() (or Page.get_lock()).
    """

    def __init__(self, object):
        from wagtail.models import Page

        self.object = object
        self.is_page = isinstance(object, Page)
        # Use the base page's model name instead of the specific type for brevity
        self.model_name = (Page if self.is_page else object)._meta.verbose_name

    def for_user(self, user):
        """
        Returns True if the lock applies to the given user.
        """
        return NotImplemented

    def get_message(self, user):
        """
        Returns a message to display to the given user describing the lock.
        """
        return None

    def get_icon(self, user):
        """
        Returns the name of the icon to use for the lock.
        """
        return "lock"

    def get_locked_by(self, user):
        """
        Returns a string that represents the user or mechanism that locked the object.
        """
        return _("Locked")

    def get_description(self, user):
        """
        Returns a description of the lock to display to the given user.
        """
        return capfirst(
            _("No one can make changes while the %(model_name)s is locked")
            % {"model_name": self.model_name}
        )

    def get_context_for_user(self, user, parent_context=None):
        """
        Returns a context dictionary to use in templates for the given user.
        """
        return {
            "locked": self.for_user(user),
            "message": self.get_message(user),
            "icon": self.get_icon(user),
            "locked_by": self.get_locked_by(user),
            "description": self.get_description(user),
        }


class BasicLock(BaseLock):
    """
    A lock that is enabled when the "locked" attribute of an object is True.

    The object may be editable by a user depending on whether the locked_by field is set
    and if WAGTAILADMIN_GLOBAL_EDIT_LOCK is not set to True.
    """

    def for_user(self, user):
        global_edit_lock = getattr(settings, "WAGTAILADMIN_GLOBAL_EDIT_LOCK", None)
        if global_edit_lock is None and hasattr(
            settings, "WAGTAILADMIN_GLOBAL_PAGE_EDIT_LOCK"
        ):
            warn(
                "settings.WAGTAILADMIN_GLOBAL_PAGE_EDIT_LOCK has been renamed to "
                "settings.WAGTAILADMIN_GLOBAL_EDIT_LOCK",
                category=RemovedInWagtail60Warning,
            )
            global_edit_lock = settings.WAGTAILADMIN_GLOBAL_PAGE_EDIT_LOCK

        return global_edit_lock or user.pk != self.object.locked_by_id

    def get_message(self, user):
        title = get_latest_str(self.object)

        if self.object.locked_by_id == user.pk:
            if self.object.locked_at:
                return format_html(
                    # nosemgrep: translation-no-new-style-formatting (new-style only w/ format_html)
                    _(
                        "<b>'{title}' was locked</b> by <b>you</b> on <b>{datetime}</b>."
                    ),
                    title=title,
                    datetime=render_timestamp(self.object.locked_at),
                )

            else:
                return format_html(
                    # nosemgrep: translation-no-new-style-formatting (new-style only w/ format_html)
                    _("<b>'{title}' is locked</b> by <b>you</b>."),
                    title=title,
                )
        else:
            if self.object.locked_by and self.object.locked_at:
                return format_html(
                    # nosemgrep: translation-no-new-style-formatting (new-style only w/ format_html)
                    _(
                        "<b>'{title}' was locked</b> by <b>{user}</b> on <b>{datetime}</b>."
                    ),
                    title=title,
                    user=get_user_display_name(self.object.locked_by),
                    datetime=render_timestamp(self.object.locked_at),
                )
            else:
                # Object was probably locked with an old version of Wagtail, or a script
                return format_html(
                    # nosemgrep: translation-no-new-style-formatting (new-style only w/ format_html)
                    _("<b>'{title}' is locked</b>."),
                    title=title,
                )

    def get_locked_by(self, user):
        if self.object.locked_by_id == user.pk:
            return _("Locked by you")
        if self.object.locked_by_id:
            return _("Locked by another user")
        return super().get_locked_by(user)

    def get_description(self, user):
        if self.object.locked_by_id == user.pk:
            return capfirst(
                _("Only you can make changes while the %(model_name)s is locked")
                % {"model_name": self.model_name}
            )
        if self.object.locked_by_id:
            return capfirst(
                _("Only %(user)s can make changes while the %(model_name)s is locked")
                % {
                    "user": get_user_display_name(self.object.locked_by),
                    "model_name": self.model_name,
                }
            )
        return super().get_description(user)


class WorkflowLock(BaseLock):
    """
    A lock that requires the user to pass the Task.locked_for_user test on the given workflow task.
    """

    def __init__(self, object, task):
        super().__init__(object)
        self.task = task

    def for_user(self, user):
        return self.task.locked_for_user(self.object, user)

    def get_message(self, user):
        if self.for_user(user):
            current_workflow_state = self.object.current_workflow_state
            if (
                current_workflow_state
                and len(current_workflow_state.all_tasks_with_status()) == 1
            ):
                # If only one task in workflow, show simple message
                workflow_info = capfirst(
                    _("This %(model_name)s is currently awaiting moderation.")
                    % {"model_name": self.model_name}
                )
            else:
                workflow_info = format_html(
                    # nosemgrep: translation-no-new-style-formatting (new-style only w/ format_html)
                    _(
                        "This {model_name} is awaiting <b>'{task_name}'</b> in the <b>'{workflow_name}'</b> workflow."
                    ),
                    model_name=self.model_name,
                    task_name=self.task.name,
                    workflow_name=current_workflow_state.workflow.name,
                )
                # Make sure message is correctly capitalised even if it
                # starts with model_name.
                workflow_info = mark_safe(capfirst(workflow_info))

            reviewers_info = capfirst(
                _("Only reviewers for this task can edit the %(model_name)s.")
                % {"model_name": self.model_name}
            )

            return mark_safe(workflow_info + " " + reviewers_info)

    def get_icon(self, user, can_lock=False):
        if can_lock:
            return "lock-open"
        return super().get_icon(user)

    def get_locked_by(self, user, can_lock=False):
        if can_lock:
            return _("Unlocked")
        return _("Locked by workflow")

    def get_description(self, user, can_lock=False):
        if can_lock:
            return capfirst(
                _(
                    "Reviewers can edit this %(model_name)s – lock it to prevent other reviewers from editing"
                )
                % {"model_name": self.model_name}
            )
        return capfirst(
            _("Only reviewers can edit and approve the %(model_name)s")
            % {"model_name": self.model_name}
        )

    def get_context_for_user(self, user, parent_context=None):
        context = super().get_context_for_user(user, parent_context)
        # BasicLock can still be applied on top of WorkflowLock, so we need to
        # check if the user can lock the object based on the parent context.
        # We're utilising the parent context instead of self.task.user_can_lock()
        # because the latter does not take into account the user's permissions,
        # while the parent context does and also checks self.task.user_can_lock().
        if parent_context and "user_can_lock" in parent_context:
            can_lock = parent_context.get("user_can_lock", False)
            context.update(
                {
                    "icon": self.get_icon(user, can_lock),
                    "locked_by": self.get_locked_by(user, can_lock),
                    "description": self.get_description(user, can_lock),
                }
            )
        return context


class ScheduledForPublishLock(BaseLock):
    """
    A lock that occurs when something is scheduled to be published.

    This prevents it becoming difficult for users to see which version is going to be published.
    Nobody can edit something that's scheduled for publish.
    """

    def for_user(self, user):
        return True

    def get_message(self, user):
        scheduled_revision = self.object.scheduled_revision

        message = format_html(
            # nosemgrep: translation-no-new-style-formatting (new-style only w/ format_html)
            _(
                "{model_name} '{title}' is locked and has been scheduled to go live at {datetime}"
            ),
            model_name=self.model_name,
            title=scheduled_revision.object_str,
            datetime=render_timestamp(scheduled_revision.approved_go_live_at),
        )
        return mark_safe(capfirst(message))

    def get_locked_by(self, user):
        return _("Locked by schedule")

    def get_description(self, user):
        return _("Currently locked and will go live on the scheduled date")
