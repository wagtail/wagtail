from django.core.exceptions import PermissionDenied

from wagtail.actions.base import BaseAction
from wagtail.log_actions import log
from wagtail.utils.forms import FormValidationError

# Sentinel for "auto-detect the sort order field from the model", distinct from
# an explicit None which means "do not set a sort order".
UNSET = object()


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
    :param form: an optional bound, validated model form for the instance. When
        given, the action saves the instance through the form (preserving any
        custom form save logic and saving many-to-many data); otherwise it saves
        the instance directly.
    :param log_action: pass a string to override the default ``"wagtail.create"``
        log action code, or ``False``/``None`` to skip logging.
    :param publish: whether to publish the object. Only applies to models using
        ``DraftStateMixin``; the created revision is published, making the
        object live. When ``False`` (the default), the object is created as a
        draft.
    :param sort_order_field: the name of the field to use for ordering. If not
        given, it is read from the model's ``sort_order_field`` attribute (e.g.
        from the ``Orderable`` mixin). Pass ``None`` explicitly to disable
        setting a sort order.
    :param clean: whether to validate the instance when creating its revision.
        By default the revision is validated unless saving a draft of a
        draft-enabled object. Pass an explicit value to override this, e.g. when
        publishing happens in a separate later step.
    """

    action_name = "create"
    permission_policy_action = "add"
    permission_error_class = CreatePermissionError

    def __init__(
        self,
        instance,
        user=None,
        *,
        form=None,
        log_action="wagtail.create",
        publish=False,
        sort_order_field=UNSET,
        clean=None,
    ):
        from wagtail.models import DraftStateMixin, RevisionMixin

        super().__init__(instance, user=user)
        self.form = form
        self.log_action = log_action
        self.publish = publish
        self.sort_order_field = sort_order_field
        self.revision_enabled = isinstance(instance, RevisionMixin)
        self.draftstate_enabled = isinstance(instance, DraftStateMixin)
        # Validate the revision unless we're saving a draft of a draft-enabled
        # object (where incomplete content is allowed).
        if clean is None:
            clean = self.publish or not self.draftstate_enabled
        self.clean = clean
        # The revision created by execute(), if any.
        self.revision = None

    def user_has_permission(self):
        # "add" is a model-level permission: there is no existing instance to
        # check against.
        return self.permission_policy.user_has_permission(
            self.user, self.permission_policy_action
        )

    def _clean_instance(self):
        if self.form:
            if not self.form.is_valid():
                raise FormValidationError.from_form(self.form)
        else:
            self.instance.full_clean()

    def _save_instance(self):
        # If DraftStateMixin is applied, make sure the object is not live when
        # first created. Making it live is done by publishing a revision below.
        if self.draftstate_enabled:
            self.instance.live = False

        if self.form:
            self.instance = self.form.save()
        else:
            self.instance.save()

    def _create(self, skip_permission_checks=False):
        from wagtail.models.orderable import set_max_order

        if self.clean:
            self._clean_instance()

        self._save_instance()

        # If the model declares a sort order field (e.g. via the Orderable
        # mixin) and no value was set, place the object last. An explicit
        # sort_order_field of None disables this.
        if self.sort_order_field is UNSET:
            sort_order_field = getattr(self.instance, "sort_order_field", None)
        else:
            sort_order_field = self.sort_order_field
        if sort_order_field and getattr(self.instance, sort_order_field) is None:
            set_max_order(self.instance, sort_order_field)

        if self.revision_enabled:
            self.revision = self.instance.save_revision(
                user=self.user,
                clean=self.clean,
                log_action=False,
            )

        if self.log_action:
            log(
                instance=self.instance,
                action=self.log_action,
                user=self.user,
                revision=self.revision,
                content_changed=True,
            )

        # Publish the new revision to make the object live. This emits its own
        # wagtail.publish log entry and the published signal, and runs its own
        # permission check (for the "publish" permission).
        if self.publish and self.draftstate_enabled:
            self.revision.publish(
                user=self.user,
                skip_permission_checks=skip_permission_checks,
            )

        return self.instance

    def execute(self, skip_permission_checks=False):
        self.check(skip_permission_checks=skip_permission_checks)
        return self._create(skip_permission_checks=skip_permission_checks)
