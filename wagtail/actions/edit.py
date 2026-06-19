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
    :param form: an optional bound, validated model form for the instance. When
        given, the action saves the instance through the form (preserving any
        custom form save logic and saving many-to-many data); otherwise it saves
        the instance directly.
    :param log_action: pass a string to override the default ``"wagtail.edit"``
        log action code, or ``False``/``None`` to skip logging.
    :param publish: whether to publish the object. Only applies to models using
        ``DraftStateMixin``; the new revision is published, making the object
        live. When ``False`` (the default), the changes are saved as a draft.
    :param previous_revision: when reverting, the revision being reverted to.
    :param overwrite_revision: when overwriting the latest revision instead of
        creating a new one, the revision to overwrite.
    :param clean: whether to validate the instance when creating its revision.
        By default the revision is validated unless saving a draft of a
        draft-enabled object. Pass an explicit value to override this, e.g. when
        publishing happens in a separate later step.
    """

    action_name = "edit"
    permission_policy_action = "change"
    permission_error_class = EditPermissionError

    def __init__(
        self,
        instance,
        user=None,
        *,
        form=None,
        log_action="wagtail.edit",
        publish=False,
        previous_revision=None,
        overwrite_revision=None,
        clean=None,
    ):
        from wagtail.models import DraftStateMixin, RevisionMixin

        super().__init__(instance, user=user)
        self.form = form
        self.log_action = log_action
        self.publish = publish
        self.previous_revision = previous_revision
        self.overwrite_revision = overwrite_revision
        self.revision_enabled = isinstance(instance, RevisionMixin)
        self.draftstate_enabled = isinstance(instance, DraftStateMixin)
        # Content is considered changed if the form reports changes; without a
        # form (e.g. a programmatic edit), assume the content has changed.
        self.content_changed = form.has_changed() if form is not None else True
        # Validate the revision unless we're saving a draft of a draft-enabled
        # object (where incomplete content is allowed).
        if clean is None:
            clean = self.publish or not self.draftstate_enabled
        self.clean = clean
        # The revision created by execute(), if any.
        self.revision = None

    def _save_instance(self):
        if self.draftstate_enabled and self.instance.live:
            # Do not update the instance if it's a live DraftStateMixin object.
            # Edits will be saved as a revision, and the live object will be updated
            # when the revision is published.
            if self.form:
                # Ensure any custom form.save() logic is run, but do not save
                # the instance to the database.
                self.instance = self.form.save(commit=False)
            # No form is given, leave the instance as-is.
        else:
            if self.form:
                self.instance = self.form.save()
            else:
                self.instance.save()

    def _edit(self, skip_permission_checks=False):
        self._save_instance()

        if self.revision_enabled:
            self.revision = self.instance.save_revision(
                user=self.user,
                changed=self.content_changed,
                clean=self.clean,
                previous_revision=self.previous_revision,
                overwrite_revision=self.overwrite_revision,
                log_action=False,
            )

        if self.log_action:
            log(
                instance=self.instance,
                action=self.log_action,
                user=self.user,
                revision=self.revision,
                content_changed=self.content_changed,
            )

        # Publish the new revision to make the object live. This emits its own
        # wagtail.publish log entry and the published signal, and runs its own
        # permission check (for the "publish" permission).
        if self.publish and self.draftstate_enabled:
            self.revision.publish(
                user=self.user,
                changed=self.content_changed,
                previous_revision=self.previous_revision,
                skip_permission_checks=skip_permission_checks,
            )

        return self.instance

    def execute(self, skip_permission_checks=False):
        self.check(skip_permission_checks=skip_permission_checks)
        return self._edit(skip_permission_checks=skip_permission_checks)
