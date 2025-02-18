from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from modelcluster.models import (
    ClusterableModel,
)

from wagtail.log_actions import log
from wagtail.signals import workflow_submitted


class WorkflowManager(models.Manager):
    def active(self):
        return self.filter(active=True)


class AbstractWorkflow(ClusterableModel):
    name = models.CharField(max_length=255, verbose_name=_("name"))
    active = models.BooleanField(
        verbose_name=_("active"),
        default=True,
        help_text=_(
            "Active workflows can be added to pages/snippets. Deactivating a workflow does not remove it from existing pages/snippets."
        ),
    )
    objects = WorkflowManager()

    def __str__(self):
        return self.name

    @property
    def tasks(self):
        """
        Returns all ``Task`` instances linked to this workflow.
        """
        from wagtail.models import Task

        return Task.objects.filter(workflow_tasks__workflow=self).order_by(
            "workflow_tasks__sort_order"
        )

    @transaction.atomic
    def start(self, obj, user):
        """
        Initiates a workflow by creating an instance of ``WorkflowState``.
        """
        from wagtail.models import WorkflowState

        state = WorkflowState(
            content_type=obj.get_content_type(),
            base_content_type=obj.get_base_content_type(),
            object_id=str(obj.pk),
            workflow=self,
            status=WorkflowState.STATUS_IN_PROGRESS,
            requested_by=user,
        )
        state.save()
        state.update(user=user)
        workflow_submitted.send(sender=state.__class__, instance=state, user=user)

        next_task_data = None
        if state.current_task_state:
            next_task_data = {
                "id": state.current_task_state.task.id,
                "title": state.current_task_state.task.name,
            }
        log(
            instance=obj,
            action="wagtail.workflow.start",
            data={
                "workflow": {
                    "id": self.id,
                    "title": self.name,
                    "status": state.status,
                    "next": next_task_data,
                    "task_state_id": state.current_task_state.id
                    if state.current_task_state
                    else None,
                }
            },
            revision=obj.get_latest_revision(),
            user=user,
        )

        return state

    @transaction.atomic
    def deactivate(self, user=None):
        """
        Sets the workflow as inactive, and cancels all in progress instances of ``WorkflowState`` linked to this workflow.
        """
        from wagtail.models import WorkflowContentType, WorkflowPage, WorkflowState

        self.active = False
        in_progress_states = WorkflowState.objects.filter(
            workflow=self, status=WorkflowState.STATUS_IN_PROGRESS
        )
        for state in in_progress_states:
            state.cancel(user=user)
        WorkflowPage.objects.filter(workflow=self).delete()
        WorkflowContentType.objects.filter(workflow=self).delete()
        self.save()

    def all_pages(self):
        """
        Returns a queryset of all the pages that this Workflow applies to.
        """
        from wagtail.models import Page

        pages = Page.objects.none()

        for workflow_page in self.workflow_pages.all():
            pages |= workflow_page.get_pages()

        return pages

    class Meta:
        verbose_name = _("workflow")
        verbose_name_plural = _("workflows")
        abstract = True


class Workflow(AbstractWorkflow):
    pass
