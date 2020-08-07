import json

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.http import urlquote
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _
from django.views.generic.base import ContextMixin, TemplateResponseMixin, View

from wagtail.admin import messages
from wagtail.admin.action_menu import PageActionMenu
from wagtail.admin.views.pages.utils import get_valid_next_url_from_request
from wagtail.core import hooks
from wagtail.core.exceptions import PageClassNotFoundError
from wagtail.core.models import Page, WorkflowState


class EditView(TemplateResponseMixin, ContextMixin, View):
    template_name = 'wagtailadmin/pages/edit.html'

    def dispatch(self, request, page_id):
        self.real_page_record = get_object_or_404(Page, id=page_id)
        self.latest_revision = self.real_page_record.get_latest_revision()
        self.content_type = self.real_page_record.cached_content_type
        self.page_class = self.real_page_record.specific_class

        if self.page_class is None:
            raise PageClassNotFoundError(
                f"The page '{self.real_page_record}' cannot be edited because the "
                f"model class used to create it ({self.content_type.app_label}."
                f"{self.content_type.model}) can no longer be found in the codebase. "
                "This usually happens as a result of switching between git "
                "branches without running migrations to trigger the removal of "
                "unused ContentTypes. To edit the page, you will need to switch "
                "back to a branch where the model class is still present."
            )

        self.page = self.real_page_record.get_latest_revision_as_page()
        self.parent = self.page.get_parent()

        self.page_perms = self.page.permissions_for_user(self.request.user)

        if not self.page_perms.can_edit():
            raise PermissionDenied

        self.next_url = get_valid_next_url_from_request(self.request)

        for fn in hooks.get_hooks('before_edit_page'):
            result = fn(self.request, self.page)
            if hasattr(result, 'status_code'):
                return result

        self.edit_handler = self.page_class.get_edit_handler()
        self.edit_handler = self.edit_handler.bind_to(instance=self.page, request=self.request)
        self.form_class = self.edit_handler.get_form_class()

        # Retrieve current workflow state if set, default to last workflow state
        self.workflow_state = self.page.current_workflow_state or self.page.workflow_states.order_by('created_at').last()
        if self.workflow_state:
            self.workflow_tasks = self.workflow_state.all_tasks_with_status()
        else:
            self.workflow_tasks = []

        self.errors_debug = None

        if self.request.method == 'GET':
            if self.page_perms.user_has_lock():
                if self.page.locked_at:
                    lock_message = format_html(_("<b>Page '{}' was locked</b> by <b>you</b> on <b>{}</b>."), self.page.get_admin_display_title(), self.page.locked_at.strftime("%d %b %Y %H:%M"))
                else:
                    lock_message = format_html(_("<b>Page '{}' is locked</b> by <b>you</b>."), self.page.get_admin_display_title())

                lock_message += format_html(
                    '<span class="buttons"><button class="button button-small button-secondary" data-locking-action="{}">{}</button></span>',
                    reverse('wagtailadmin_pages:unlock', args=(self.page.id,)),
                    _("Unlock")
                )
                messages.warning(self.request, lock_message, extra_tags='lock')

            elif self.page.locked and self.page_perms.page_locked():
                # the page can also be locked at a permissions level if in a workflow, on a task the user is not a reviewer for
                # this should be indicated separately
                if self.page.locked_by and self.page.locked_at:
                    lock_message = format_html(_("<b>Page '{}' was locked</b> by <b>{}</b> on <b>{}</b>."), self.page.get_admin_display_title(), str(self.page.locked_by), self.page.locked_at.strftime("%d %b %Y %H:%M"))
                else:
                    # Page was probably locked with an old version of Wagtail, or a script
                    lock_message = format_html(_("<b>Page '{}' is locked</b>."), self.page.get_admin_display_title())

                if self.page_perms.can_unlock():
                    lock_message += format_html(
                        '<span class="buttons"><button class="button button-small button-secondary" data-locking-action="{}">{}</button></span>',
                        reverse('wagtailadmin_pages:unlock', args=(self.page.id,)),
                        _("Unlock")
                    )
                messages.error(self.request, lock_message, extra_tags='lock')

            if self.page.current_workflow_state:
                workflow = self.workflow_state.workflow
                task = self.workflow_state.current_task_state.task
                if (
                    self.workflow_state.status != WorkflowState.STATUS_NEEDS_CHANGES
                    and task.specific.page_locked_for_user(self.page, self.request.user)
                ):
                    # Check for revisions still undergoing moderation and warn
                    if len(self.workflow_tasks) == 1:
                        # If only one task in workflow, show simple message
                        workflow_info = _("This page is currently awaiting moderation.")
                    else:
                        workflow_info = format_html(
                            _("This page is awaiting <b>'{}'</b> in the <b>'{}'</b> workflow."),
                            task.name, workflow.name
                        )
                    messages.error(self.request, mark_safe(workflow_info + " " + _("Only reviewers for this task can edit the page.")),
                                   extra_tags="lock")

        if self.request.method == 'POST':
            self.form = self.form_class(
                self.request.POST, self.request.FILES, instance=self.page, parent_page=self.parent
            )

            is_publishing = False
            is_submitting = False
            is_restarting_workflow = False
            is_reverting = False
            is_saving = False
            is_cancelling_workflow = bool(self.request.POST.get('action-cancel-workflow')) and self.workflow_state and self.workflow_state.user_can_cancel(self.request.user)
            if is_cancelling_workflow:
                self.workflow_state.cancel(user=self.request.user)
                # do this here so even if the page is locked due to not having permissions, the original submitter can still cancel the workflow

            if self.form.is_valid() and not self.page_perms.page_locked():
                self.page = self.form.save(commit=False)

                is_publishing = bool(self.request.POST.get('action-publish')) and self.page_perms.can_publish()
                is_submitting = bool(self.request.POST.get('action-submit')) and self.page_perms.can_submit_for_moderation()
                is_restarting_workflow = bool(self.request.POST.get('action-restart-workflow')) and self.page_perms.can_submit_for_moderation() and self.workflow_state and self.workflow_state.user_can_cancel(self.request.user)
                is_reverting = bool(self.request.POST.get('revision'))

                is_performing_workflow_action = bool(self.request.POST.get('action-workflow-action'))
                if is_performing_workflow_action:
                    workflow_action = self.request.POST['workflow-action-name']
                    available_actions = self.page.current_workflow_task.get_actions(self.page, self.request.user)
                    available_action_names = [name for name, verbose_name, modal in available_actions]
                    if workflow_action not in available_action_names:
                        # prevent this action
                        is_performing_workflow_action = False

                is_saving = True
                has_content_changes = self.form.has_changed()

                if is_restarting_workflow:
                    self.workflow_state.cancel(user=self.request.user)

                # If a revision ID was passed in the form, get that revision so its
                # date can be referenced in notification messages
                if is_reverting:
                    previous_revision = get_object_or_404(self.page.revisions, id=self.request.POST.get('revision'))

                if is_performing_workflow_action and not has_content_changes:
                    # don't save a new revision, as we're just going to update the page's
                    # workflow state with no content changes
                    revision = self.latest_revision
                else:
                    # Save revision
                    revision = self.page.save_revision(
                        user=self.request.user,
                        log_action=True,  # Always log the new revision on edit
                        previous_revision=(previous_revision if is_reverting else None)
                    )

                # store submitted go_live_at for messaging below
                go_live_at = self.page.go_live_at

                # Publish
                if is_publishing:
                    for fn in hooks.get_hooks('before_publish_page'):
                        result = fn(self.request, self.page)
                        if hasattr(result, 'status_code'):
                            return result

                    revision.publish(
                        user=self.request.user,
                        changed=has_content_changes,
                        previous_revision=(previous_revision if is_reverting else None)
                    )

                    # Need to reload the page because the URL may have changed, and we
                    # need the up-to-date URL for the "View Live" button.
                    self.page = self.page.specific_class.objects.get(pk=self.page.pk)

                    for fn in hooks.get_hooks('after_publish_page'):
                        result = fn(self.request, self.page)
                        if hasattr(result, 'status_code'):
                            return result

                # Submit
                if is_submitting or is_restarting_workflow:
                    if self.workflow_state and self.workflow_state.status == WorkflowState.STATUS_NEEDS_CHANGES:
                        # If the workflow was in the needs changes state, resume the existing workflow on submission
                        self.workflow_state.resume(self.request.user)
                    else:
                        # Otherwise start a new workflow
                        workflow = self.page.get_workflow()
                        workflow.start(self.page, self.request.user)

                if is_performing_workflow_action:
                    extra_workflow_data_json = self.request.POST.get('workflow-action-extra-data', '{}')
                    extra_workflow_data = json.loads(extra_workflow_data_json)
                    self.page.current_workflow_task.on_action(self.page.current_workflow_task_state, self.request.user, workflow_action, **extra_workflow_data)

            # Notifications
            if is_publishing:
                if go_live_at and go_live_at > timezone.now():
                    # Page has been scheduled for publishing in the future

                    if is_reverting:
                        message = _(
                            "Version from {0} of page '{1}' has been scheduled for publishing."
                        ).format(
                            previous_revision.created_at.strftime("%d %b %Y %H:%M"),
                            self.page.get_admin_display_title()
                        )
                    else:
                        if self.page.live:
                            message = _(
                                "Page '{0}' is live and this version has been scheduled for publishing."
                            ).format(
                                self.page.get_admin_display_title()
                            )

                        else:
                            message = _(
                                "Page '{0}' has been scheduled for publishing."
                            ).format(
                                self.page.get_admin_display_title()
                            )

                    messages.success(self.request, message, buttons=[
                        messages.button(
                            reverse('wagtailadmin_pages:edit', args=(self.page.id,)),
                            _('Edit')
                        )
                    ])

                else:
                    # Page is being published now

                    if is_reverting:
                        message = _(
                            "Version from {0} of page '{1}' has been published."
                        ).format(
                            previous_revision.created_at.strftime("%d %b %Y %H:%M"),
                            self.page.get_admin_display_title()
                        )
                    else:
                        message = _(
                            "Page '{0}' has been published."
                        ).format(
                            self.page.get_admin_display_title()
                        )

                    buttons = []
                    if self.page.url is not None:
                        buttons.append(messages.button(self.page.url, _('View live'), new_window=True))
                    buttons.append(messages.button(reverse('wagtailadmin_pages:edit', args=(self.page.id,)), _('Edit')))
                    messages.success(self.request, message, buttons=buttons)

            elif is_submitting:

                message = _(
                    "Page '{0}' has been submitted for moderation."
                ).format(
                    self.page.get_admin_display_title()
                )

                messages.success(self.request, message, buttons=[
                    messages.button(
                        reverse('wagtailadmin_pages:view_draft', args=(self.page.id,)),
                        _('View draft'),
                        new_window=True
                    ),
                    messages.button(
                        reverse('wagtailadmin_pages:edit', args=(self.page.id,)),
                        _('Edit')
                    )
                ])

            elif is_cancelling_workflow:
                message = _(
                    "Workflow on page '{0}' has been cancelled."
                ).format(
                    self.page.get_admin_display_title()
                )

                messages.success(self.request, message, buttons=[
                    messages.button(
                        reverse('wagtailadmin_pages:view_draft', args=(self.page.id,)),
                        _('View draft'),
                        new_window=True
                    ),
                    messages.button(
                        reverse('wagtailadmin_pages:edit', args=(self.page.id,)),
                        ('Edit')
                    )
                ])

            elif is_restarting_workflow:

                message = _(
                    "Workflow on page '{0}' has been restarted."
                ).format(
                    self.page.get_admin_display_title()
                )

                messages.success(self.request, message, buttons=[
                    messages.button(
                        reverse('wagtailadmin_pages:view_draft', args=(self.page.id,)),
                        _('View draft'),
                        new_window=True
                    ),
                    messages.button(
                        reverse('wagtailadmin_pages:edit', args=(self.page.id,)),
                        _('Edit')
                    )
                ])

            elif is_reverting:
                message = _(
                    "Page '{0}' has been replaced with version from {1}."
                ).format(
                    self.page.get_admin_display_title(),
                    previous_revision.created_at.strftime("%d %b %Y %H:%M")
                )

                messages.success(self.request, message)
            elif is_saving:
                message = _(
                    "Page '{0}' has been updated."
                ).format(
                    self.page.get_admin_display_title()
                )

                messages.success(self.request, message)

            if is_saving:
                for fn in hooks.get_hooks('after_edit_page'):
                    result = fn(self.request, self.page)
                    if hasattr(result, 'status_code'):
                        return result

                if is_publishing or is_submitting or is_restarting_workflow or is_performing_workflow_action:
                    # we're done here - redirect back to the explorer
                    if self.next_url:
                        # redirect back to 'next' url if present
                        return redirect(self.next_url)
                    # redirect back to the explorer
                    return redirect('wagtailadmin_explore', self.page.get_parent().id)
                else:
                    # Just saving - remain on edit page for further edits
                    target_url = reverse('wagtailadmin_pages:edit', args=[self.page.id])
                    if self.next_url:
                        # Ensure the 'next' url is passed through again if present
                        target_url += '?next=%s' % urlquote(self.next_url)
                    return redirect(target_url)
            else:
                if self.page_perms.page_locked():
                    messages.error(self.request, _("The page could not be saved as it is locked"))
                else:
                    messages.validation_error(
                        self.request, _("The page could not be saved due to validation errors"), self.form
                    )
                self.errors_debug = (
                    repr(self.form.errors)
                    + repr([
                        (name, formset.errors)
                        for (name, formset) in self.form.formsets.items()
                        if formset.errors
                    ])
                )
                self.has_unsaved_changes = True
        else:
            self.form = self.form_class(instance=self.page, parent_page=self.parent)
            self.has_unsaved_changes = False

        self.edit_handler = self.edit_handler.bind_to(form=self.form)

        # Check for revisions still undergoing moderation and warn - this is for the old moderation system
        if self.latest_revision and self.latest_revision.submitted_for_moderation:
            buttons = []

            if self.page.live:
                buttons.append(messages.button(
                    reverse('wagtailadmin_pages:revisions_compare', args=(self.page.id, 'live', self.latest_revision.id)),
                    _('Compare with live version')
                ))

            messages.warning(self.request, _("This page is currently awaiting moderation"), buttons=buttons)

        if self.page.live and self.page.has_unpublished_changes:
            # Page status needs to present the version of the page containing the correct live URL
            self.page_for_status = self.real_page_record.specific
        else:
            self.page_for_status = self.page

        return self.render_to_response(self.get_context_data())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page': self.page,
            'page_for_status': self.page_for_status,
            'content_type': self.content_type,
            'edit_handler': self.edit_handler,
            'errors_debug': self.errors_debug,
            'action_menu': PageActionMenu(self.request, view='edit', page=self.page),
            'preview_modes': self.page.preview_modes,
            'form': self.form,
            'next': self.next_url,
            'has_unsaved_changes': self.has_unsaved_changes,
            'page_locked': self.page_perms.page_locked(),
            'workflow_state': self.workflow_state if self.workflow_state and self.workflow_state.is_active else None,
            'current_task_state': self.page.current_workflow_task_state,
            'publishing_will_cancel_workflow': self.workflow_tasks and getattr(settings, 'WAGTAIL_WORKFLOW_CANCEL_ON_PUBLISH', True)
        })
        return context
