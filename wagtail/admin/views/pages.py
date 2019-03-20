from time import time

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count
from django.http import Http404, HttpResponse, JsonResponse
from django.http.request import QueryDict
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.http import is_safe_url, urlquote
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.vary import vary_on_headers
from django.views.generic import View

from wagtail.admin import messages, signals
from wagtail.admin.action_menu import PageActionMenu
from wagtail.admin.forms.pages import CopyForm
from wagtail.admin.forms.search import SearchForm
from wagtail.admin.navigation import get_explorable_root_page
from wagtail.admin.utils import send_notification, user_has_any_page_permission, user_passes_test
from wagtail.core import hooks
from wagtail.core.models import Page, PageRevision, UserPagePermissionsProxy
from wagtail.search.query import MATCH_ALL


def get_valid_next_url_from_request(request):
    next_url = request.POST.get('next') or request.GET.get('next')
    if not next_url or not is_safe_url(url=next_url, allowed_hosts={request.get_host()}):
        return ''
    return next_url


@user_passes_test(user_has_any_page_permission)
def index(request, parent_page_id=None):
    if parent_page_id:
        parent_page = get_object_or_404(Page, id=parent_page_id)
    else:
        parent_page = Page.get_first_root_node()

    # This will always succeed because of the @user_passes_test above.
    root_page = get_explorable_root_page(request.user)

    # If this page isn't a descendant of the user's explorable root page,
    # then redirect to that explorable root page instead.
    if not (
        parent_page.pk == root_page.pk
        or parent_page.is_descendant_of(root_page)
    ):
        return redirect('wagtailadmin_explore', root_page.pk)

    parent_page = parent_page.specific

    pages = parent_page.get_children().prefetch_related('content_type', 'sites_rooted_here')

    # Get page ordering
    ordering = request.GET.get('ordering', '-latest_revision_created_at')
    if ordering not in [
        'title',
        '-title',
        'content_type',
        '-content_type',
        'live', '-live',
        'latest_revision_created_at',
        '-latest_revision_created_at',
        'ord'
    ]:
        ordering = '-latest_revision_created_at'

    if ordering == 'ord':
        # preserve the native ordering from get_children()
        pass
    elif ordering == 'latest_revision_created_at':
        # order by oldest revision first.
        # Special case NULL entries - these should go at the top of the list.
        # Do this by annotating with Count('latest_revision_created_at'),
        # which returns 0 for these
        pages = pages.annotate(
            null_position=Count('latest_revision_created_at')
        ).order_by('null_position', 'latest_revision_created_at')
    elif ordering == '-latest_revision_created_at':
        # order by oldest revision first.
        # Special case NULL entries - these should go at the end of the list.
        pages = pages.annotate(
            null_position=Count('latest_revision_created_at')
        ).order_by('-null_position', '-latest_revision_created_at')
    else:
        pages = pages.order_by(ordering)

    # Don't paginate if sorting by page order - all pages must be shown to
    # allow drag-and-drop reordering
    do_paginate = ordering != 'ord'

    if do_paginate or pages.count() < 100:
        # Retrieve pages in their most specific form, so that custom
        # get_admin_display_title and get_url_parts methods on subclasses are respected.
        # However, skip this on unpaginated listings with >100 child pages as this could
        # be a significant performance hit. (This should only happen on the reorder view,
        # and hopefully no-one is having to do manual reordering on listings that large...)
        pages = pages.specific(defer=True)

    # allow hooks to modify the queryset
    for hook in hooks.get_hooks('construct_explorer_page_queryset'):
        pages = hook(parent_page, pages, request)

    # Pagination
    if do_paginate:
        paginator = Paginator(pages, per_page=50)
        pages = paginator.get_page(request.GET.get('p'))

    return render(request, 'wagtailadmin/pages/index.html', {
        'parent_page': parent_page.specific,
        'ordering': ordering,
        'pagination_query_params': "ordering=%s" % ordering,
        'pages': pages,
        'do_paginate': do_paginate,
    })


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

    return render(request, 'wagtailadmin/pages/add_subpage.html', {
        'parent_page': parent_page,
        'page_types': page_types,
        'next': get_valid_next_url_from_request(request),
    })


def content_type_use(request, content_type_app_name, content_type_model_name):
    try:
        content_type = ContentType.objects.get_by_natural_key(content_type_app_name, content_type_model_name)
    except ContentType.DoesNotExist:
        raise Http404

    page_class = content_type.model_class()

    # page_class must be a Page type and not some other random model
    if not issubclass(page_class, Page):
        raise Http404

    pages = page_class.objects.all()

    paginator = Paginator(pages, per_page=10)
    pages = paginator.get_page(request.GET.get('p'))

    return render(request, 'wagtailadmin/pages/content_type_use.html', {
        'pages': pages,
        'app_name': content_type_app_name,
        'content_type': content_type,
        'page_class': page_class,
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
            is_submitting = bool(request.POST.get('action-submit'))

            if not is_publishing:
                page.live = False

            # Save page
            parent_page.add_child(instance=page)

            # Save revision
            revision = page.save_revision(
                user=request.user,
                submitted_for_moderation=is_submitting,
            )

            # Publish
            if is_publishing:
                revision.publish()

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
                messages.success(
                    request,
                    _("Page '{0}' created and submitted for moderation.").format(page.get_admin_display_title()),
                    buttons=[
                        messages.button(
                            reverse('wagtailadmin_pages:view_draft', args=(page.id,)),
                            _('View draft'),
                            new_window=True
                        ),
                        messages.button(
                            reverse('wagtailadmin_pages:edit', args=(page.id,)),
                            _('Edit')
                        )
                    ]
                )
                if not send_notification(page.get_latest_revision().id, 'submitted', request.user.pk):
                    messages.error(request, _("Failed to send notifications to moderators"))
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

    return render(request, 'wagtailadmin/pages/create.html', {
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


def edit(request, page_id):
    real_page_record = get_object_or_404(Page, id=page_id)
    latest_revision = real_page_record.get_latest_revision()
    page = real_page_record.get_latest_revision_as_page()
    parent = page.get_parent()

    content_type = ContentType.objects.get_for_model(page)
    page_class = content_type.model_class()

    page_perms = page.permissions_for_user(request.user)
    if not page_perms.can_edit():
        raise PermissionDenied

    for fn in hooks.get_hooks('before_edit_page'):
        result = fn(request, page)
        if hasattr(result, 'status_code'):
            return result

    edit_handler = page_class.get_edit_handler()
    edit_handler = edit_handler.bind_to(instance=page, request=request)
    form_class = edit_handler.get_form_class()

    next_url = get_valid_next_url_from_request(request)

    errors_debug = None

    if request.method == 'POST':
        form = form_class(request.POST, request.FILES, instance=page,
                          parent_page=parent)

        if form.is_valid() and not page.locked:
            page = form.save(commit=False)

            is_publishing = bool(request.POST.get('action-publish')) and page_perms.can_publish()
            is_submitting = bool(request.POST.get('action-submit'))
            is_reverting = bool(request.POST.get('revision'))

            # If a revision ID was passed in the form, get that revision so its
            # date can be referenced in notification messages
            if is_reverting:
                previous_revision = get_object_or_404(page.revisions, id=request.POST.get('revision'))

            # Save revision
            revision = page.save_revision(
                user=request.user,
                submitted_for_moderation=is_submitting,
            )
            # store submitted go_live_at for messaging below
            go_live_at = page.go_live_at

            # Publish
            if is_publishing:
                revision.publish()
                # Need to reload the page because the URL may have changed, and we
                # need the up-to-date URL for the "View Live" button.
                page = page.specific_class.objects.get(pk=page.pk)

            # Notifications
            if is_publishing:
                if go_live_at and go_live_at > timezone.now():
                    # Page has been scheduled for publishing in the future

                    if is_reverting:
                        message = _(
                            "Revision from {0} of page '{1}' has been scheduled for publishing."
                        ).format(
                            previous_revision.created_at.strftime("%d %b %Y %H:%M"),
                            page.get_admin_display_title()
                        )
                    else:
                        if page.live:
                            message = _(
                                "Page '{0}' is live and this revision has been scheduled for publishing."
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
                            "Revision from {0} of page '{1}' has been published."
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

                if not send_notification(page.get_latest_revision().id, 'submitted', request.user.pk):
                    messages.error(request, _("Failed to send notifications to moderators"))

            else:  # Saving

                if is_reverting:
                    message = _(
                        "Page '{0}' has been replaced with revision from {1}."
                    ).format(
                        page.get_admin_display_title(),
                        previous_revision.created_at.strftime("%d %b %Y %H:%M")
                    )
                else:
                    message = _(
                        "Page '{0}' has been updated."
                    ).format(
                        page.get_admin_display_title()
                    )

                messages.success(request, message)

            for fn in hooks.get_hooks('after_edit_page'):
                result = fn(request, page)
                if hasattr(result, 'status_code'):
                    return result

            if is_publishing or is_submitting:
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
            if page.locked:
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

    return render(request, 'wagtailadmin/pages/edit.html', {
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
    })


def delete(request, page_id):
    page = get_object_or_404(Page, id=page_id).specific
    if not page.permissions_for_user(request.user).can_delete():
        raise PermissionDenied

    with transaction.atomic():
        for fn in hooks.get_hooks('before_delete_page'):
            result = fn(request, page)
            if hasattr(result, 'status_code'):
                return result

        next_url = get_valid_next_url_from_request(request)

        if request.method == 'POST':
            parent_id = page.get_parent().id
            page.delete()

            messages.success(request, _("Page '{0}' deleted.").format(page.get_admin_display_title()))

            for fn in hooks.get_hooks('after_delete_page'):
                result = fn(request, page)
                if hasattr(result, 'status_code'):
                    return result

            if next_url:
                return redirect(next_url)
            return redirect('wagtailadmin_explore', parent_id)

    return render(request, 'wagtailadmin/pages/confirm_delete.html', {
        'page': page,
        'descendant_count': page.get_descendant_count(),
        'next': next_url,
    })


def view_draft(request, page_id):
    page = get_object_or_404(Page, id=page_id).get_latest_revision_as_page()
    perms = page.permissions_for_user(request.user)
    if not (perms.can_publish() or perms.can_edit()):
        raise PermissionDenied
    return page.serve_preview(page.dummy_request(request), page.default_preview_mode)


class PreviewOnEdit(View):
    http_method_names = ('post', 'get')
    preview_expiration_timeout = 60 * 60 * 24  # seconds
    session_key_prefix = 'wagtail-preview-'

    def remove_old_preview_data(self):
        expiration = time() - self.preview_expiration_timeout
        expired_keys = [
            k for k, v in self.request.session.items()
            if k.startswith(self.session_key_prefix) and v[1] < expiration]
        # Removes the session key gracefully
        for k in expired_keys:
            self.request.session.pop(k)

    @property
    def session_key(self):
        return self.session_key_prefix + ','.join(self.args)

    def get_page(self):
        return get_object_or_404(Page,
                                 id=self.args[0]).get_latest_revision_as_page()

    def get_form(self, page, query_dict):
        form_class = page.get_edit_handler().get_form_class()
        parent_page = page.get_parent().specific

        if self.session_key not in self.request.session:
            # Session key not in session, returning null form
            return form_class(instance=page, parent_page=parent_page)

        return form_class(query_dict, instance=page, parent_page=parent_page)

    def post(self, request, *args, **kwargs):
        # TODO: Handle request.FILES.
        request.session[self.session_key] = request.POST.urlencode(), time()
        self.remove_old_preview_data()
        form = self.get_form(self.get_page(), request.POST)
        return JsonResponse({'is_valid': form.is_valid()})

    def error_response(self, page):
        return render(self.request, 'wagtailadmin/pages/preview_error.html',
                      {'page': page})

    def get(self, request, *args, **kwargs):
        page = self.get_page()

        post_data, timestamp = self.request.session.get(self.session_key,
                                                        (None, None))
        if not isinstance(post_data, str):
            post_data = ''
        form = self.get_form(page, QueryDict(post_data))

        if not form.is_valid():
            return self.error_response(page)

        form.save(commit=False)
        preview_mode = request.GET.get('mode', page.default_preview_mode)
        return page.serve_preview(page.dummy_request(request),
                                  preview_mode)


class PreviewOnCreate(PreviewOnEdit):
    def get_page(self):
        (content_type_app_name, content_type_model_name,
         parent_page_id) = self.args
        try:
            content_type = ContentType.objects.get_by_natural_key(
                content_type_app_name, content_type_model_name)
        except ContentType.DoesNotExist:
            raise Http404

        page = content_type.model_class()()
        parent_page = get_object_or_404(Page, id=parent_page_id).specific
        # We need to populate treebeard's path / depth fields in order to
        # pass validation. We can't make these 100% consistent with the rest
        # of the tree without making actual database changes (such as
        # incrementing the parent's numchild field), but by calling treebeard's
        # internal _get_path method, we can set a 'realistic' value that will
        # hopefully enable tree traversal operations
        # to at least partially work.
        page.depth = parent_page.depth + 1
        # Puts the page at the maximum possible path
        # for a child of `parent_page`.
        page.path = Page._get_children_path_interval(parent_page.path)[1]
        return page

    def get_form(self, page, query_dict):
        form = super().get_form(page, query_dict)
        if form.is_valid():
            # Ensures our unsaved page has a suitable url.
            form.instance.set_url_path(form.parent_page)

            form.instance.full_clean()
        return form


def unpublish(request, page_id):
    page = get_object_or_404(Page, id=page_id).specific

    user_perms = UserPagePermissionsProxy(request.user)
    if not user_perms.for_page(page).can_unpublish():
        raise PermissionDenied

    next_url = get_valid_next_url_from_request(request)

    if request.method == 'POST':
        include_descendants = request.POST.get("include_descendants", False)

        page.unpublish()

        if include_descendants:
            live_descendant_pages = page.get_descendants().live().specific()
            for live_descendant_page in live_descendant_pages:
                if user_perms.for_page(live_descendant_page).can_unpublish():
                    live_descendant_page.unpublish()

        messages.success(request, _("Page '{0}' unpublished.").format(page.get_admin_display_title()), buttons=[
            messages.button(reverse('wagtailadmin_pages:edit', args=(page.id,)), _('Edit'))
        ])

        if next_url:
            return redirect(next_url)
        return redirect('wagtailadmin_explore', page.get_parent().id)

    return render(request, 'wagtailadmin/pages/confirm_unpublish.html', {
        'page': page,
        'next': next_url,
        'live_descendant_count': page.get_descendants().live().count(),
    })


def move_choose_destination(request, page_to_move_id, viewed_page_id=None):
    page_to_move = get_object_or_404(Page, id=page_to_move_id)
    page_perms = page_to_move.permissions_for_user(request.user)
    if not page_perms.can_move():
        raise PermissionDenied

    if viewed_page_id:
        viewed_page = get_object_or_404(Page, id=viewed_page_id)
    else:
        viewed_page = Page.get_first_root_node()

    viewed_page.can_choose = page_perms.can_move_to(viewed_page)

    child_pages = []
    for target in viewed_page.get_children():
        # can't move the page into itself or its descendants
        target.can_choose = page_perms.can_move_to(target)

        target.can_descend = (
            not(target == page_to_move
                or target.is_child_of(page_to_move))
            and target.get_children_count()
        )

        child_pages.append(target)

    # Pagination
    paginator = Paginator(child_pages, per_page=50)
    child_pages = paginator.get_page(request.GET.get('p'))

    return render(request, 'wagtailadmin/pages/move_choose_destination.html', {
        'page_to_move': page_to_move,
        'viewed_page': viewed_page,
        'child_pages': child_pages,
    })


def move_confirm(request, page_to_move_id, destination_id):
    page_to_move = get_object_or_404(Page, id=page_to_move_id).specific
    destination = get_object_or_404(Page, id=destination_id)
    if not page_to_move.permissions_for_user(request.user).can_move_to(destination):
        raise PermissionDenied

    if not Page._slug_is_available(page_to_move.slug, destination, page=page_to_move):
        messages.error(
            request,
            _("The slug '{0}' is already in use at the selected parent page. Make sure the slug is unique and try again".format(page_to_move.slug))
        )
        return redirect('wagtailadmin_pages:move_choose_destination', page_to_move.id, destination.id)

    for fn in hooks.get_hooks('before_move_page'):
        result = fn(request, page_to_move, destination)
        if hasattr(result, 'status_code'):
            return result

    if request.method == 'POST':
        # any invalid moves *should* be caught by the permission check above,
        # so don't bother to catch InvalidMoveToDescendant
        page_to_move.move(destination, pos='last-child')

        messages.success(request, _("Page '{0}' moved.").format(page_to_move.get_admin_display_title()), buttons=[
            messages.button(reverse('wagtailadmin_pages:edit', args=(page_to_move.id,)), _('Edit'))
        ])

        for fn in hooks.get_hooks('after_move_page'):
            result = fn(request, page_to_move)
            if hasattr(result, 'status_code'):
                return result

        return redirect('wagtailadmin_explore', destination.id)

    return render(request, 'wagtailadmin/pages/confirm_move.html', {
        'page_to_move': page_to_move,
        'destination': destination,
    })


def set_page_position(request, page_to_move_id):
    page_to_move = get_object_or_404(Page, id=page_to_move_id)
    parent_page = page_to_move.get_parent()

    if not parent_page.permissions_for_user(request.user).can_reorder_children():
        raise PermissionDenied

    if request.method == 'POST':
        # Get position parameter
        position = request.GET.get('position', None)

        # Find page thats already in this position
        position_page = None
        if position is not None:
            try:
                position_page = parent_page.get_children()[int(position)]
            except IndexError:
                pass  # No page in this position

        # Move page

        # any invalid moves *should* be caught by the permission check above,
        # so don't bother to catch InvalidMoveToDescendant

        if position_page:
            # If the page has been moved to the right, insert it to the
            # right. If left, then left.
            old_position = list(parent_page.get_children()).index(page_to_move)
            if int(position) < old_position:
                page_to_move.move(position_page, pos='left')
            elif int(position) > old_position:
                page_to_move.move(position_page, pos='right')
        else:
            # Move page to end
            page_to_move.move(parent_page, pos='last-child')

    return HttpResponse('')


@user_passes_test(user_has_any_page_permission)
def copy(request, page_id):
    page = Page.objects.get(id=page_id)

    # Parent page defaults to parent of source page
    parent_page = page.get_parent()

    # Check if the user has permission to publish subpages on the parent
    can_publish = parent_page.permissions_for_user(request.user).can_publish_subpage()

    # Create the form
    form = CopyForm(request.POST or None, user=request.user, page=page, can_publish=can_publish)

    next_url = get_valid_next_url_from_request(request)

    for fn in hooks.get_hooks('before_copy_page'):
        result = fn(request, page)
        if hasattr(result, 'status_code'):
            return result

    # Check if user is submitting
    if request.method == 'POST':
        # Prefill parent_page in case the form is invalid (as prepopulated value for the form field,
        # because ModelChoiceField seems to not fall back to the user given value)
        parent_page = Page.objects.get(id=request.POST['new_parent_page'])

        if form.is_valid():
            # Receive the parent page (this should never be empty)
            if form.cleaned_data['new_parent_page']:
                parent_page = form.cleaned_data['new_parent_page']

            if not page.permissions_for_user(request.user).can_copy_to(parent_page,
                                                                       form.cleaned_data.get('copy_subpages')):
                raise PermissionDenied

            # Re-check if the user has permission to publish subpages on the new parent
            can_publish = parent_page.permissions_for_user(request.user).can_publish_subpage()

            # Copy the page
            new_page = page.specific.copy(
                recursive=form.cleaned_data.get('copy_subpages'),
                to=parent_page,
                update_attrs={
                    'title': form.cleaned_data['new_title'],
                    'slug': form.cleaned_data['new_slug'],
                },
                keep_live=(can_publish and form.cleaned_data.get('publish_copies')),
                user=request.user,
            )

            # Give a success message back to the user
            if form.cleaned_data.get('copy_subpages'):
                messages.success(
                    request,
                    _("Page '{0}' and {1} subpages copied.").format(page.get_admin_display_title(), new_page.get_descendants().count())
                )
            else:
                messages.success(request, _("Page '{0}' copied.").format(page.get_admin_display_title()))

            for fn in hooks.get_hooks('after_copy_page'):
                result = fn(request, page, new_page)
                if hasattr(result, 'status_code'):
                    return result

            # Redirect to explore of parent page
            if next_url:
                return redirect(next_url)
            return redirect('wagtailadmin_explore', parent_page.id)

    return render(request, 'wagtailadmin/pages/copy.html', {
        'page': page,
        'form': form,
        'next': next_url,
    })


@vary_on_headers('X-Requested-With')
@user_passes_test(user_has_any_page_permission)
def search(request):
    pages = all_pages = Page.objects.all().prefetch_related('content_type').specific()
    q = MATCH_ALL
    content_types = []
    pagination_query_params = QueryDict({}, mutable=True)
    ordering = None

    if 'ordering' in request.GET:
        if request.GET['ordering'] in ['title', '-title', 'latest_revision_created_at', '-latest_revision_created_at', 'live', '-live']:
            ordering = request.GET['ordering']

            if ordering == 'title':
                pages = pages.order_by('title')
            elif ordering == '-title':
                pages = pages.order_by('-title')

            if ordering == 'latest_revision_created_at':
                pages = pages.order_by('latest_revision_created_at')
            elif ordering == '-latest_revision_created_at':
                pages = pages.order_by('-latest_revision_created_at')

            if ordering == 'live':
                pages = pages.order_by('live')
            elif ordering == '-live':
                pages = pages.order_by('-live')

    if 'content_type' in request.GET:
        pagination_query_params['content_type'] = request.GET['content_type']

        app_label, model_name = request.GET['content_type'].split('.')

        try:
            selected_content_type = ContentType.objects.get_by_natural_key(app_label, model_name)
        except ContentType.DoesNotExist:
            raise Http404

        pages = pages.filter(content_type=selected_content_type)
    else:
        selected_content_type = None

    if 'q' in request.GET:
        form = SearchForm(request.GET)
        if form.is_valid():
            q = form.cleaned_data['q']
            pagination_query_params['q'] = q

            all_pages = all_pages.search(q, order_by_relevance=not ordering, operator='and')
            pages = pages.search(q, order_by_relevance=not ordering, operator='and')

            if pages.supports_facet:
                content_types = [
                    (ContentType.objects.get(id=content_type_id), count)
                    for content_type_id, count in all_pages.facet('content_type_id').items()
                ]

    else:
        form = SearchForm()

    paginator = Paginator(pages, per_page=20)
    pages = paginator.get_page(request.GET.get('p'))

    if request.is_ajax():
        return render(request, "wagtailadmin/pages/search_results.html", {
            'pages': pages,
            'all_pages': all_pages,
            'query_string': q,
            'content_types': content_types,
            'selected_content_type': selected_content_type,
            'ordering': ordering,
            'pagination_query_params': pagination_query_params.urlencode(),
        })
    else:
        return render(request, "wagtailadmin/pages/search.html", {
            'search_form': form,
            'pages': pages,
            'all_pages': all_pages,
            'query_string': q,
            'content_types': content_types,
            'selected_content_type': selected_content_type,
            'ordering': ordering,
            'pagination_query_params': pagination_query_params.urlencode(),
        })


def approve_moderation(request, revision_id):
    revision = get_object_or_404(PageRevision, id=revision_id)
    if not revision.page.permissions_for_user(request.user).can_publish():
        raise PermissionDenied

    if not revision.submitted_for_moderation:
        messages.error(request, _("The page '{0}' is not currently awaiting moderation.").format(revision.page.get_admin_display_title()))
        return redirect('wagtailadmin_home')

    if request.method == 'POST':
        revision.approve_moderation()

        message = _("Page '{0}' published.").format(revision.page.get_admin_display_title())
        buttons = []
        if revision.page.url is not None:
            buttons.append(messages.button(revision.page.url, _('View live'), new_window=True))
        buttons.append(messages.button(reverse('wagtailadmin_pages:edit', args=(revision.page.id,)), _('Edit')))
        messages.success(request, message, buttons=buttons)

        if not send_notification(revision.id, 'approved', request.user.pk):
            messages.error(request, _("Failed to send approval notifications"))

    return redirect('wagtailadmin_home')


def reject_moderation(request, revision_id):
    revision = get_object_or_404(PageRevision, id=revision_id)
    if not revision.page.permissions_for_user(request.user).can_publish():
        raise PermissionDenied

    if not revision.submitted_for_moderation:
        messages.error(request, _("The page '{0}' is not currently awaiting moderation.").format(revision.page.get_admin_display_title()))
        return redirect('wagtailadmin_home')

    if request.method == 'POST':
        revision.reject_moderation()
        messages.success(request, _("Page '{0}' rejected for publication.").format(revision.page.get_admin_display_title()), buttons=[
            messages.button(reverse('wagtailadmin_pages:edit', args=(revision.page.id,)), _('Edit'))
        ])
        if not send_notification(revision.id, 'rejected', request.user.pk):
            messages.error(request, _("Failed to send rejection notifications"))

    return redirect('wagtailadmin_home')


@require_GET
def preview_for_moderation(request, revision_id):
    revision = get_object_or_404(PageRevision, id=revision_id)
    if not revision.page.permissions_for_user(request.user).can_publish():
        raise PermissionDenied

    if not revision.submitted_for_moderation:
        messages.error(request, _("The page '{0}' is not currently awaiting moderation.").format(revision.page.get_admin_display_title()))
        return redirect('wagtailadmin_home')

    page = revision.as_page_object()

    request.revision_id = revision_id

    # pass in the real user request rather than page.dummy_request(), so that request.user
    # and request.revision_id will be picked up by the wagtail user bar
    return page.serve_preview(request, page.default_preview_mode)


@require_POST
def lock(request, page_id):
    # Get the page
    page = get_object_or_404(Page, id=page_id).specific

    # Check permissions
    if not page.permissions_for_user(request.user).can_lock():
        raise PermissionDenied

    # Lock the page
    if not page.locked:
        page.locked = True
        page.save()

        messages.success(request, _("Page '{0}' is now locked.").format(page.get_admin_display_title()))

    # Redirect
    redirect_to = request.POST.get('next', None)
    if redirect_to and is_safe_url(url=redirect_to, allowed_hosts={request.get_host()}):
        return redirect(redirect_to)
    else:
        return redirect('wagtailadmin_explore', page.get_parent().id)


@require_POST
def unlock(request, page_id):
    # Get the page
    page = get_object_or_404(Page, id=page_id).specific

    # Check permissions
    if not page.permissions_for_user(request.user).can_lock():
        raise PermissionDenied

    # Unlock the page
    if page.locked:
        page.locked = False
        page.save()

        messages.success(request, _("Page '{0}' is now unlocked.").format(page.get_admin_display_title()))

    # Redirect
    redirect_to = request.POST.get('next', None)
    if redirect_to and is_safe_url(url=redirect_to, allowed_hosts={request.get_host()}):
        return redirect(redirect_to)
    else:
        return redirect('wagtailadmin_explore', page.get_parent().id)


@user_passes_test(user_has_any_page_permission)
def revisions_index(request, page_id):
    page = get_object_or_404(Page, id=page_id).specific

    # Get page ordering
    ordering = request.GET.get('ordering', '-created_at')
    if ordering not in ['created_at', '-created_at', ]:
        ordering = '-created_at'

    revisions = page.revisions.order_by(ordering)

    paginator = Paginator(revisions, per_page=20)
    revisions = paginator.get_page(request.GET.get('p'))

    return render(request, 'wagtailadmin/pages/revisions/index.html', {
        'page': page,
        'ordering': ordering,
        'pagination_query_params': "ordering=%s" % ordering,
        'revisions': revisions,
    })


def revisions_revert(request, page_id, revision_id):
    page = get_object_or_404(Page, id=page_id).specific
    page_perms = page.permissions_for_user(request.user)
    if not page_perms.can_edit():
        raise PermissionDenied

    revision = get_object_or_404(page.revisions, id=revision_id)
    revision_page = revision.as_page_object()

    content_type = ContentType.objects.get_for_model(page)
    page_class = content_type.model_class()

    edit_handler = page_class.get_edit_handler()
    edit_handler = edit_handler.bind_to(instance=revision_page,
                                        request=request)
    form_class = edit_handler.get_form_class()

    form = form_class(instance=revision_page)
    edit_handler = edit_handler.bind_to(form=form)

    user_avatar = render_to_string('wagtailadmin/shared/user_avatar.html', {'user': revision.user})

    messages.warning(request, mark_safe(
        _("You are viewing a previous revision of this page from <b>%(created_at)s</b> by %(user)s") % {
            'created_at': revision.created_at.strftime("%d %b %Y %H:%M"),
            'user': user_avatar,
        }
    ))

    return render(request, 'wagtailadmin/pages/edit.html', {
        'page': page,
        'revision': revision,
        'is_revision': True,
        'content_type': content_type,
        'edit_handler': edit_handler,
        'errors_debug': None,
        'action_menu': PageActionMenu(request, view='revisions_revert', page=page),
        'preview_modes': page.preview_modes,
        'form': form,  # Used in unit tests
    })


@user_passes_test(user_has_any_page_permission)
def revisions_view(request, page_id, revision_id):
    page = get_object_or_404(Page, id=page_id).specific
    revision = get_object_or_404(page.revisions, id=revision_id)
    revision_page = revision.as_page_object()

    return revision_page.serve_preview(page.dummy_request(request), page.default_preview_mode)


def revisions_compare(request, page_id, revision_id_a, revision_id_b):
    page = get_object_or_404(Page, id=page_id).specific

    # Get revision to compare from
    if revision_id_a == 'live':
        if not page.live:
            raise Http404

        revision_a = page
        revision_a_heading = _("Live")
    elif revision_id_a == 'earliest':
        revision_a = page.revisions.order_by('created_at', 'id').first()
        if revision_a:
            revision_a = revision_a.as_page_object()
            revision_a_heading = _("Earliest")
        else:
            raise Http404
    else:
        revision_a = get_object_or_404(page.revisions, id=revision_id_a).as_page_object()
        revision_a_heading = str(get_object_or_404(page.revisions, id=revision_id_a).created_at)

    # Get revision to compare to
    if revision_id_b == 'live':
        if not page.live:
            raise Http404

        revision_b = page
        revision_b_heading = _("Live")
    elif revision_id_b == 'latest':
        revision_b = page.revisions.order_by('created_at', 'id').last()
        if revision_b:
            revision_b = revision_b.as_page_object()
            revision_b_heading = _("Latest")
        else:
            raise Http404
    else:
        revision_b = get_object_or_404(page.revisions, id=revision_id_b).as_page_object()
        revision_b_heading = str(get_object_or_404(page.revisions, id=revision_id_b).created_at)

    comparison = page.get_edit_handler().get_comparison()
    comparison = [comp(revision_a, revision_b) for comp in comparison]
    comparison = [comp for comp in comparison if comp.has_changed()]

    return render(request, 'wagtailadmin/pages/revisions/compare.html', {
        'page': page,
        'revision_a_heading': revision_a_heading,
        'revision_a': revision_a,
        'revision_b_heading': revision_b_heading,
        'revision_b': revision_b,
        'comparison': comparison,
    })


def revisions_unschedule(request, page_id, revision_id):
    page = get_object_or_404(Page, id=page_id).specific

    user_perms = UserPagePermissionsProxy(request.user)
    if not user_perms.for_page(page).can_unschedule():
        raise PermissionDenied

    revision = get_object_or_404(page.revisions, id=revision_id)

    next_url = get_valid_next_url_from_request(request)

    subtitle = _('revision {0} of "{1}"').format(revision.id, page.get_admin_display_title())

    if request.method == 'POST':
        revision.approved_go_live_at = None
        revision.save(update_fields=['approved_go_live_at'])

        messages.success(request, _('Revision {0} of "{1}" unscheduled.').format(revision.id, page.get_admin_display_title()), buttons=[
            messages.button(reverse('wagtailadmin_pages:edit', args=(page.id,)), _('Edit'))
        ])

        if next_url:
            return redirect(next_url)
        return redirect('wagtailadmin_pages:revisions_index', page.id)

    return render(request, 'wagtailadmin/pages/revisions/confirm_unschedule.html', {
        'page': page,
        'revision': revision,
        'next': next_url,
        'subtitle': subtitle
    })
