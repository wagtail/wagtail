from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils import timezone
from django.utils.http import urlquote
from django.utils.translation import gettext as _

from wagtail.admin import messages, signals
from wagtail.admin.action_menu import PageActionMenu
from wagtail.admin.views.pages.utils import get_valid_next_url_from_request
from wagtail.core import hooks
from wagtail.core.models import Page


def add_subpage(request, parent_page_id):
    parent_page = get_object_or_404(Page, id=parent_page_id).specific
    if not parent_page.permissions_for_user(request.user).can_add_subpage():
        raise PermissionDenied

    page_types = [
        (model.get_verbose_name(), model._meta.app_label, model._meta.model_name)
        for model in type(parent_page).creatable_subpage_models()
        if model.can_create_at(parent_page)
    ]
    # sort by lower-cased version of verbose name
    page_types.sort(key=lambda page_type: page_type[0].lower())

    if len(page_types) == 1:
        # Only one page type is available - redirect straight to the create form rather than
        # making the user choose
        verbose_name, app_label, model_name = page_types[0]
        return redirect('wagtailadmin_pages:add', app_label, model_name, parent_page.id)

    return TemplateResponse(request, 'wagtailadmin/pages/add_subpage.html', {
        'parent_page': parent_page,
        'page_types': page_types,
        'next': get_valid_next_url_from_request(request),
    })


def create(request, content_type_app_name, content_type_model_name, parent_page_id):
    parent_page = get_object_or_404(Page, id=parent_page_id).specific
    parent_page_perms = parent_page.permissions_for_user(request.user)
    if not parent_page_perms.can_add_subpage():
        raise PermissionDenied

    try:
        content_type = ContentType.objects.get_by_natural_key(content_type_app_name, content_type_model_name)
    except ContentType.DoesNotExist:
        raise Http404

    # Get class
    page_class = content_type.model_class()

    # Make sure the class is a descendant of Page
    if not issubclass(page_class, Page):
        raise Http404

    # page must be in the list of allowed subpage types for this parent ID
    if page_class not in parent_page.creatable_subpage_models():
        raise PermissionDenied

    if not page_class.can_create_at(parent_page):
        raise PermissionDenied

    for fn in hooks.get_hooks('before_create_page'):
        result = fn(request, parent_page, page_class)
        if hasattr(result, 'status_code'):
            return result

    page = page_class(owner=request.user)
    edit_handler = page_class.get_edit_handler()
    edit_handler = edit_handler.bind_to(request=request, instance=page)
    form_class = edit_handler.get_form_class()

    next_url = get_valid_next_url_from_request(request)

    if request.method == 'POST':
        form = form_class(request.POST, request.FILES, instance=page,
                          parent_page=parent_page)

        if form.is_valid():
            page = form.save(commit=False)

            is_publishing = bool(request.POST.get('action-publish')) and parent_page_perms.can_publish_subpage()
            is_submitting = bool(request.POST.get('action-submit')) and parent_page.has_workflow

            if not is_publishing:
                page.live = False

            # Save page
            parent_page.add_child(instance=page)

            # Save revision
            revision = page.save_revision(user=request.user, log_action=False)

            # Publish
            if is_publishing:
                for fn in hooks.get_hooks('before_publish_page'):
                    result = fn(request, page)
                    if hasattr(result, 'status_code'):
                        return result

                revision.publish(user=request.user)

                for fn in hooks.get_hooks('after_publish_page'):
                    result = fn(request, page)
                    if hasattr(result, 'status_code'):
                        return result

            # Submit
            if is_submitting:
                workflow = page.get_workflow()
                workflow.start(page, request.user)

            # Notifications
            if is_publishing:
                if page.go_live_at and page.go_live_at > timezone.now():
                    messages.success(request, _("Page '{0}' created and scheduled for publishing.").format(page.get_admin_display_title()), buttons=[
                        messages.button(reverse('wagtailadmin_pages:edit', args=(page.id,)), _('Edit'))
                    ])
                else:
                    buttons = []
                    if page.url is not None:
                        buttons.append(messages.button(page.url, _('View live'), new_window=True))
                    buttons.append(messages.button(reverse('wagtailadmin_pages:edit', args=(page.id,)), _('Edit')))
                    messages.success(request, _("Page '{0}' created and published.").format(page.get_admin_display_title()), buttons=buttons)

            elif is_submitting:
                buttons = []
                if page.is_previewable():
                    buttons.append(
                        messages.button(
                            reverse('wagtailadmin_pages:view_draft', args=(page.id,)),
                            _('View draft'),
                            new_window=True
                        ),
                    )

                buttons.append(
                    messages.button(
                        reverse('wagtailadmin_pages:edit', args=(page.id,)),
                        _('Edit')
                    )
                )

                messages.success(
                    request,
                    _("Page '{0}' created and submitted for moderation.").format(page.get_admin_display_title()),
                    buttons=buttons
                )
            else:
                messages.success(request, _("Page '{0}' created.").format(page.get_admin_display_title()))

            for fn in hooks.get_hooks('after_create_page'):
                result = fn(request, page)
                if hasattr(result, 'status_code'):
                    return result

            if is_publishing or is_submitting:
                # we're done here
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
            messages.validation_error(
                request, _("The page could not be created due to validation errors"), form
            )
            has_unsaved_changes = True
    else:
        signals.init_new_page.send(sender=create, page=page, parent=parent_page)
        form = form_class(instance=page, parent_page=parent_page)
        has_unsaved_changes = False

    edit_handler = edit_handler.bind_to(form=form)

    return TemplateResponse(request, 'wagtailadmin/pages/create.html', {
        'content_type': content_type,
        'page_class': page_class,
        'parent_page': parent_page,
        'edit_handler': edit_handler,
        'action_menu': PageActionMenu(request, view='create', parent_page=parent_page),
        'preview_modes': page.preview_modes,
        'form': form,
        'next': next_url,
        'has_unsaved_changes': has_unsaved_changes,
    })
