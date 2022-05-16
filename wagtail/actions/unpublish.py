import logging

from django.core.exceptions import PermissionDenied

from wagtail.log_actions import log
from wagtail.signals import object_unpublished

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
        include_descendants=False,
    ):
        self.object = object
        self.set_expired = set_expired
        self.commit = commit
        self.user = user
        self.log_action = log_action
        self.include_descendants = include_descendants

    def check(self, skip_permission_checks=False):
        if (
            self.user
            and not skip_permission_checks
            and not self.object.permissions_for_user(self.user).can_unpublish()
        ):
            raise UnpublishPermissionError(
                "You do not have permission to unpublish this object"
            )

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
                # using clean=False to bypass validation
                object.save(clean=False)

            object_unpublished.send(
                sender=object.specific_class, instance=object.specific
            )

            if log_action:
                log(
                    instance=object,
                    action=log_action
                    if isinstance(log_action, str)
                    else "wagtail.unpublish",
                    user=user,
                )

            logger.info('Object unpublished: "%s" id=%d', str(object), object.id)

            object.revisions.update(approved_go_live_at=None)

            # Unpublish aliases
            for alias in object.aliases.all():
                alias.unpublish()

    def execute(self, skip_permission_checks=False):
        self.check(skip_permission_checks=skip_permission_checks)

        self._unpublish_object(
            self.object,
            set_expired=self.set_expired,
            commit=self.commit,
            user=self.user,
            log_action=self.log_action,
        )

        if self.include_descendants:
            from wagtail.models import UserPagePermissionsProxy

            user_perms = UserPagePermissionsProxy(self.user)
            for live_descendant_object in (
                self.object.get_descendants().live().defer_streamfields().specific()
            ):
                action = UnpublishAction(live_descendant_object)
                if user_perms.for_page(live_descendant_object).can_unpublish():
                    action.execute(skip_permission_checks=True)
