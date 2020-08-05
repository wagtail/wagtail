import json

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.http import urlquote
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _

from wagtail.admin import messages
from wagtail.admin.action_menu import PageActionMenu
from wagtail.admin.views.pages.utils import get_valid_next_url_from_request
from wagtail.core import hooks
from wagtail.core.exceptions import PageClassNotFoundError
from wagtail.core.models import Page, WorkflowState


def edit(request, page_id):
    real_page_record = get_object_or_404(Page, id=page_id)
    latest_revision = real_page_record.get_latest_revision()
    content_type = real_page_record.cached_content_type
    page_class = real_page_record.specific_class

    if page_class is None:
        raise PageClassNotFoundError(
            f"The page '{real_page_record}' cannot be edited because the "
            f"model class used to create it ({content_type.app_label}."
            f"{content_type.model}) can no longer be found in the codebase. "
            "This usually happens as a result of switching between git "
            "branches without running migrations to trigger the removal of "
            "unused ContentTypes. To edit the page, you will need to switch "
            "back to a branch where the model class is still present."
        )

    page = real_page_record.get_latest_revision_as_page()
    parent = page.get_parent()

    page_perms = page.permissions_for_user(request.user)

    if not page_perms.can_edit():
        raise PermissionDenied

    next_url = get_valid_next_url_from_request(request)

    for fn in hooks.get_hooks('before_edit_page'):
        result = fn(request, page)
        if hasattr(result, 'status_code'):
            return result

    edit_handler = page_class.get_edit_handler()
    edit_handler = edit_handler.bind_to(instance=page, request=request)
    form_class = edit_handler.get_form_class()

    if request.method == 'GET':
        if page_perms.user_has_lock():
            if page.locked_at:
                lock_message = format_html(_("<b>Page '{}' was locked</b> by <b>you</b> on <b>{}</b>."), page.get_admin_display_title(), page.locked_at.strftime("%d %b %Y %H:%M"))
            else:
                lock_message = format_html(_("<b>Page '{}' is locked</b> by <b>you</b>."), page.get_admin_display_title())

            lock_message += format_html(
                '<span class="buttons"><button class="button button-small button-secondary" data-locking-action="{}">{}</button></span>',
                reverse('wagtailadmin_pages:unlock', args=(page.id,)),
                _("Unlock")
            )
            messages.warning(request, lock_message, extra_tags='lock')

        elif page.locked and page_perms.page_locked():
            # the page can also be locked at a permissions level if in a workflow, on a task the user is not a reviewer for
            # this should be indicated separately
            if page.locked_by and page.locked_at:
                lock_message = format_html(_("<b>Page '{}' was locked</b> by <b>{}</b> on <b>{}</b>."), page.get_admin_display_title(), str(page.locked_by), page.locked_at.strftime("%d %b %Y %H:%M"))
            else:
                # Page was probably locked with an old version of Wagtail, or a script
                lock_message = format_html(_("<b>Page '{}' is locked</b>."), page.get_admin_display_title())

            if page_perms.can_unlock():
                lock_message += format_html(
                    '<span class="buttons"><button class="button button-small button-secondary" data-locking-action="{}">{}</button></span>',
                    reverse('wagtailadmin_pages:unlock', args=(page.id,)),
                    _("Unlock")
                )
            messages.error(request, lock_message, extra_tags='lock')

        if page.current_workflow_state:
            workflow_state = page.current_workflow_state
            workflow = workflow_state.workflow
            workflow_tasks = workflow_state.all_tasks_with_status()
            task = workflow_state.current_task_state.task
            if (
                workflow_state.status != WorkflowState.STATUS_NEEDS_CHANGES
                and task.specific.page_locked_for_user(page, request.user)
            ):
                # Check for revisions still undergoing moderation and warn
                if len(workflow_tasks) == 1:
                    # If only one task in workflow, show simple message
                    workflow_info = _("This page is currently awaiting moderation.")
                else:
                    workflow_info = format_html(
                        _("This page is awaiting <b>'{}'</b> in the <b>'{}'</b> workflow."),
                        task.name, workflow.name
                    )
                messages.error(request, mark_safe(workflow_info + " " + _("Only reviewers for this task can edit the page.")),
                               extra_tags="lock")
    # Check for revisions still undergoing moderation and warn - this is for the old moderation system
    if latest_revision and latest_revision.submitted_for_moderation:
        buttons = []

        if page.live:
            buttons.append(messages.button(
                reverse('wagtailadmin_pages:revisions_compare', args=(page.id, 'live', latest_revision.id)),
                _('Compare with live version')
            ))

        messages.warning(request, _("This page is currently awaiting moderation"), buttons=buttons)

    # Show current workflow state if set, default to last workflow state
    workflow_state = page.current_workflow_state or page.workflow_states.order_by('created_at').last()
    if workflow_state:
        workflow_tasks = workflow_state.all_tasks_with_status()
    else:
        workflow_tasks = []

    errors_debug = None

    if request.method == 'POST':
        form = form_class(request.POST, request.FILES, instance=page,
                          parent_page=parent)

        is_publishing = False
        is_submitting = False
        is_restarting_workflow = False
        is_reverting = False
        is_saving = False
        is_cancelling_workflow = bool(request.POST.get('action-cancel-workflow')) and workflow_state and workflow_state.user_can_cancel(request.user)
        if is_cancelling_workflow:
            workflow_state.cancel(user=request.user)
            # do this here so even if the page is locked due to not having permissions, the original submitter can still cancel the workflow

        if form.is_valid() and not page_perms.page_locked():
            page = form.save(commit=False)

            is_publishing = bool(request.POST.get('action-publish')) and page_perms.can_publish()
            is_submitting = bool(request.POST.get('action-submit')) and page_perms.can_submit_for_moderation()
            is_restarting_workflow = bool(request.POST.get('action-restart-workflow')) and page_perms.can_submit_for_moderation() and workflow_state and workflow_state.user_can_cancel(request.user)
            is_reverting = bool(request.POST.get('revision'))

            is_performing_workflow_action = bool(request.POST.get('action-workflow-action'))
            if is_performing_workflow_action:
                workflow_action = request.POST['workflow-action-name']
                available_actions = page.current_workflow_task.get_actions(page, request.user)
                available_action_names = [name for name, verbose_name, modal in available_actions]
                if workflow_action not in available_action_names:
                    # prevent this action
                    is_performing_workflow_action = False

            is_saving = True
            has_content_changes = form.has_changed()

            if is_restarting_workflow:
                workflow_state.cancel(user=request.user)

            # If a revision ID was passed in the form, get that revision so its
            # date can be referenced in notification messages
            if is_reverting:
                previous_revision = get_object_or_404(page.revisions, id=request.POST.get('revision'))

            if is_performing_workflow_action and not has_content_changes:
                # don't save a new revision, as we're just going to update the page's
                # workflow state with no content changes
                revision = latest_revision
            else:
                # Save revision
                revision = page.save_revision(
                    user=request.user,
                    log_action=True,  # Always log the new revision on edit
                    previous_revision=(previous_revision if is_reverting else None)
                )

            # store submitted go_live_at for messaging below
            go_live_at = page.go_live_at

            # Publish
            if is_publishing:
                for fn in hooks.get_hooks('before_publish_page'):
                    result = fn(request, page)
                    if hasattr(result, 'status_code'):
                        return result

                revision.publish(
                    user=request.user,
                    changed=has_content_changes,
                    previous_revision=(previous_revision if is_reverting else None)
                )

                # Need to reload the page because the URL may have changed, and we
                # need the up-to-date URL for the "View Live" button.
                page = page.specific_class.objects.get(pk=page.pk)

                for fn in hooks.get_hooks('after_publish_page'):
                    result = fn(request, page)
                    if hasattr(result, 'status_code'):
                        return result

            # Submit
            if is_submitting or is_restarting_workflow:
                if workflow_state and workflow_state.status == WorkflowState.STATUS_NEEDS_CHANGES:
                    # If the workflow was in the needs changes state, resume the existing workflow on submission
                    workflow_state.resume(request.user)
                else:
                    # Otherwise start a new workflow
                    workflow = page.get_workflow()
                    workflow.start(page, request.user)

            if is_performing_workflow_action:
                extra_workflow_data_json = request.POST.get('workflow-action-extra-data', '{}')
                extra_workflow_data = json.loads(extra_workflow_data_json)
                page.current_workflow_task.on_action(page.current_workflow_task_state, request.user, workflow_action, **extra_workflow_data)

        # Notifications
        if is_publishing:
            if go_live_at and go_live_at > timezone.now():
                # Page has been scheduled for publishing in the future

                if is_reverting:
                    message = _(
                        "Version from {0} of page '{1}' has been scheduled for publishing."
                    ).format(
                        previous_revision.created_at.strftime("%d %b %Y %H:%M"),
                        page.get_admin_display_title()
                    )
                else:
                    if page.live:
                        message = _(
                            "Page '{0}' is live and this version has been scheduled for publishing."
                        ).format(
                            page.get_admin_display_title()
                        )

                    else:
                        message = _(
                            "Page '{0}' has been scheduled for publishing."
                        ).format(
                            page.get_admin_display_title()
                        )

                messages.success(request, message, buttons=[
                    messages.button(
                        reverse('wagtailadmin_pages:edit', args=(page.id,)),
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
                        page.get_admin_display_title()
                    )
                else:
                    message = _(
                        "Page '{0}' has been published."
                    ).format(
                        page.get_admin_display_title()
                    )

                buttons = []
                if page.url is not None:
                    buttons.append(messages.button(page.url, _('View live'), new_window=True))
                buttons.append(messages.button(reverse('wagtailadmin_pages:edit', args=(page_id,)), _('Edit')))
                messages.success(request, message, buttons=buttons)

        elif is_submitting:

            message = _(
                "Page '{0}' has been submitted for moderation."
            ).format(
                page.get_admin_display_title()
            )

            messages.success(request, message, buttons=[
                messages.button(
                    reverse('wagtailadmin_pages:view_draft', args=(page_id,)),
                    _('View draft'),
                    new_window=True
                ),
                messages.button(
                    reverse('wagtailadmin_pages:edit', args=(page_id,)),
                    _('Edit')
                )
            ])

        elif is_cancelling_workflow:
            message = _(
                "Workflow on page '{0}' has been cancelled."
            ).format(
                page.get_admin_display_title()
            )

            messages.success(request, message, buttons=[
                messages.button(
                    reverse('wagtailadmin_pages:view_draft', args=(page_id,)),
                    _('View draft'),
                    new_window=True
                ),
                messages.button(
                    reverse('wagtailadmin_pages:edit', args=(page_id,)),
                    ('Edit')
                )
            ])

        elif is_restarting_workflow:

            message = _(
                "Workflow on page '{0}' has been restarted."
            ).format(
                page.get_admin_display_title()
            )

            messages.success(request, message, buttons=[
                messages.button(
                    reverse('wagtailadmin_pages:view_draft', args=(page_id,)),
                    _('View draft'),
                    new_window=True
                ),
                messages.button(
                    reverse('wagtailadmin_pages:edit', args=(page_id,)),
                    _('Edit')
                )
            ])

        elif is_reverting:
            message = _(
                "Page '{0}' has been replaced with version from {1}."
            ).format(
                page.get_admin_display_title(),
                previous_revision.created_at.strftime("%d %b %Y %H:%M")
            )

            messages.success(request, message)
        elif is_saving:
            message = _(
                "Page '{0}' has been updated."
            ).format(
                page.get_admin_display_title()
            )

            messages.success(request, message)

        if is_saving:
            for fn in hooks.get_hooks('after_edit_page'):
                result = fn(request, page)
                if hasattr(result, 'status_code'):
                    return result

            if is_publishing or is_submitting or is_restarting_workflow or is_performing_workflow_action:
                # we're done here - redirect back to the explorer
                if next_url:
                    # redirect back to 'next' url if present
                    return redirect(next_url)
                # redirect back to the explorer
                return redirect('wagtailadmin_explore', page.get_parent().id)
            else:
                # Just saving - remain on edit page for further edits
                target_url = reverse('wagtailadmin_pages:edit', args=[page.id])
                if next_url:
                    # Ensure the 'next' url is passed through again if present
                    target_url += '?next=%s' % urlquote(next_url)
                return redirect(target_url)
        else:
            if page_perms.page_locked():
                messages.error(request, _("The page could not be saved as it is locked"))
            else:
                messages.validation_error(
                    request, _("The page could not be saved due to validation errors"), form
                )
            errors_debug = (
                repr(form.errors)
                + repr([
                    (name, formset.errors)
                    for (name, formset) in form.formsets.items()
                    if formset.errors
                ])
            )
            has_unsaved_changes = True
    else:
        form = form_class(instance=page, parent_page=parent)
        has_unsaved_changes = False

    edit_handler = edit_handler.bind_to(form=form)

    # Check for revisions still undergoing moderation and warn
    if latest_revision and latest_revision.submitted_for_moderation:
        buttons = []

        if page.live:
            buttons.append(messages.button(
                reverse('wagtailadmin_pages:revisions_compare', args=(page.id, 'live', latest_revision.id)),
                _('Compare with live version')
            ))

        messages.warning(request, _("This page is currently awaiting moderation"), buttons=buttons)

    if page.live and page.has_unpublished_changes:
        # Page status needs to present the version of the page containing the correct live URL
        page_for_status = real_page_record.specific
    else:
        page_for_status = page

    return TemplateResponse(request, 'wagtailadmin/pages/edit.html', {
        'page': page,
        'page_for_status': page_for_status,
        'content_type': content_type,
        'edit_handler': edit_handler,
        'errors_debug': errors_debug,
        'action_menu': PageActionMenu(request, view='edit', page=page),
        'preview_modes': page.preview_modes,
        'form': form,
        'next': next_url,
        'has_unsaved_changes': has_unsaved_changes,
        'page_locked': page_perms.page_locked(),
        'workflow_state': workflow_state if workflow_state and workflow_state.is_active else None,
        'current_task_state': page.current_workflow_task_state,
        'publishing_will_cancel_workflow': workflow_tasks and getattr(settings, 'WAGTAIL_WORKFLOW_CANCEL_ON_PUBLISH', True)
    })
