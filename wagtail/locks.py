from django.conf import settings


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
