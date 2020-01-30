from wagtail.admin.mail import GroupApprovalTaskStateSubmissionNotifier, WorkflowStateApprovalNotifier, WorkflowStateRejectionNotifier, WorkflowStateSubmissionNotifier
from wagtail.core.models import TaskState, WorkflowState
from wagtail.core.signals import task_submitted, workflow_approved, workflow_rejected, workflow_submitted


task_submission_notifier = GroupApprovalTaskStateSubmissionNotifier()
workflow_submission_notifier = WorkflowStateSubmissionNotifier()
workflow_approval_notifier = WorkflowStateApprovalNotifier()
workflow_rejection_notifier = WorkflowStateRejectionNotifier()


def register_signal_handlers():
    task_submitted.connect(task_submission_notifier, sender=TaskState, dispatch_uid='group_approval_task_submitted_email_notification')

    workflow_submitted.connect(workflow_submission_notifier, sender=WorkflowState, dispatch_uid='workflow_state_submitted_email_notification')
    workflow_rejected.connect(workflow_rejection_notifier, sender=WorkflowState, dispatch_uid='workflow_state_rejected_email_notification')
    workflow_approved.connect(workflow_approval_notifier, sender=WorkflowState, dispatch_uid='workflow_state_approved_email_notification')
