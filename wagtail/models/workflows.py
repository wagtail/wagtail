from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import models, transaction
from django.db.models import Q
from django.db.models.expressions import OuterRef, Subquery
from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _
from modelcluster.fields import ParentalKey
from modelcluster.models import (
    ClusterableModel,
)

from wagtail.coreutils import get_content_type_label
from wagtail.log_actions import log
from wagtail.signals import (
    workflow_approved,
    workflow_cancelled,
    workflow_rejected,
    workflow_submitted,
)

from .locking import LockableMixin
from .orderable import Orderable
from .revisions import Revision


class WorkflowContentType(models.Model):
    content_type = models.OneToOneField(
        ContentType,
        related_name="wagtail_workflow_content_type",
        verbose_name=_("content type"),
        on_delete=models.CASCADE,
        primary_key=True,
        unique=True,
    )
    workflow = models.ForeignKey(
        "Workflow",
        related_name="workflow_content_types",
        verbose_name=_("workflow"),
        on_delete=models.CASCADE,
    )

    def __str__(self):
        content_type_label = get_content_type_label(self.content_type)
        return f"WorkflowContentType: {content_type_label} - {self.workflow}"


class WorkflowStateQuerySet(models.QuerySet):
    def active(self):
        """
        Filters to only ``STATUS_IN_PROGRESS`` and ``STATUS_NEEDS_CHANGES`` WorkflowStates.
        """
        return self.filter(
            Q(status=WorkflowState.STATUS_IN_PROGRESS)
            | Q(status=WorkflowState.STATUS_NEEDS_CHANGES)
        )

    def for_instance(self, instance):
        """
        Filters to only WorkflowStates for the given instance.
        """
        try:
            # Use RevisionMixin.get_base_content_type() if available
            return self.filter(
                base_content_type=instance.get_base_content_type(),
                object_id=str(instance.pk),
            )
        except AttributeError:
            # Fallback to ContentType for the model
            return self.filter(
                content_type=ContentType.objects.get_for_model(
                    instance, for_concrete_model=False
                ),
                object_id=str(instance.pk),
            )


WorkflowStateManager = models.Manager.from_queryset(WorkflowStateQuerySet)


class WorkflowState(models.Model):
    """Tracks the status of a started Workflow on an object."""

    STATUS_IN_PROGRESS = "in_progress"
    STATUS_APPROVED = "approved"
    STATUS_NEEDS_CHANGES = "needs_changes"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = (
        (STATUS_IN_PROGRESS, _("In progress")),
        (STATUS_APPROVED, _("Approved")),
        (STATUS_NEEDS_CHANGES, _("Needs changes")),
        (STATUS_CANCELLED, _("Cancelled")),
    )

    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, related_name="+"
    )
    base_content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, related_name="+"
    )
    object_id = models.CharField(max_length=255, verbose_name=_("object id"))

    content_object = GenericForeignKey(
        "base_content_type", "object_id", for_concrete_model=False
    )
    content_object.wagtail_reference_index_ignore = True

    workflow = models.ForeignKey(
        "Workflow",
        on_delete=models.CASCADE,
        verbose_name=_("workflow"),
        related_name="workflow_states",
    )
    status = models.fields.CharField(
        choices=STATUS_CHOICES,
        verbose_name=_("status"),
        max_length=50,
        default=STATUS_IN_PROGRESS,
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("created at"))
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("requested by"),
        null=True,
        blank=True,
        editable=True,
        on_delete=models.SET_NULL,
        related_name="requested_workflows",
    )
    current_task_state = models.OneToOneField(
        "TaskState",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("current task state"),
    )

    # allows a custom function to be called on finishing the Workflow successfully.
    on_finish = import_string(
        getattr(
            settings,
            "WAGTAIL_FINISH_WORKFLOW_ACTION",
            "wagtail.workflows.publish_workflow_state",
        )
    )

    objects = WorkflowStateManager()

    def clean(self):
        super().clean()

        if self.status in (self.STATUS_IN_PROGRESS, self.STATUS_NEEDS_CHANGES):
            # The unique constraint is conditional, and so not supported on the MySQL backend - so an additional check is done here
            if (
                WorkflowState.objects.active()
                .filter(
                    base_content_type_id=self.base_content_type_id,
                    object_id=self.object_id,
                )
                .exclude(pk=self.pk)
                .exists()
            ):
                raise ValidationError(
                    _(
                        "There may only be one in progress or needs changes workflow state per page/snippet."
                    )
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return _(
            "Workflow '%(workflow_name)s' on %(model_name)s '%(title)s': %(status)s"
        ) % {
            "workflow_name": self.workflow,
            "model_name": self.content_object._meta.verbose_name,
            "title": self.content_object,
            "status": self.status,
        }

    def resume(self, user=None):
        """Put a STATUS_NEEDS_CHANGES workflow state back into STATUS_IN_PROGRESS, and restart the current task"""
        from wagtail.models import Page

        if self.status != self.STATUS_NEEDS_CHANGES:
            raise PermissionDenied
        revision = self.current_task_state.revision
        current_task_state = self.current_task_state
        self.current_task_state = None
        self.status = self.STATUS_IN_PROGRESS
        self.save()

        instance = self.content_object
        if isinstance(instance, Page):
            instance = self.content_object.specific

        log(
            instance=instance,
            action="wagtail.workflow.resume",
            data={
                "workflow": {
                    "id": self.workflow_id,
                    "title": self.workflow.name,
                    "status": self.status,
                    "task_state_id": current_task_state.id,
                    "task": {
                        "id": current_task_state.task.id,
                        "title": current_task_state.task.name,
                    },
                }
            },
            revision=revision,
            user=user,
        )
        return self.update(user=user, next_task=current_task_state.task)

    def user_can_cancel(self, user):
        if (
            isinstance(self.content_object, LockableMixin)
            and self.content_object.locked
            and self.content_object.locked_by != user
        ):
            return False
        return (
            user == self.requested_by
            or user == getattr(self.content_object, "owner", None)
            or (
                self.current_task_state
                and self.current_task_state.status
                == self.current_task_state.STATUS_IN_PROGRESS
                and "approve"
                in [
                    action[0]
                    for action in self.current_task_state.task.get_actions(
                        self.content_object, user
                    )
                ]
            )
        )

    def update(self, user=None, next_task=None):
        """
        Checks the status of the current task, and progresses (or ends) the workflow if appropriate.
        If the workflow progresses, next_task will be used to start a specific task next if provided.
        """
        from wagtail.models import TaskState

        if self.status != self.STATUS_IN_PROGRESS:
            # Updating a completed or cancelled workflow should have no effect
            return
        try:
            current_status = self.current_task_state.status
        except AttributeError:
            current_status = None
        if current_status == TaskState.STATUS_REJECTED:
            self.status = self.STATUS_NEEDS_CHANGES
            self.save()
            workflow_rejected.send(sender=self.__class__, instance=self, user=user)
        else:
            if not next_task:
                next_task = self.get_next_task()
            if next_task:
                if (
                    (not self.current_task_state)
                    or self.current_task_state.status
                    != self.current_task_state.STATUS_IN_PROGRESS
                ):
                    # if not on a task, or the next task to move to is not the current task (ie current task's status is
                    # not STATUS_IN_PROGRESS), move to the next task
                    self.current_task_state = next_task.specific.start(self, user=user)
                    self.save()
                    # if task has auto-approved, update the workflow again
                    if (
                        self.current_task_state.status
                        != self.current_task_state.STATUS_IN_PROGRESS
                    ):
                        self.update(user=user)
                # otherwise, continue on the current task
            else:
                # if there is no uncompleted task, finish the workflow.
                self.finish(user=user)

    @property
    def successful_task_states(self):
        from wagtail.models import TaskState

        successful_task_states = self.task_states.filter(
            Q(status=TaskState.STATUS_APPROVED) | Q(status=TaskState.STATUS_SKIPPED)
        )
        if getattr(settings, "WAGTAIL_WORKFLOW_REQUIRE_REAPPROVAL_ON_EDIT", False):
            successful_task_states = successful_task_states.filter(
                revision=self.content_object.get_latest_revision()
            )

        return successful_task_states

    def get_next_task(self):
        """
        Returns the next active task, which has not been either approved or skipped.
        """
        from wagtail.models import Task

        return (
            Task.objects.filter(workflow_tasks__workflow=self.workflow, active=True)
            .exclude(task_states__in=self.successful_task_states)
            .order_by("workflow_tasks__sort_order")
            .first()
        )

    def cancel(self, user=None):
        """Cancels the workflow state"""
        from wagtail.models import Page, TaskState

        if self.status not in (self.STATUS_IN_PROGRESS, self.STATUS_NEEDS_CHANGES):
            raise PermissionDenied
        self.status = self.STATUS_CANCELLED
        self.save()

        instance = self.content_object
        if isinstance(instance, Page):
            instance = self.content_object.specific

        log(
            instance=instance,
            action="wagtail.workflow.cancel",
            data={
                "workflow": {
                    "id": self.workflow_id,
                    "title": self.workflow.name,
                    "status": self.status,
                    "task_state_id": self.current_task_state.id,
                    "task": {
                        "id": self.current_task_state.task.id,
                        "title": self.current_task_state.task.name,
                    },
                }
            },
            revision=self.current_task_state.revision,
            user=user,
        )

        for state in self.task_states.filter(status=TaskState.STATUS_IN_PROGRESS):
            # Cancel all in progress task states
            state.specific.cancel(user=user)
        workflow_cancelled.send(sender=self.__class__, instance=self, user=user)

    @transaction.atomic
    def finish(self, user=None):
        """
        Finishes a successful in progress workflow, marking it as approved and performing the ``on_finish`` action.
        """
        if self.status != self.STATUS_IN_PROGRESS:
            raise PermissionDenied
        self.status = self.STATUS_APPROVED
        self.save()
        self.on_finish(user=user)
        workflow_approved.send(sender=self.__class__, instance=self, user=user)

    def copy_approved_task_states_to_revision(self, revision):
        """
        Creates copies of previously approved task states with revision set to a different revision.
        """
        from wagtail.models import TaskState

        approved_states = TaskState.objects.filter(
            workflow_state=self, status=TaskState.STATUS_APPROVED
        )
        for state in approved_states:
            state.copy(update_attrs={"revision": revision})

    def revisions(self):
        """
        Returns all revisions associated with task states linked to the current workflow state.
        """
        return Revision.objects.filter(
            base_content_type_id=self.base_content_type_id,
            object_id=self.object_id,
            id__in=self.task_states.values_list("revision_id", flat=True),
        ).defer("content")

    def _get_applicable_task_states(self):
        """
        Returns the set of task states whose status applies to the current revision.
        """
        from wagtail.models import TaskState

        task_states = TaskState.objects.filter(workflow_state_id=self.id)
        # If WAGTAIL_WORKFLOW_REQUIRE_REAPPROVAL_ON_EDIT=True, this is only task states created on the current revision
        if getattr(settings, "WAGTAIL_WORKFLOW_REQUIRE_REAPPROVAL_ON_EDIT", False):
            latest_revision_id = (
                self.revisions()
                .order_by("-created_at", "-id")
                .values_list("id", flat=True)
                .first()
            )
            task_states = task_states.filter(revision_id=latest_revision_id)
        return task_states

    def all_tasks_with_status(self):
        """
        Returns a list of Task objects that are linked with this workflow state's
        workflow. The status of that task in this workflow state is annotated in the
        ``.status`` field. And a displayable version of that status is annotated in the
        ``.status_display`` field.

        This is different to querying TaskState as it also returns tasks that haven't
        been started yet (so won't have a TaskState).
        """
        from wagtail.models import TaskState

        # Get the set of task states whose status applies to the current revision
        task_states = self._get_applicable_task_states()

        tasks = list(
            self.workflow.tasks.annotate(
                status=Subquery(
                    task_states.filter(
                        task_id=OuterRef("id"),
                    )
                    .order_by("-started_at", "-id")
                    .values("status")[:1]
                ),
            )
        )

        # Manually annotate status_display
        status_choices = dict(TaskState.STATUS_CHOICES)
        for task in tasks:
            task.status_display = status_choices.get(task.status, _("Not started"))

        return tasks

    def all_tasks_with_state(self):
        """
        Returns a list of Task objects that are linked with this WorkflowState's
        workflow, and have the latest task state.

        In a "Submit for moderation -> reject at step 1 -> resubmit -> accept" workflow, this ensures
        the task list reflects the accept, rather than the reject.
        """
        task_states = self._get_applicable_task_states()

        tasks = list(
            self.workflow.tasks.annotate(
                task_state_id=Subquery(
                    task_states.filter(
                        task_id=OuterRef("id"),
                    )
                    .order_by("-started_at", "-id")
                    .values("id")[:1]
                ),
            )
        )

        task_states = {task_state.id: task_state for task_state in task_states}
        # Manually annotate task_state
        for task in tasks:
            task.task_state = task_states.get(task.task_state_id)

        return tasks

    @property
    def is_active(self):
        return self.status not in [self.STATUS_APPROVED, self.STATUS_CANCELLED]

    @property
    def is_at_final_task(self):
        """
        Returns the next active task, which has not been either approved or skipped.
        """
        from wagtail.models import Task

        last_task = (
            Task.objects.filter(workflow_tasks__workflow=self.workflow, active=True)
            .exclude(task_states__in=self.successful_task_states)
            .order_by("workflow_tasks__sort_order")
            .last()
        )

        return self.get_next_task() == last_task

    class Meta:
        verbose_name = _("Workflow state")
        verbose_name_plural = _("Workflow states")
        # prevent multiple STATUS_IN_PROGRESS/STATUS_NEEDS_CHANGES workflows for the same object. This is only supported by specific databases (e.g. Postgres, SQL Server), so is checked additionally on save.
        constraints = [
            models.UniqueConstraint(
                fields=["base_content_type", "object_id"],
                condition=Q(status__in=("in_progress", "needs_changes")),
                name="unique_in_progress_workflow",
            )
        ]
        indexes = [
            models.Index(
                fields=["content_type", "object_id"],
                name="workflowstate_ct_id_idx",
            ),
            models.Index(
                fields=["base_content_type", "object_id"],
                name="workflowstate_base_ct_id_idx",
            ),
        ]


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
        from wagtail.models import WorkflowPage

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


class WorkflowTask(Orderable):
    workflow = ParentalKey(
        "Workflow",
        on_delete=models.CASCADE,
        verbose_name=_("workflow_tasks"),
        related_name="workflow_tasks",
    )
    task = models.ForeignKey(
        "Task",
        on_delete=models.CASCADE,
        verbose_name=_("task"),
        related_name="workflow_tasks",
        limit_choices_to={"active": True},
    )

    class Meta(Orderable.Meta):
        unique_together = [("workflow", "task")]
        verbose_name = _("workflow task order")
        verbose_name_plural = _("workflow task orders")
