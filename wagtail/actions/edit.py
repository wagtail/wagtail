from django.core.exceptions import PermissionDenied

from wagtail.actions.base import BaseAction
from wagtail.log_actions import log


class EditPermissionError(PermissionDenied):
    """
    Raised when editing an object is not permitted.
    """

    pass


class EditAction(BaseAction):
    """
    Save changes to an existing object, creating a revision if the model is
    revisable, and log a ``wagtail.edit`` action.

    :param instance: the object to edit, with its changes already applied.
    :param user: the user performing the action.
    :param log_action: pass a string to override the default ``"wagtail.edit"``
        log action code, or ``False``/``None`` to skip logging.
    :param content_changed: whether the log entry should mark the content as
        changed.
    :param publish: whether to publish the object. Only applies to models using
        ``DraftStateMixin``; the new revision is published, making the object
        live. When ``False`` (the default), the changes are saved as a draft.
    :param previous_revision: when reverting, the revision being reverted to.
    :param overwrite_revision: when overwriting the latest revision instead of
        creating a new one, the revision to overwrite.
    """

    action_name = "edit"
    permission_policy_action = "change"
    permission_error_class = EditPermissionError

    def __init__(
        self,
        instance,
        user=None,
        *,
        log_action="wagtail.edit",
        content_changed=True,
        publish=False,
        previous_revision=None,
        overwrite_revision=None,
    ):
        super().__init__(instance, user=user)
        self.log_action = log_action
        self.content_changed = content_changed
        self.publish = publish
        self.previous_revision = previous_revision
        self.overwrite_revision = overwrite_revision

    def _edit(self, skip_permission_checks=False):
        from wagtail.models import DraftStateMixin, RevisionMixin

        revision_enabled = isinstance(self.instance, RevisionMixin)
        draftstate_enabled = isinstance(self.instance, DraftStateMixin)

        # Do not update the instance if it's a live DraftStateMixin object.
        # Edits will be saved as a revision, and the live object will be updated
        # when the revision is published.
        if not (draftstate_enabled and self.instance.live):
            self.instance.save()

        revision = None
        if revision_enabled:
            revision = self.instance.save_revision(
                user=self.user,
                changed=self.content_changed,
                clean=self.publish,
                previous_revision=self.previous_revision,
                overwrite_revision=self.overwrite_revision,
                log_action=False,
            )

        if self.log_action:
            log(
                instance=self.instance,
                action=self.log_action,
                user=self.user,
                revision=revision,
                content_changed=self.content_changed,
            )

        # Publish the new revision to make the object live. This emits its own
        # wagtail.publish log entry and the published signal, and runs its own
        # permission check (for the "publish" permission).
        if self.publish and draftstate_enabled:
            revision.publish(
                user=self.user,
                changed=self.content_changed,
                previous_revision=self.previous_revision,
                skip_permission_checks=skip_permission_checks,
            )

        return self.instance

    def execute(self, skip_permission_checks=False):
        self.check(skip_permission_checks=skip_permission_checks)
        return self._edit(skip_permission_checks=skip_permission_checks)
