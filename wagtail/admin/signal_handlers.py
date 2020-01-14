from wagtail.admin.mail import GroupApprovalTaskStateNotifier, WorkflowStateNotifier
from wagtail.core.models import TaskState, WorkflowState
from wagtail.core.signals import task_submitted, workflow_approved, workflow_rejected, workflow_submitted

group_approval_task_state_notifier = GroupApprovalTaskStateNotifier({'submitted'})
workflow_state_notifier = WorkflowStateNotifier({'submitted', 'approved', 'rejected'})


def register_signal_handlers():
    task_submitted.connect(group_approval_task_state_notifier.submitted, sender=TaskState, dispatch_uid='group_approval_task_submitted_email_notification')

    workflow_submitted.connect(workflow_state_notifier.submitted, sender=WorkflowState, dispatch_uid='workflow_state_submitted_email_notification')
    workflow_rejected.connect(workflow_state_notifier.rejected, sender=WorkflowState, dispatch_uid='workflow_state_rejected_email_notification')
    workflow_approved.connect(workflow_state_notifier.approved, sender=WorkflowState, dispatch_uid='workflow_state_approved_email_notification')
