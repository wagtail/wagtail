from warnings import warn

from django.conf import settings
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.text import capfirst
from django.utils.translation import gettext as _

from wagtail.admin.utils import get_latest_str
from wagtail.utils.deprecation import RemovedInWagtail60Warning


class BaseLock:
    """
    Holds information about a lock on an object.

    Returned by LockableMixin.get_lock() (or Page.get_lock()).
    """

    def __init__(self, object):
        from wagtail.models import Page

        self.object = object
        self.is_page = isinstance(object, Page)

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
                if self.is_page:
                    return format_html(
                        # nosemgrep: translation-no-new-style-formatting (new-style only w/ format_html)
                        _(
                            "<b>Page '{page_title}' was locked</b> by <b>you</b> on <b>{datetime}</b>."
                        ),
                        page_title=title,
                        datetime=self.object.locked_at.strftime("%d %b %Y %H:%M"),
                    )
                else:
                    return format_html(
                        # nosemgrep: translation-no-new-style-formatting (new-style only w/ format_html)
                        _(
                            "<b>'{title}' was locked</b> by <b>you</b> on <b>{datetime}</b>."
                        ),
                        title=title,
                        datetime=self.object.locked_at.strftime("%d %b %Y %H:%M"),
                    )

            else:
                if self.is_page:
                    return format_html(
                        # nosemgrep: translation-no-new-style-formatting (new-style only w/ format_html)
                        _("<b>Page '{page_title}' is locked</b> by <b>you</b>."),
                        page_title=title,
                    )
                else:
                    return format_html(
                        # nosemgrep: translation-no-new-style-formatting (new-style only w/ format_html)
                        _("<b>'{title}' is locked</b> by <b>you</b>."),
                        title=title,
                    )
        else:
            if self.object.locked_by and self.object.locked_at:
                if self.is_page:
                    return format_html(
                        # nosemgrep: translation-no-new-style-formatting (new-style only w/ format_html)
                        _(
                            "<b>Page '{page_title}' was locked</b> by <b>{user}</b> on <b>{datetime}</b>."
                        ),
                        page_title=title,
                        user=str(self.object.locked_by),
                        datetime=self.object.locked_at.strftime("%d %b %Y %H:%M"),
                    )
                else:
                    return format_html(
                        # nosemgrep: translation-no-new-style-formatting (new-style only w/ format_html)
                        _(
                            "<b>'{title}' was locked</b> by <b>{user}</b> on <b>{datetime}</b>."
                        ),
                        title=title,
                        user=str(self.object.locked_by),
                        datetime=self.object.locked_at.strftime("%d %b %Y %H:%M"),
                    )
            else:
                # Page was probably locked with an old version of Wagtail, or a script
                if self.is_page:
                    return format_html(
                        # nosemgrep: translation-no-new-style-formatting (new-style only w/ format_html)
                        _("<b>Page '{page_title}' is locked</b>."),
                        page_title=title,
                    )
                else:
                    return format_html(
                        # nosemgrep: translation-no-new-style-formatting (new-style only w/ format_html)
                        _("<b>'{title}' is locked</b>."),
                        title=title,
                    )


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
                if self.is_page:
                    workflow_info = _("This page is currently awaiting moderation.")
                else:
                    workflow_info = capfirst(
                        _("This %(model_name)s is currently awaiting moderation.")
                        % {"model_name": self.object._meta.verbose_name}
                    )
            else:
                if self.is_page:
                    workflow_info = format_html(
                        # nosemgrep: translation-no-new-style-formatting (new-style only w/ format_html)
                        _(
                            "This page is awaiting <b>'{task_name}'</b> in the <b>'{workflow_name}'</b> workflow."
                        ),
                        task_name=self.task.name,
                        workflow_name=current_workflow_state.workflow.name,
                    )
                else:
                    workflow_info = format_html(
                        # nosemgrep: translation-no-new-style-formatting (new-style only w/ format_html)
                        _(
                            "This {model_name} is awaiting <b>'{task_name}'</b> in the <b>'{workflow_name}'</b> workflow."
                        ),
                        model_name=self.object._meta.verbose_name,
                        task_name=self.task.name,
                        workflow_name=current_workflow_state.workflow.name,
                    )
                    # Make sure message is correctly capitalised even if it
                    # starts with model_name.
                    workflow_info = mark_safe(capfirst(workflow_info))

            if self.is_page:
                reviewers_info = _("Only reviewers for this task can edit the page.")
            else:
                reviewers_info = capfirst(
                    _("Only reviewers for this task can edit the %(model_name)s.")
                    % {"model_name": self.object._meta.verbose_name}
                )

            return mark_safe(workflow_info + " " + reviewers_info)


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

        if self.is_page:
            return format_html(
                # nosemgrep: translation-no-new-style-formatting (new-style only w/ format_html)
                _(
                    "Page '{page_title}' is locked and has been scheduled to go live at {datetime}"
                ),
                page_title=self.object.get_admin_display_title(),
                datetime=scheduled_revision.approved_go_live_at.strftime(
                    "%d %b %Y %H:%M"
                ),
            )
        else:
            message = format_html(
                # nosemgrep: translation-no-new-style-formatting (new-style only w/ format_html)
                _(
                    "{model_name} '{title}' is locked and has been scheduled to go live at {datetime}"
                ),
                model_name=self.object._meta.verbose_name,
                title=scheduled_revision.object_str,
                datetime=scheduled_revision.approved_go_live_at.strftime(
                    "%d %b %Y %H:%M"
                ),
            )
            return mark_safe(capfirst(message))
