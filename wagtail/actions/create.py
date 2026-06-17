from django.core.exceptions import PermissionDenied

from wagtail.actions.base import BaseAction
from wagtail.log_actions import log


class CreatePermissionError(PermissionDenied):
    """
    Raised when creating an object is not permitted.
    """

    pass


class CreateAction(BaseAction):
    """
    Save a new object to the database, creating a revision if the model is
    revisable, and log a ``wagtail.create`` action.

    :param instance: the (unsaved) object to create.
    :param user: the user performing the action.
    :param log_action: pass a string to override the default ``"wagtail.create"``
        log action code, or ``False``/``None`` to skip logging.
    :param content_changed: whether the log entry should mark the content as
        changed.
    :param publish: whether to publish the object. Only applies to models using
        ``DraftStateMixin``; the created revision is published, making the
        object live. When ``False`` (the default), the object is created as a
        draft.
    """

    action_name = "create"
    permission_policy_action = "add"
    permission_error_class = CreatePermissionError

    def __init__(
        self,
        instance,
        user=None,
        *,
        log_action="wagtail.create",
        content_changed=True,
        publish=False,
    ):
        super().__init__(instance, user=user)
        self.log_action = log_action
        self.content_changed = content_changed
        self.publish = publish

    def user_has_permission(self):
        # "add" is a model-level permission: there is no existing instance to
        # check against.
        return self.permission_policy.user_has_permission(
            self.user, self.permission_policy_action
        )

    def _create(self, skip_permission_checks=False):
        from wagtail.models import DraftStateMixin, RevisionMixin
        from wagtail.models.orderable import set_max_order

        revision_enabled = isinstance(self.instance, RevisionMixin)
        draftstate_enabled = isinstance(self.instance, DraftStateMixin)

        # If DraftStateMixin is applied, make sure the object is not live when
        # first created. Making it live is done by publishing a revision below.
        if draftstate_enabled:
            self.instance.live = False

        self.instance.save()

        # If the model declares a sort order field (e.g. via the Orderable
        # mixin) and no value was set, place the object last.
        sort_order_field = getattr(self.instance, "sort_order_field", None)
        if sort_order_field and getattr(self.instance, sort_order_field) is None:
            set_max_order(self.instance, sort_order_field)

        revision = None
        if revision_enabled:
            revision = self.instance.save_revision(
                user=self.user,
                changed=self.content_changed,
                clean=self.publish,
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
                skip_permission_checks=skip_permission_checks,
            )

        return self.instance

    def execute(self, skip_permission_checks=False):
        self.check(skip_permission_checks=skip_permission_checks)
        return self._create(skip_permission_checks=skip_permission_checks)
