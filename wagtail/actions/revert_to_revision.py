from django.core.exceptions import PermissionDenied

from wagtail.actions.base import BaseAction


class RevertToRevisionPermissionError(PermissionDenied):
    """
    Raised when the revision revert cannot be performed due to insufficient permissions.
    """

    pass


class RevertToRevisionAction(BaseAction):
    action_name = "revert"
    permission_policy_action = "change"
    permission_error_class = RevertToRevisionPermissionError

    def __init__(
        self,
        instance,
        revision,
        user=None,
        log_action="wagtail.revert",
        approved_go_live_at=None,
        changed=True,
        clean=True,
    ):
        super().__init__(instance, user=user)
        self.revision = revision
        self.log_action = log_action
        self.approved_go_live_at = approved_go_live_at
        self.changed = changed
        self.clean = clean

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
