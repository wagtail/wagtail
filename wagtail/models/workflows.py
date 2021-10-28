from django import forms
from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import models, transaction
from django.db.models import Q
from django.db.models.expressions import OuterRef, Subquery
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.module_loading import import_string
from django.utils.text import capfirst
from django.utils.translation import gettext_lazy as _
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel

from wagtail.forms import TaskStateCommentForm
from wagtail.logging import log
from wagtail.models import Orderable, Page, PageRevision, WorkflowPage
from wagtail.models.copying import _copy, _copy_m2m_relations
from wagtail.signals import (
    task_approved, task_cancelled, task_rejected, task_submitted, workflow_approved,
    workflow_cancelled, workflow_rejected, workflow_submitted)


class WorkflowTask(Orderable):
    workflow = ParentalKey('Workflow', on_delete=models.CASCADE, verbose_name=_('workflow_tasks'),
                           related_name='workflow_tasks')
    task = models.ForeignKey('Task', on_delete=models.CASCADE, verbose_name=_('task'), related_name='workflow_tasks',
                             limit_choices_to={'active': True})

    class Meta(Orderable.Meta):
        unique_together = [('workflow', 'task')]
        verbose_name = _('workflow task order')
        verbose_name_plural = _('workflow task orders')


class TaskManager(models.Manager):
    def active(self):
        return self.filter(active=True)


class Task(models.Model):
    name = models.CharField(max_length=255, verbose_name=_('name'))
    content_type = models.ForeignKey(
        ContentType,
        verbose_name=_('content type'),
        related_name='wagtail_tasks',
        on_delete=models.CASCADE
    )
    active = models.BooleanField(verbose_name=_('active'), default=True, help_text=_(
        "Active tasks can be added to workflows. Deactivating a task does not remove it from existing workflows."))
    objects = TaskManager()

    admin_form_fields = ['name']
    admin_form_readonly_on_edit_fields = ['name']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.id:
            # this model is being newly created
            # rather than retrieved from the db;
            if not self.content_type_id:
                # set content type to correctly represent the model class
                # that this was created as
                self.content_type = ContentType.objects.get_for_model(self)

    def __str__(self):
        return self.name

    @property
    def workflows(self):
        """Returns all ``Workflow`` instances that use this task"""
        return Workflow.objects.filter(workflow_tasks__task=self)

    @property
    def active_workflows(self):
        """Return a ``QuerySet``` of active workflows that this task is part of"""
        return Workflow.objects.active().filter(workflow_tasks__task=self)

    @classmethod
    def get_verbose_name(cls):
        """
        Returns the human-readable "verbose name" of this task model e.g "Group approval task".
        """
        # This is similar to doing cls._meta.verbose_name.title()
        # except this doesn't convert any characters to lowercase
        return capfirst(cls._meta.verbose_name)

    @cached_property
    def specific(self):
        """
        Return this Task in its most specific subclassed form.
        """
        # the ContentType.objects manager keeps a cache, so this should potentially
        # avoid a database lookup over doing self.content_type. I think.
        content_type = ContentType.objects.get_for_id(self.content_type_id)
        model_class = content_type.model_class()
        if model_class is None:
            # Cannot locate a model class for this content type. This might happen
            # if the codebase and database are out of sync (e.g. the model exists
            # on a different git branch and we haven't rolled back migrations before
            # switching branches); if so, the best we can do is return the page
            # unchanged.
            return self
        elif isinstance(self, model_class):
            # self is already the an instance of the most specific class
            return self
        else:
            return content_type.get_object_for_this_type(id=self.id)

    task_state_class = None

    @classmethod
    def get_task_state_class(self):
        return self.task_state_class or TaskState

    def start(self, workflow_state, user=None):
        """Start this task on the provided workflow state by creating an instance of TaskState"""
        task_state = self.get_task_state_class()(workflow_state=workflow_state)
        task_state.status = TaskState.STATUS_IN_PROGRESS
        task_state.page_revision = workflow_state.page.get_latest_revision()
        task_state.task = self
        task_state.save()
        task_submitted.send(sender=task_state.specific.__class__, instance=task_state.specific, user=user)
        return task_state

    @transaction.atomic
    def on_action(self, task_state, user, action_name, **kwargs):
        """Performs an action on a task state determined by the ``action_name`` string passed"""
        if action_name == 'approve':
            task_state.approve(user=user, **kwargs)
        elif action_name == 'reject':
            task_state.reject(user=user, **kwargs)

    def user_can_access_editor(self, page, user):
        """Returns True if a user who would not normally be able to access the editor for the page should be able to if the page is currently on this task.
        Note that returning False does not remove permissions from users who would otherwise have them."""
        return False

    def page_locked_for_user(self, page, user):
        """Returns True if the page should be locked to a given user's edits. This can be used to prevent editing by non-reviewers."""
        return False

    def user_can_lock(self, page, user):
        """Returns True if a user who would not normally be able to lock the page should be able to if the page is currently on this task.
        Note that returning False does not remove permissions from users who would otherwise have them."""
        return False

    def user_can_unlock(self, page, user):
        """Returns True if a user who would not normally be able to unlock the page should be able to if the page is currently on this task.
        Note that returning False does not remove permissions from users who would otherwise have them."""
        return False

    def get_actions(self, page, user):
        """
        Get the list of action strings (name, verbose_name, whether the action requires additional data - see
        ``get_form_for_action``) for actions the current user can perform for this task on the given page.
        These strings should be the same as those able to be passed to ``on_action``
        """
        return []

    def get_form_for_action(self, action):
        return TaskStateCommentForm

    def get_template_for_action(self, action):
        return ''

    def get_task_states_user_can_moderate(self, user, **kwargs):
        """Returns a ``QuerySet`` of the task states the current user can moderate"""
        return TaskState.objects.none()

    @classmethod
    def get_description(cls):
        """Returns the task description."""
        return ''

    @transaction.atomic
    def deactivate(self, user=None):
        """Set ``active`` to False and cancel all in progress task states linked to this task"""
        self.active = False
        self.save()
        in_progress_states = TaskState.objects.filter(task=self, status=TaskState.STATUS_IN_PROGRESS)
        for state in in_progress_states:
            state.cancel(user=user)

    class Meta:
        verbose_name = _('task')
        verbose_name_plural = _('tasks')


class WorkflowManager(models.Manager):
    def active(self):
        return self.filter(active=True)


class Workflow(ClusterableModel):
    name = models.CharField(max_length=255, verbose_name=_('name'))
    active = models.BooleanField(verbose_name=_('active'), default=True, help_text=_(
        "Active workflows can be added to pages. Deactivating a workflow does not remove it from existing pages."))
    objects = WorkflowManager()

    def __str__(self):
        return self.name

    @property
    def tasks(self):
        """Returns all ``Task`` instances linked to this workflow"""
        return Task.objects.filter(workflow_tasks__workflow=self).order_by('workflow_tasks__sort_order')

    @transaction.atomic
    def start(self, page, user):
        """Initiates a workflow by creating an instance of ``WorkflowState``"""
        state = WorkflowState(page=page, workflow=self, status=WorkflowState.STATUS_IN_PROGRESS, requested_by=user)
        state.save()
        state.update(user=user)
        workflow_submitted.send(sender=state.__class__, instance=state, user=user)

        next_task_data = None
        if state.current_task_state:
            next_task_data = {
                'id': state.current_task_state.task.id,
                'title': state.current_task_state.task.name,
            }
        log(
            instance=page,
            action='wagtail.workflow.start',
            data={
                'workflow': {
                    'id': self.id,
                    'title': self.name,
                    'status': state.status,
                    'next': next_task_data,
                    'task_state_id': state.current_task_state.id if state.current_task_state else None,
                }
            },
            revision=page.get_latest_revision(),
            user=user,
        )

        return state

    @transaction.atomic
    def deactivate(self, user=None):
        """Sets the workflow as inactive, and cancels all in progress instances of ``WorkflowState`` linked to this workflow"""
        self.active = False
        in_progress_states = WorkflowState.objects.filter(workflow=self, status=WorkflowState.STATUS_IN_PROGRESS)
        for state in in_progress_states:
            state.cancel(user=user)
        WorkflowPage.objects.filter(workflow=self).delete()
        self.save()

    def all_pages(self):
        """
        Returns a queryset of all the pages that this Workflow applies to.
        """
        pages = Page.objects.none()

        for workflow_page in self.workflow_pages.all():
            pages |= workflow_page.get_pages()

        return pages

    class Meta:
        verbose_name = _('workflow')
        verbose_name_plural = _('workflows')


class GroupApprovalTask(Task):
    groups = models.ManyToManyField(Group, verbose_name=_('groups'), help_text=_('Pages at this step in a workflow will be moderated or approved by these groups of users'))

    admin_form_fields = Task.admin_form_fields + ['groups']
    admin_form_widgets = {
        'groups': forms.CheckboxSelectMultiple,
    }

    def start(self, workflow_state, user=None):
        if workflow_state.page.locked_by:
            # If the person who locked the page isn't in one of the groups, unlock the page
            if not workflow_state.page.locked_by.groups.filter(id__in=self.groups.all()).exists():
                workflow_state.page.locked = False
                workflow_state.page.locked_by = None
                workflow_state.page.locked_at = None
                workflow_state.page.save(update_fields=['locked', 'locked_by', 'locked_at'])

        return super().start(workflow_state, user=user)

    def user_can_access_editor(self, page, user):
        return self.groups.filter(id__in=user.groups.all()).exists() or user.is_superuser

    def page_locked_for_user(self, page, user):
        return not (self.groups.filter(id__in=user.groups.all()).exists() or user.is_superuser)

    def user_can_lock(self, page, user):
        return self.groups.filter(id__in=user.groups.all()).exists()

    def user_can_unlock(self, page, user):
        return False

    def get_actions(self, page, user):
        if self.groups.filter(id__in=user.groups.all()).exists() or user.is_superuser:
            return [
                ('reject', _("Request changes"), True),
                ('approve', _("Approve"), False),
                ('approve', _("Approve with comment"), True),
            ]

        return []

    def get_task_states_user_can_moderate(self, user, **kwargs):
        if self.groups.filter(id__in=user.groups.all()).exists() or user.is_superuser:
            return TaskState.objects.filter(status=TaskState.STATUS_IN_PROGRESS, task=self.task_ptr)
        else:
            return TaskState.objects.none()

    @classmethod
    def get_description(cls):
        return _("Members of the chosen Wagtail Groups can approve this task")

    class Meta:
        verbose_name = _('Group approval task')
        verbose_name_plural = _('Group approval tasks')


class WorkflowStateManager(models.Manager):
    def active(self):
        """
        Filters to only STATUS_IN_PROGRESS and STATUS_NEEDS_CHANGES WorkflowStates
        """
        return self.filter(Q(status=WorkflowState.STATUS_IN_PROGRESS) | Q(status=WorkflowState.STATUS_NEEDS_CHANGES))


class WorkflowState(models.Model):
    """Tracks the status of a started Workflow on a Page."""
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_APPROVED = 'approved'
    STATUS_NEEDS_CHANGES = 'needs_changes'
    STATUS_CANCELLED = 'cancelled'
    STATUS_CHOICES = (
        (STATUS_IN_PROGRESS, _("In progress")),
        (STATUS_APPROVED, _("Approved")),
        (STATUS_NEEDS_CHANGES, _("Needs changes")),
        (STATUS_CANCELLED, _("Cancelled")),
    )

    page = models.ForeignKey('Page', on_delete=models.CASCADE, verbose_name=_("page"), related_name='workflow_states')
    workflow = models.ForeignKey('Workflow', on_delete=models.CASCADE, verbose_name=_('workflow'), related_name='workflow_states')
    status = models.fields.CharField(choices=STATUS_CHOICES, verbose_name=_("status"), max_length=50, default=STATUS_IN_PROGRESS)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("created at"))
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL,
                                     verbose_name=_('requested by'),
                                     null=True,
                                     blank=True,
                                     editable=True,
                                     on_delete=models.SET_NULL,
                                     related_name='requested_workflows')
    current_task_state = models.OneToOneField('TaskState', on_delete=models.SET_NULL, null=True, blank=True,
                                              verbose_name=_("current task state"))

    # allows a custom function to be called on finishing the Workflow successfully.
    on_finish = import_string(getattr(settings, 'WAGTAIL_FINISH_WORKFLOW_ACTION', 'wagtail.workflows.publish_workflow_state'))

    objects = WorkflowStateManager()

    def clean(self):
        super().clean()

        if self.status in (self.STATUS_IN_PROGRESS, self.STATUS_NEEDS_CHANGES):
            # The unique constraint is conditional, and so not supported on the MySQL backend - so an additional check is done here
            if WorkflowState.objects.active().filter(page=self.page).exclude(pk=self.pk).exists():
                raise ValidationError(_('There may only be one in progress or needs changes workflow state per page.'))

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return _("Workflow '{0}' on Page '{1}': {2}").format(self.workflow, self.page, self.status)

    def resume(self, user=None):
        """Put a STATUS_NEEDS_CHANGES workflow state back into STATUS_IN_PROGRESS, and restart the current task"""
        if self.status != self.STATUS_NEEDS_CHANGES:
            raise PermissionDenied
        revision = self.current_task_state.page_revision
        current_task_state = self.current_task_state
        self.current_task_state = None
        self.status = self.STATUS_IN_PROGRESS
        self.save()

        log(
            instance=self.page.specific,
            action='wagtail.workflow.resume',
            data={
                'workflow': {
                    'id': self.workflow_id,
                    'title': self.workflow.name,
                    'status': self.status,
                    'task_state_id': current_task_state.id,
                    'task': {
                        'id': current_task_state.task.id,
                        'title': current_task_state.task.name,
                    },
                }
            },
            revision=revision,
            user=user,
        )
        return self.update(user=user, next_task=current_task_state.task)

    def user_can_cancel(self, user):
        if self.page.locked and self.page.locked_by != user:
            return False
        return user == self.requested_by or user == self.page.owner or (self.current_task_state and self.current_task_state.status == self.current_task_state.STATUS_IN_PROGRESS and 'approve' in [action[0] for action in self.current_task_state.task.get_actions(self.page, user)])

    def update(self, user=None, next_task=None):
        """Checks the status of the current task, and progresses (or ends) the workflow if appropriate. If the workflow progresses,
        next_task will be used to start a specific task next if provided."""
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
                if (not self.current_task_state) or self.current_task_state.status != self.current_task_state.STATUS_IN_PROGRESS:
                    # if not on a task, or the next task to move to is not the current task (ie current task's status is
                    # not STATUS_IN_PROGRESS), move to the next task
                    self.current_task_state = next_task.specific.start(self, user=user)
                    self.save()
                    # if task has auto-approved, update the workflow again
                    if self.current_task_state.status != self.current_task_state.STATUS_IN_PROGRESS:
                        self.update(user=user)
                # otherwise, continue on the current task
            else:
                # if there is no uncompleted task, finish the workflow.
                self.finish(user=user)

    @property
    def successful_task_states(self):
        successful_task_states = self.task_states.filter(
            Q(status=TaskState.STATUS_APPROVED) | Q(status=TaskState.STATUS_SKIPPED)
        )
        if getattr(settings, "WAGTAIL_WORKFLOW_REQUIRE_REAPPROVAL_ON_EDIT", False):
            successful_task_states = successful_task_states.filter(page_revision=self.page.get_latest_revision())

        return successful_task_states

    def get_next_task(self):
        """Returns the next active task, which has not been either approved or skipped"""

        return (
            Task.objects.filter(workflow_tasks__workflow=self.workflow, active=True)
            .exclude(
                task_states__in=self.successful_task_states
            ).order_by('workflow_tasks__sort_order').first()
        )

    def cancel(self, user=None):
        """Cancels the workflow state"""
        if self.status not in (self.STATUS_IN_PROGRESS, self.STATUS_NEEDS_CHANGES):
            raise PermissionDenied
        self.status = self.STATUS_CANCELLED
        self.save()

        log(
            instance=self.page.specific,
            action='wagtail.workflow.cancel',
            data={
                'workflow': {
                    'id': self.workflow_id,
                    'title': self.workflow.name,
                    'status': self.status,
                    'task_state_id': self.current_task_state.id,
                    'task': {
                        'id': self.current_task_state.task.id,
                        'title': self.current_task_state.task.name,
                    },
                }
            },
            revision=self.current_task_state.page_revision,
            user=user,
        )

        for state in self.task_states.filter(status=TaskState.STATUS_IN_PROGRESS):
            # Cancel all in progress task states
            state.specific.cancel(user=user)
        workflow_cancelled.send(sender=self.__class__, instance=self, user=user)

    @transaction.atomic
    def finish(self, user=None):
        """Finishes a successful in progress workflow, marking it as approved and performing the ``on_finish`` action"""
        if self.status != self.STATUS_IN_PROGRESS:
            raise PermissionDenied
        self.status = self.STATUS_APPROVED
        self.save()
        self.on_finish(user=user)
        workflow_approved.send(sender=self.__class__, instance=self, user=user)

    def copy_approved_task_states_to_revision(self, revision):
        """This creates copies of previously approved task states with page_revision set to a different revision."""
        approved_states = TaskState.objects.filter(workflow_state=self, status=TaskState.STATUS_APPROVED)
        for state in approved_states:
            state.copy(update_attrs={'page_revision': revision})

    def revisions(self):
        """Returns all page revisions associated with task states linked to the current workflow state"""
        return PageRevision.objects.filter(
            page_id=self.page_id,
            id__in=self.task_states.values_list('page_revision_id', flat=True)
        ).defer('content_json')

    def _get_applicable_task_states(self):
        """Returns the set of task states whose status applies to the current revision"""

        task_states = TaskState.objects.filter(workflow_state_id=self.id)
        # If WAGTAIL_WORKFLOW_REQUIRE_REAPPROVAL_ON_EDIT=True, this is only task states created on the current revision
        if getattr(settings, "WAGTAIL_WORKFLOW_REQUIRE_REAPPROVAL_ON_EDIT", False):
            latest_revision_id = self.revisions().order_by('-created_at', '-id').values_list('id', flat=True).first()
            task_states = task_states.filter(page_revision_id=latest_revision_id)
        return task_states

    def all_tasks_with_status(self):
        """
        Returns a list of Task objects that are linked with this workflow state's
        workflow. The status of that task in this workflow state is annotated in the
        `.status` field. And a displayable version of that status is annotated in the
        `.status_display` field.

        This is different to querying TaskState as it also returns tasks that haven't
        been started yet (so won't have a TaskState).
        """
        # Get the set of task states whose status applies to the current revision
        task_states = self._get_applicable_task_states()

        tasks = list(
            self.workflow.tasks.annotate(
                status=Subquery(
                    task_states.filter(
                        task_id=OuterRef('id'),
                    ).order_by(
                        '-started_at', '-id'
                    ).values('status')[:1]
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
                        task_id=OuterRef('id'),
                    ).order_by(
                        '-started_at', '-id'
                    ).values('id')[:1]
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
        """Returns the next active task, which has not been either approved or skipped"""

        last_task = Task.objects.filter(workflow_tasks__workflow=self.workflow, active=True)\
            .exclude(task_states__in=self.successful_task_states)\
            .order_by('workflow_tasks__sort_order').last()

        return self.get_next_task() == last_task

    class Meta:
        verbose_name = _('Workflow state')
        verbose_name_plural = _('Workflow states')
        # prevent multiple STATUS_IN_PROGRESS/STATUS_NEEDS_CHANGES workflows for the same page. This is only supported by specific databases (e.g. Postgres, SQL Server), so is checked additionally on save.
        constraints = [
            models.UniqueConstraint(fields=['page'], condition=Q(status__in=('in_progress', 'needs_changes')), name='unique_in_progress_workflow')
        ]


class TaskStateManager(models.Manager):
    def reviewable_by(self, user):
        tasks = Task.objects.filter(active=True)
        states = TaskState.objects.none()
        for task in tasks:
            states = states | task.specific.get_task_states_user_can_moderate(user=user)
        return states


class TaskState(models.Model):
    """Tracks the status of a given Task for a particular page revision."""
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_SKIPPED = 'skipped'
    STATUS_CANCELLED = 'cancelled'
    STATUS_CHOICES = (
        (STATUS_IN_PROGRESS, _("In progress")),
        (STATUS_APPROVED, _("Approved")),
        (STATUS_REJECTED, _("Rejected")),
        (STATUS_SKIPPED, _("Skipped")),
        (STATUS_CANCELLED, _("Cancelled")),
    )

    workflow_state = models.ForeignKey('WorkflowState', on_delete=models.CASCADE, verbose_name=_('workflow state'), related_name='task_states')
    page_revision = models.ForeignKey('PageRevision', on_delete=models.CASCADE, verbose_name=_('page revision'), related_name='task_states')
    task = models.ForeignKey('Task', on_delete=models.CASCADE, verbose_name=_('task'), related_name='task_states')
    status = models.fields.CharField(choices=STATUS_CHOICES, verbose_name=_("status"), max_length=50, default=STATUS_IN_PROGRESS)
    started_at = models.DateTimeField(verbose_name=_('started at'), auto_now_add=True)
    finished_at = models.DateTimeField(verbose_name=_('finished at'), blank=True, null=True)
    finished_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_('finished by'),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='finished_task_states'
    )
    comment = models.TextField(blank=True)
    content_type = models.ForeignKey(
        ContentType,
        verbose_name=_('content type'),
        related_name='wagtail_task_states',
        on_delete=models.CASCADE
    )
    exclude_fields_in_copy = []
    default_exclude_fields_in_copy = ['id']

    objects = TaskStateManager()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.id:
            # this model is being newly created
            # rather than retrieved from the db;
            if not self.content_type_id:
                # set content type to correctly represent the model class
                # that this was created as
                self.content_type = ContentType.objects.get_for_model(self)

    def __str__(self):
        return _("Task '{0}' on Page Revision '{1}': {2}").format(self.task, self.page_revision, self.status)

    @cached_property
    def specific(self):
        """
        Return this TaskState in its most specific subclassed form.
        """
        # the ContentType.objects manager keeps a cache, so this should potentially
        # avoid a database lookup over doing self.content_type. I think.
        content_type = ContentType.objects.get_for_id(self.content_type_id)
        model_class = content_type.model_class()
        if model_class is None:
            # Cannot locate a model class for this content type. This might happen
            # if the codebase and database are out of sync (e.g. the model exists
            # on a different git branch and we haven't rolled back migrations before
            # switching branches); if so, the best we can do is return the page
            # unchanged.
            return self
        elif isinstance(self, model_class):
            # self is already the an instance of the most specific class
            return self
        else:
            return content_type.get_object_for_this_type(id=self.id)

    @transaction.atomic
    def approve(self, user=None, update=True, comment=''):
        """Approve the task state and update the workflow state"""
        if self.status != self.STATUS_IN_PROGRESS:
            raise PermissionDenied
        self.status = self.STATUS_APPROVED
        self.finished_at = timezone.now()
        self.finished_by = user
        self.comment = comment
        self.save()

        self.log_state_change_action(user, 'approve')
        if update:
            self.workflow_state.update(user=user)
        task_approved.send(sender=self.specific.__class__, instance=self.specific, user=user)
        return self

    @transaction.atomic
    def reject(self, user=None, update=True, comment=''):
        """Reject the task state and update the workflow state"""
        if self.status != self.STATUS_IN_PROGRESS:
            raise PermissionDenied
        self.status = self.STATUS_REJECTED
        self.finished_at = timezone.now()
        self.finished_by = user
        self.comment = comment
        self.save()

        self.log_state_change_action(user, 'reject')
        if update:
            self.workflow_state.update(user=user)
        task_rejected.send(sender=self.specific.__class__, instance=self.specific, user=user)

        return self

    @cached_property
    def task_type_started_at(self):
        """Finds the first chronological started_at for successive TaskStates - ie started_at if the task had not been restarted"""
        task_states = TaskState.objects.filter(workflow_state=self.workflow_state).order_by('-started_at').select_related('task')
        started_at = None
        for task_state in task_states:
            if task_state.task == self.task:
                started_at = task_state.started_at
            elif started_at:
                break
        return started_at

    @transaction.atomic
    def cancel(self, user=None, resume=False, comment=''):
        """Cancel the task state and update the workflow state. If ``resume`` is set to True, then upon update the workflow state
        is passed the current task as ``next_task``, causing it to start a new task state on the current task if possible"""
        self.status = self.STATUS_CANCELLED
        self.finished_at = timezone.now()
        self.comment = comment
        self.finished_by = user
        self.save()
        if resume:
            self.workflow_state.update(user=user, next_task=self.task.specific)
        else:
            self.workflow_state.update(user=user)
        task_cancelled.send(sender=self.specific.__class__, instance=self.specific, user=user)
        return self

    def copy(self, update_attrs=None, exclude_fields=None):
        """Copy this task state, excluding the attributes in the ``exclude_fields`` list and updating any attributes to values
        specified in the ``update_attrs`` dictionary of ``attribute``: ``new value`` pairs"""
        exclude_fields = self.default_exclude_fields_in_copy + self.exclude_fields_in_copy + (exclude_fields or [])
        instance, child_object_map = _copy(self.specific, exclude_fields, update_attrs)
        instance.save()
        _copy_m2m_relations(self, instance, exclude_fields=exclude_fields)
        return instance

    def get_comment(self):
        """
        Returns a string that is displayed in workflow history.

        This could be a comment by the reviewer, or generated.
        Use mark_safe to return HTML.
        """
        return self.comment

    def log_state_change_action(self, user, action):
        """Log the approval/rejection action"""
        page = self.page_revision.as_page_object()
        next_task = self.workflow_state.get_next_task()
        next_task_data = None
        if next_task:
            next_task_data = {
                'id': next_task.id,
                'title': next_task.name
            }
        log(
            instance=page,
            action='wagtail.workflow.{}'.format(action),
            user=user,
            data={
                'workflow': {
                    'id': self.workflow_state.workflow.id,
                    'title': self.workflow_state.workflow.name,
                    'status': self.status,
                    'task_state_id': self.id,
                    'task': {
                        'id': self.task.id,
                        'title': self.task.name,
                    },
                    'next': next_task_data,
                },
                'comment': self.get_comment()
            },
            revision=self.page_revision
        )

    class Meta:
        verbose_name = _('Task state')
        verbose_name_plural = _('Task states')
