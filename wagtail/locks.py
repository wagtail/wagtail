from django.conf import settings
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _


class BaseLock:
    """
    Holds information about a lock on an object.

    Returned by LockableMixin.get_lock() (or Page.get_lock()).
    """

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
    A lock that is enabled when the "locked" attribute of a page is True.

    The object may be editable by a user depending on whether the locked_by field is set
    and if WAGTAILADMIN_GLOBAL_PAGE_EDIT_LOCK is not set to True.
    """

    def __init__(self, page):
        self.page = page

    def for_user(self, user):
        if getattr(settings, "WAGTAILADMIN_GLOBAL_PAGE_EDIT_LOCK", False):
            return True
        else:
            return user.pk != self.page.locked_by_id

    def get_message(self, user):
        if self.page.locked_by_id == user.pk:
            if self.page.locked_at:
                return format_html(
                    _("<b>Page '{}' was locked</b> by <b>you</b> on <b>{}</b>."),
                    self.page.get_admin_display_title(),
                    self.page.locked_at.strftime("%d %b %Y %H:%M"),
                )

            else:
                return format_html(
                    _("<b>Page '{}' is locked</b> by <b>you</b>."),
                    self.page.get_admin_display_title(),
                )
        else:
            if self.page.locked_by and self.page.locked_at:
                return format_html(
                    _("<b>Page '{}' was locked</b> by <b>{}</b> on <b>{}</b>."),
                    self.page.get_admin_display_title(),
                    str(self.page.locked_by),
                    self.page.locked_at.strftime("%d %b %Y %H:%M"),
                )
            else:
                # Page was probably locked with an old version of Wagtail, or a script
                return format_html(
                    _("<b>Page '{}' is locked</b>."),
                    self.page.get_admin_display_title(),
                )


class WorkflowLock(BaseLock):
    """
    A lock that requires the user to pass the Task.page_locked_for_user test on the given workflow task.

    Can be applied to pages only.
    """

    def __init__(self, task, page):
        self.task = task
        self.page = page

    def for_user(self, user):
        return self.task.page_locked_for_user(self.page, user)

    def get_message(self, user):
        if self.for_user(user):
            if len(self.page.current_workflow_state.all_tasks_with_status()) == 1:
                # If only one task in workflow, show simple message
                workflow_info = _("This page is currently awaiting moderation.")
            else:
                workflow_info = format_html(
                    _("This page is awaiting <b>'{}'</b> in the <b>'{}'</b> workflow."),
                    self.task.name,
                    self.page.current_workflow_state.workflow.name,
                )

            return mark_safe(
                workflow_info
                + " "
                + _("Only reviewers for this task can edit the page.")
            )


class ScheduledForPublishLock(BaseLock):
    """
    A lock that occurs when something is scheduled to be published.

    This prevents it becoming difficult for users to see which version of a page that is going to be published.
    Nobody can edit something that's scheduled for publish.
    """

    def __init__(self, page):
        self.page = page

    def for_user(self, user):
        return True

    def get_message(self, user):
        scheduled_revision = self.page.revisions.filter(
            approved_go_live_at__isnull=False
        ).first()

        return format_html(
            _("Page '{}' is locked and has been scheduled to go live at {}"),
            self.page.get_admin_display_title(),
            scheduled_revision.approved_go_live_at.strftime("%d %b %Y %H:%M"),
        )
