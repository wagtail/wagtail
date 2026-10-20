from django.core.exceptions import PermissionDenied
from django.db import transaction

from wagtail.actions.base import BaseAction
from wagtail.actions.publish_page_revision import PublishPagePermissionError
from wagtail.actions.publish_revision import PublishPermissionError
from wagtail.actions.registry import action_registry


class WorkflowStateError(Exception):
    """
    Raised when a workflow action cannot be performed because the object is
    not in the right workflow state.

    Unlike permission failures, state failures are not the user's fault: over
    the API they map onto a 422 response rather than a 403.
    """


def can_edit_instance(instance, user):
    """
    Return whether ``user`` can edit ``instance``.

    Pages use the page permission tester; all other models go through the
    permission policy registry.
    """
    from wagtail.models import AbstractPage

    if isinstance(instance, AbstractPage):
        return instance.permissions_for_user(user).can_edit()

    from wagtail.permissions import policy_registry

    return policy_registry.get(instance).user_has_permission_for_instance(
        user, "change", instance
    )


def _get_specific(instance):
    from wagtail.models import AbstractPage

    # Matches WorkflowState.resume's own handling of base Page instances.
    return instance.specific if isinstance(instance, AbstractPage) else instance


def _translate_state_errors(fn, *args, **kwargs):
    """Races can make the model methods raise PermissionDenied for state
    violations after check() passed; translate to WorkflowStateError (422) so
    a concurrent transition surfaces as invalid-state rather than
    forbidden. Publish-permission failures on final approval are genuine
    permission problems and stay 403 (the default workflow completion
    publishes the revision as the approver)."""
    try:
        return fn(*args, **kwargs)
    except (PublishPermissionError, PublishPagePermissionError):
        raise
    except PermissionDenied as e:
        raise WorkflowStateError(str(e)) from e


class WorkflowAction(BaseAction):
    """Base for workflow transition actions. check() performs both the
    permission checks (PermissionDenied -> 403) and the state validation
    (WorkflowStateError -> 422 over the API)."""

    def user_has_permission(self):
        # Permission gate for the submit / resume transitions. The approve /
        # reject / cancel transitions define their own permission logic.
        return can_edit_instance(self.instance, self.user)

    def check_lock(self):
        from wagtail.models import LockableMixin

        if (
            isinstance(self.instance, LockableMixin)
            and self.user
            and (lock := self.instance.get_lock()) is not None
            and lock.for_user(self.user)
        ):
            model_name = self.instance._meta.verbose_name
            raise PermissionDenied(f"The {model_name} is locked.")

    def check(self, skip_permission_checks=False):
        super().check(skip_permission_checks=skip_permission_checks)
        if not skip_permission_checks:
            self.check_lock()

    def can_execute(self) -> bool:
        try:
            self.check()
        except (PermissionDenied, WorkflowStateError):
            return False
        return True


class SubmitWorkflowAction(WorkflowAction):
    """
    Start the object's workflow on its latest revision, the same as
    submitting for moderation from the admin. Logs ``wagtail.workflow.start``.

    :param instance: the object to submit (a ``WorkflowMixin`` instance)
    :param user: the user submitting the object
    """

    action_name = "submit"

    def check(self, skip_permission_checks=False):
        super().check(skip_permission_checks=skip_permission_checks)
        from wagtail.models import AbstractPage

        if isinstance(self.instance, AbstractPage) and self.instance.alias_of_id:
            raise WorkflowStateError(
                "This page is an alias of another page and cannot be submitted for moderation."
            )
        if self.instance.get_workflow() is None:
            raise WorkflowStateError(
                "There is no active workflow assigned to this object."
            )
        if self.instance.current_workflow_state is not None:
            raise WorkflowStateError("A workflow is already active on this object.")

    @transaction.atomic
    def execute(self, skip_permission_checks=False):
        self.check(skip_permission_checks=skip_permission_checks)
        instance = _get_specific(self.instance)
        if instance.get_latest_revision() is None:
            instance.save_revision(user=self.user)
        return _translate_state_errors(
            self.instance.get_workflow().start, instance, self.user
        )


class ResumeWorkflowAction(WorkflowAction):
    """
    Put a workflow state in "needs changes" back into progress, the same as
    resuming from the admin. Logs ``wagtail.workflow.resume``.

    :param instance: the object whose workflow is to be resumed
    :param user: the user resuming the workflow
    """

    action_name = "resume"

    def check(self, skip_permission_checks=False):
        from wagtail.models import WorkflowState

        super().check(skip_permission_checks=skip_permission_checks)
        current_state = self.instance.current_workflow_state
        if (
            current_state is None
            or current_state.status != WorkflowState.STATUS_NEEDS_CHANGES
        ):
            raise WorkflowStateError(
                "The workflow on this object is not awaiting changes."
            )

    def execute(self, skip_permission_checks=False):
        self.check(skip_permission_checks=skip_permission_checks)
        state = self.instance.current_workflow_state
        # WorkflowState.resume() returns None (it delegates to update(), which
        # has no return value), so return the state directly.
        _translate_state_errors(state.resume, self.user)
        return state


class ApproveTaskStateAction(WorkflowAction):
    """
    Approve the object's current in-progress task state, the same as choosing
    "Approve" in the admin moderation UI. Logs ``wagtail.workflow.approve``.

    :param task_state: the in-progress task state to approve
    :param user: the user approving
    :param comment: an optional reviewer comment recorded on the task state
    """

    action_name = "approve"

    def __init__(self, task_state, user=None, comment=""):
        self.task_state = task_state.specific
        self.comment = comment
        self.object = _get_specific(self.task_state.workflow_state.content_object)
        super().__init__(task_state, user=user)

    def check(self, skip_permission_checks=False):
        from wagtail.models import TaskState, WorkflowState

        if self.user and not skip_permission_checks:
            actions = [
                name
                for name, verbose_name, modal in self.task_state.task.specific.get_actions(
                    self.object, self.user
                )
            ]
            if self.action_name not in actions:
                raise PermissionDenied(
                    "You do not have permission to perform this workflow action on this object."
                )
        if (
            self.task_state.workflow_state.status != WorkflowState.STATUS_IN_PROGRESS
            or self.task_state.status != TaskState.STATUS_IN_PROGRESS
        ):
            raise WorkflowStateError(
                "This object is not currently awaiting moderation."
            )

    def execute(self, skip_permission_checks=False):
        self.check(skip_permission_checks=skip_permission_checks)
        # Task.on_action() returns None (it calls task_state.approve/reject
        # without returning), so return the task state directly to honour
        # execute() -> TaskState.
        _translate_state_errors(
            self.task_state.task.specific.on_action,
            self.task_state,
            self.user,
            self.action_name,
            comment=self.comment,
        )
        return self.task_state


class RejectTaskStateAction(ApproveTaskStateAction):
    """
    Request changes on the object's current in-progress task state, the same as
    choosing "Request changes" in the admin moderation UI. Logs
    ``wagtail.workflow.reject``. Takes the same arguments as
    :class:`ApproveTaskStateAction`.
    """

    action_name = "reject"


class CancelWorkflowAction(WorkflowAction):
    """
    Cancel a workflow that is in progress or awaiting changes, the same as
    cancelling from the admin. Logs ``wagtail.workflow.cancel``.

    :param instance: the object whose workflow is to be cancelled
    :param user: the user cancelling the workflow
    """

    action_name = "cancel"

    def check(self, skip_permission_checks=False):
        state = self.instance.current_workflow_state
        if state is None:
            raise WorkflowStateError(
                "There is no active workflow on this object to cancel."
            )
        if (
            self.user
            and not skip_permission_checks
            and not state.user_can_cancel(self.user)
        ):
            raise PermissionDenied(
                "You do not have permission to cancel this workflow."
            )

    def execute(self, skip_permission_checks=False):
        self.check(skip_permission_checks=skip_permission_checks)
        state = self.instance.current_workflow_state
        # WorkflowState.cancel() returns None (like resume()), so return the
        # state directly.
        _translate_state_errors(state.cancel, self.user)
        return state


def get_available_workflow_transitions(instance, user=None) -> list[str]:
    """Return the names of the workflow transitions ``user`` may currently
    perform on ``instance``, in a fixed display order. Probes the registered
    action classes with ``can_execute()`` (non-raising), so what is advertised
    is exactly what ``execute()`` would accept."""
    available = set()
    for name in ("submit", "resume", "cancel"):
        action_class = action_registry.get_action_class(type(instance), name)
        if action_class is not None and action_class(instance, user=user).can_execute():
            available.add(name)
    task_state = instance.current_workflow_task_state
    if task_state is not None:
        for name in ("approve", "reject"):
            action_class = action_registry.get_action_class(type(instance), name)
            if (
                action_class is not None
                and action_class(task_state, user=user).can_execute()
            ):
                available.add(name)
    return [
        n for n in ("submit", "approve", "reject", "resume", "cancel") if n in available
    ]
