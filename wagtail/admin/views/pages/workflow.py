from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _

from wagtail.admin import messages
from wagtail.admin.auth import user_has_any_page_permission, user_passes_test
from wagtail.admin.utils import get_latest_str
from wagtail.admin.views.generic import workflow
from wagtail.models import Page


class WorkflowPageViewMixin:
    model = Page
    pk_url_kwarg = "page_id"
    redirect_url_name = "wagtailadmin_pages:edit"

    def add_not_in_moderation_error(self):
        messages.error(
            self.request,
            _("The page '%(page_title)s' is not currently awaiting moderation.")
            % {
                "page_title": get_latest_str(self.object),
            },
        )

    def get_context_data(self, **kwargs):
        return super().get_context_data(page=self.object, **kwargs)


class WorkflowAction(WorkflowPageViewMixin, workflow.WorkflowAction):
    submit_url_name = "wagtailadmin_pages:workflow_action"


class CollectWorkflowActionData(
    WorkflowPageViewMixin, workflow.CollectWorkflowActionData
):
    submit_url_name = "wagtailadmin_pages:collect_workflow_action_data"


class ConfirmWorkflowCancellation(
    WorkflowPageViewMixin, workflow.ConfirmWorkflowCancellation
):
    template_name = "wagtailadmin/pages/confirm_workflow_cancellation.html"


@method_decorator(user_passes_test(user_has_any_page_permission), name="dispatch")
class WorkflowStatus(WorkflowPageViewMixin, workflow.WorkflowStatus):
    workflow_history_url_name = "wagtailadmin_pages:workflow_history"
    revisions_compare_url_name = "wagtailadmin_pages:revisions_compare"


class PreviewRevisionForTask(WorkflowPageViewMixin, workflow.PreviewRevisionForTask):
    def add_error_message(self):
        messages.error(
            self.request,
            _(
                "The page '%(page_title)s' is not currently awaiting moderation in task '%(task_name)s'."
            )
            % {
                "page_title": get_latest_str(self.object),
                "task_name": self.task.name,
            },
        )
