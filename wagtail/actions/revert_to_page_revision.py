from wagtail.actions.revert_to_revision import (
    RevertToRevisionAction,
    RevertToRevisionPermissionError,
)


class RevertToPageRevisionError(RuntimeError):
    """
    Raised when the revision revert cannot be performed for data reasons.
    """

    pass


class RevertToPageRevisionPermissionError(RevertToRevisionPermissionError):
    """
    Raised when the revision revert cannot be performed due to insufficient permissions.
    """

    pass


class RevertToPageRevisionAction(RevertToRevisionAction):
    def check(self, skip_permission_checks=False):
        if self.instance.alias_of_id:
            raise RevertToPageRevisionError(
                "Revisions are not required for alias pages as they are an exact copy of another page."
            )

        # Permission checks
        if (
            self.user
            and not skip_permission_checks
            and not self.instance.permissions_for_user(self.user).can_edit()
        ):
            raise RevertToPageRevisionPermissionError(
                "You do not have permission to edit this page."
            )
