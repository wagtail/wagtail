from django.core.exceptions import PermissionDenied

from wagtail.actions.base import BaseAction
from wagtail.actions.publish_page_revision import PublishPagePermissionError
from wagtail.actions.publish_revision import PublishPermissionError


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


def _is_locked_for_user(instance, user):
    from wagtail.models import LockableMixin

    return (
        isinstance(instance, LockableMixin)
        and (lock := instance.get_lock())
        and lock.for_user(user)
    )


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
        # Permission gate for the submit / resume transitions: edit access to
        # the instance, and no lock held against this user. The approve /
        # reject / cancel transitions and the page-specific subclasses define
        # their own permission logic.
        return can_edit_instance(self.instance, self.user) and not _is_locked_for_user(
            self.instance, self.user
        )

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
        if self.instance.get_workflow() is None:
            raise WorkflowStateError(
                "There is no active workflow assigned to this object."
            )
        if self.instance.current_workflow_state is not None:
            raise WorkflowStateError("A workflow is already active on this object.")

    def execute(self, skip_permission_checks=False):
        self.check(skip_permission_checks=skip_permission_checks)
        return _translate_state_errors(
            self.instance.get_workflow().start, _get_specific(self.instance), self.user
        )


class SubmitPageWorkflowAction(SubmitWorkflowAction):
    """Submit, with edit permissions based on the page permission tester."""

    def user_has_permission(self):
        return self.instance.permissions_for_user(self.user).can_edit() and not (
            _is_locked_for_user(self.instance, self.user)
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


class ResumePageWorkflowAction(ResumeWorkflowAction):
    """Resume, with edit permissions based on the page permission tester."""

    def user_has_permission(self):
        return self.instance.permissions_for_user(self.user).can_edit() and not (
            _is_locked_for_user(self.instance, self.user)
        )
