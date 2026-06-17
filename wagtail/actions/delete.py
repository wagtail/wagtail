from django.core.exceptions import PermissionDenied
from django.db import transaction

from wagtail.actions.base import BaseAction
from wagtail.log_actions import log


class DeletePermissionError(PermissionDenied):
    """
    Raised when deleting an object is not permitted.
    """

    pass


class DeleteAction(BaseAction):
    """
    Delete an object from the database and log a ``wagtail.delete`` action.

    :param instance: the object to delete.
    :param user: the user performing the action.
    :param log_action: pass a string to override the default ``"wagtail.delete"``
        log action code, or ``False``/``None`` to skip logging.
    """

    action_name = "delete"
    permission_policy_action = "delete"
    permission_error_class = DeletePermissionError

    def __init__(self, instance, user=None, *, log_action="wagtail.delete"):
        super().__init__(instance, user=user)
        self.log_action = log_action

    def _delete(self):
        with transaction.atomic():
            if self.log_action:
                # Log before deleting, while the object still exists.
                log(
                    instance=self.instance,
                    action=self.log_action,
                    user=self.user,
                    deleted=True,
                )
            return self.instance.delete()

    def execute(self, skip_permission_checks=False):
        self.check(skip_permission_checks=skip_permission_checks)
        return self._delete()
