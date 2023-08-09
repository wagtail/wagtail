import logging

from django.core.exceptions import PermissionDenied

from wagtail.log_actions import log
from wagtail.signals import unpublished

logger = logging.getLogger("wagtail")


class UnpublishPermissionError(PermissionDenied):
    """
    Raised when the object unpublish cannot be performed due to insufficient permissions.
    """

    pass


class UnpublishAction:
    def __init__(
        self,
        object,
        set_expired=False,
        commit=True,
        user=None,
        log_action=True,
    ):
        self.object = object
        self.set_expired = set_expired
        self.commit = commit
        self.user = user
        self.log_action = log_action

    def check(self, skip_permission_checks=False):
        if (
            self.user
            and not skip_permission_checks
            and not self.object.permissions_for_user(self.user).can_unpublish()
        ):
            raise UnpublishPermissionError(
                "You do not have permission to unpublish this object"
            )

    def _commit_unpublish(self, object):
        object.save()

    def _after_unpublish(self, object):
        unpublished.send(sender=type(object), instance=object)

    def _unpublish_object(self, object, set_expired, commit, user, log_action):
        """
        Unpublish the object by setting ``live`` to ``False``. Does nothing if ``live`` is already ``False``
        :param log_action: flag for logging the action. Pass False to skip logging. Can be passed an action string.
            Defaults to 'wagtail.unpublish'
        """
        if object.live:
            object.live = False
            object.has_unpublished_changes = True
            object.live_revision = None

            if set_expired:
                object.expired = True

            if commit:
                self._commit_unpublish(object)

            if log_action:
                log(
                    instance=object,
                    action=log_action
                    if isinstance(log_action, str)
                    else "wagtail.unpublish",
                    user=user,
                )

            logger.info('Unpublished: "%s" pk=%s', str(object), str(object.pk))

            object.revisions.update(approved_go_live_at=None)

            self._after_unpublish(object)

    def execute(self, skip_permission_checks=False):
        self.check(skip_permission_checks=skip_permission_checks)

        self._unpublish_object(
            self.object,
            set_expired=self.set_expired,
            commit=self.commit,
            user=self.user,
            log_action=self.log_action,
        )
