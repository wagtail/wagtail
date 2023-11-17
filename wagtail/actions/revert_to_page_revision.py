from django.core.exceptions import PermissionDenied


class RevertToPageRevisionError(RuntimeError):
    """
    Raised when the revision revert cannot be performed for data reasons.
    """

    pass


class RevertToPageRevisionPermissionError(PermissionDenied):
    """
    Raised when the revision revert cannot be performed due to insufficient permissions.
    """

    pass


class RevertToPageRevisionAction:
    def __init__(
        self,
        page,
        revision,
        user=None,
        log_action="wagtail.revert",
        approved_go_live_at=None,
        changed=True,
        clean=True,
    ):
        self.page = page
        self.revision = revision
        self.user = user
        self.log_action = log_action
        self.approved_go_live_at = approved_go_live_at
        self.changed = changed
        self.clean = clean

    def check(self, skip_permission_checks=False):
        if self.page.alias_of_id:
            raise RevertToPageRevisionError(
                "Revisions are not required for alias pages as they are an exact copy of another page."
            )

        # Permission checks
        if (
            self.user
            and not skip_permission_checks
            and not self.page.permissions_for_user(self.user).can_edit()
        ):
            raise RevertToPageRevisionPermissionError(
                "You do not have permission to edit this page"
            )

    def execute(self, skip_permission_checks=False):
        self.check(skip_permission_checks=skip_permission_checks)

        return self.revision.as_object().save_revision(
            previous_revision=self.revision,
            user=self.user,
            log_action=self.log_action,
            approved_go_live_at=self.approved_go_live_at,
            changed=self.changed,
            clean=self.clean,
        )
