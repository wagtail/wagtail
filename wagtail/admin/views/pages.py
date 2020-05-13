from time import time

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count
from django.http import Http404, HttpResponse, JsonResponse
from django.http.request import QueryDict
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.http import is_safe_url, urlquote
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.vary import vary_on_headers
from django.views.generic import TemplateView, View

from wagtail.admin import messages, signals
from wagtail.admin.action_menu import PageActionMenu
from wagtail.admin.auth import user_has_any_page_permission, user_passes_test
from wagtail.admin.forms.pages import CopyForm
from wagtail.admin.forms.search import SearchForm
from wagtail.admin.mail import send_notification
from wagtail.admin.navigation import get_explorable_root_page
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

    user_perms = UserPagePermissionsProxy(request.user)
    pages = (
        parent_page.get_children().prefetch_related(
            "content_type", "sites_rooted_here"
        )
        & user_perms.explorable_pages()
    )

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

    return TemplateResponse(request, 'wagtailadmin/pages/index.html', {
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

    return TemplateResponse(request, 'wagtailadmin/pages/add_subpage.html', {
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

    return TemplateResponse(request, 'wagtailadmin/pages/content_type_use.html', {
        'pages': pages,
        'app_name': content_type_app_name,
        'content_type': content_type,
        'page_class': page_class,
    })


# Support for customising create-page / edit-page views on a
# per-page-type basis.
# _create_page_views_by_page_class is a mapping of page classes to
# custom view functions that should be invoked when creating a page
# of that type.
# _edit_page_views_by_page_class is the same for the page edit action.

_create_page_views_by_page_class = {}
_edit_page_views_by_page_class = {}


def register_create_page_view(page_class, view):
    _create_page_views_by_page_class[page_class] = view


def register_edit_page_view(page_class, view):
    _edit_page_views_by_page_class[page_class] = view


class CreatePageView(TemplateView):
    template_name = 'wagtailadmin/pages/create.html'

    def get_page_instance(self):
        return self.page_class(owner=self.request.user)

    def get_edit_handler(self):
        return self.page_class.get_edit_handler()

    def get_form_class(self):
        return self.edit_handler.get_form_class()

    def dispatch(self, request, content_type_app_name, content_type_model_name, parent_page_id):
        try:
            self.content_type = ContentType.objects.get_by_natural_key(content_type_app_name, content_type_model_name)
        except ContentType.DoesNotExist:
            raise Http404

        # Get class
        self.page_class = self.content_type.model_class()

        # Make sure the class is a descendant of Page
        if not issubclass(self.page_class, Page):
            raise Http404

        # Check _create_page_views_by_page_class to see if we've registered a custom
        # create view for this page type - if so, we'll defer to that view instead of
        # continuing here

        # If there _is_ a custom view registered, and it's a subclass of CreatePageView (as expected),
        # we'll end up back here when we call it. We therefore need to set a flag on the request to
        # not repeat the lookup (and end up in an infinite loop)
        if not getattr(request, '_using_custom_create_page_view', False):
            # check page_class and all its superclasses for an entry in _create_page_views_by_page_class
            for cls in self.page_class.__mro__:
                try:
                    view = _create_page_views_by_page_class[cls]
                except KeyError:
                    continue

                request._using_custom_create_page_view = True
                return view(request, content_type_app_name, content_type_model_name, parent_page_id)

        self.parent_page = get_object_or_404(Page, id=parent_page_id).specific
        self.parent_page_perms = self.parent_page.permissions_for_user(request.user)
        if not self.parent_page_perms.can_add_subpage():
            raise PermissionDenied

        # page must be in the list of allowed subpage types for this parent ID
        if self.page_class not in self.parent_page.creatable_subpage_models():
            raise PermissionDenied

        if not self.page_class.can_create_at(self.parent_page):
            raise PermissionDenied

        for fn in hooks.get_hooks('before_create_page'):
            result = fn(request, self.parent_page, self.page_class)
            if hasattr(result, 'status_code'):
                return result

        self.page = self.get_page_instance()
        self.edit_handler = self.get_edit_handler()
        self.edit_handler = self.edit_handler.bind_to(request=request, instance=self.page)
        self.form_class = self.get_form_class()

        self.next_url = get_valid_next_url_from_request(request)

        return super().dispatch(request, content_type_app_name, content_type_model_name, parent_page_id)

    def post(self, request, content_type_app_name, content_type_model_name, parent_page_id):
        self.form = self.form_class(request.POST, request.FILES, instance=self.page,
                                    parent_page=self.parent_page)

        if self.form.is_valid():
            self.page = self.form.save(commit=False)

            is_publishing = bool(request.POST.get('action-publish')) and self.parent_page_perms.can_publish_subpage()
            is_submitting = bool(request.POST.get('action-submit'))

            if not is_publishing:
                self.page.live = False

            # Save page
            self.parent_page.add_child(instance=self.page)

            # Save revision
            revision = self.page.save_revision(
                user=request.user,
                submitted_for_moderation=is_submitting,
            )

            # Publish
            if is_publishing:
                for fn in hooks.get_hooks('before_publish_page'):
                    result = fn(request, self.page)
                    if hasattr(result, 'status_code'):
                        return result

                revision.publish()

                for fn in hooks.get_hooks('after_publish_page'):
                    result = fn(request, self.page)
                    if hasattr(result, 'status_code'):
                        return result

            # Notifications
            if is_publishing:
                if self.page.go_live_at and self.page.go_live_at > timezone.now():
                    messages.success(
                        request,
                        _("Page '{0}' created and scheduled for publishing.").format(self.page.get_admin_display_title()),
                        buttons=[
                            messages.button(reverse('wagtailadmin_pages:edit', args=(self.page.id,)), _('Edit'))
                        ]
                    )
                else:
                    buttons = []
                    if self.page.url is not None:
                        buttons.append(messages.button(self.page.url, _('View live'), new_window=True))
                    buttons.append(messages.button(reverse('wagtailadmin_pages:edit', args=(self.page.id,)), _('Edit')))
                    messages.success(
                        request,
                        _("Page '{0}' created and published.").format(self.page.get_admin_display_title()),
                        buttons=buttons
                    )
            elif is_submitting:
                buttons = []
                if self.page.is_previewable():
                    buttons.append(
                        messages.button(
                            reverse('wagtailadmin_pages:view_draft', args=(self.page.id,)),
                            _('View draft'),
                            new_window=True
                        ),
                    )

                buttons.append(
                    messages.button(
                        reverse('wagtailadmin_pages:edit', args=(self.page.id,)),
                        _('Edit')
                    )
                )

                messages.success(
                    request,
                    _("Page '{0}' created and submitted for moderation.").format(self.page.get_admin_display_title()),
                    buttons=buttons
                )
                if not send_notification(self.page.get_latest_revision().id, 'submitted', request.user.pk):
                    messages.error(request, _("Failed to send notifications to moderators"))
            else:
                messages.success(request, _("Page '{0}' created.").format(self.page.get_admin_display_title()))

            for fn in hooks.get_hooks('after_create_page'):
                result = fn(request, self.page)
                if hasattr(result, 'status_code'):
                    return result

            if is_publishing or is_submitting:
                # we're done here
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
            messages.validation_error(
                request, _("The page could not be created due to validation errors"), self.form
            )
            self.has_unsaved_changes = True

            context = self.get_context_data()
            return self.render_to_response(context)

    def get(self, request, content_type_app_name, content_type_model_name, parent_page_id):
        signals.init_new_page.send(sender=self, page=self.page, parent=self.parent_page)
        self.form = self.form_class(instance=self.page, parent_page=self.parent_page)
        self.has_unsaved_changes = False

        context = self.get_context_data()
        return self.render_to_response(context)

    def get_context_data(self):
        self.edit_handler = self.edit_handler.bind_to(form=self.form)

        return {
            'content_type': self.content_type,
            'page_class': self.page_class,
            'parent_page': self.parent_page,
            'edit_handler': self.edit_handler,
            'action_menu': PageActionMenu(self.request, view='create', parent_page=self.parent_page),
            'preview_modes': self.page.preview_modes,
            'form': self.form,
            'next': self.next_url,
            'has_unsaved_changes': self.has_unsaved_changes,
        }


class EditPageView(TemplateView):
    template_name = 'wagtailadmin/pages/edit.html'

    def get_latest_revision(self):
        return self.real_page_record.get_latest_revision()

    def get_page_instance(self):
        return self.real_page_record.get_latest_revision_as_page()

    def get_edit_handler(self):
        return self.page_class.get_edit_handler()

    def get_form_class(self):
        return self.edit_handler.get_form_class()

    def dispatch(self, request, page_id):
        self.real_page_record = get_object_or_404(Page, id=page_id)
        self.page = self.get_page_instance()

        self.content_type = ContentType.objects.get_for_model(self.page)
        self.page_class = self.content_type.model_class()

        # If there _is_ a custom view registered, and it's a subclass of EditPageView (as expected),
        # we'll end up back here when we call it. We therefore need to set a flag on the request to
        # not repeat the lookup (and end up in an infinite loop)
        if not getattr(request, '_using_custom_edit_page_view', False):
            # check page_class and all its superclasses for an entry in _edit_page_views_by_page_class
            for cls in self.page_class.__mro__:
                try:
                    view = _edit_page_views_by_page_class[cls]
                except KeyError:
                    continue

                request._using_custom_edit_page_view = True
                return view(request, page_id)

        self.latest_revision = self.get_latest_revision()
        self.parent = self.page.get_parent()

        self.page_perms = self.page.permissions_for_user(request.user)
        if not self.page_perms.can_edit():
            raise PermissionDenied

        for fn in hooks.get_hooks('before_edit_page'):
            result = fn(request, self.page)
            if hasattr(result, 'status_code'):
                return result

        self.edit_handler = self.get_edit_handler()
        self.edit_handler = self.edit_handler.bind_to(instance=self.page, request=request)
        self.form_class = self.get_form_class()

        if request.method == 'GET':
            if self.page_perms.user_has_lock():
                if self.page.locked_at:
                    lock_message = format_html(_("<b>Page '{}' was locked</b> by <b>you</b> on <b>{}</b>."), self.page.get_admin_display_title(), self.page.locked_at.strftime("%d %b %Y %H:%M"))
                else:
                    lock_message = format_html(_("<b>Page '{}' is locked</b> by <b>you</b>."), self.page.get_admin_display_title())

                messages.warning(request, lock_message, extra_tags='lock')

            elif self.page_perms.page_locked():
                if self.page.locked_by and self.page.locked_at:
                    lock_message = format_html(_("<b>Page '{}' was locked</b> by <b>{}</b> on <b>{}</b>."), self.page.get_admin_display_title(), str(self.page.locked_by), self.page.locked_at.strftime("%d %b %Y %H:%M"))
                else:
                    # Page was probably locked with an old version of Wagtail, or a script
                    lock_message = format_html(_("<b>Page '{}' is locked</b>."), self.page.get_admin_display_title())

                messages.error(request, lock_message, extra_tags='lock')

        self.next_url = get_valid_next_url_from_request(request)

        self.errors_debug = None

        return super().dispatch(request, page_id)

    def post(self, request, page_id):
        self.form = self.form_class(request.POST, request.FILES, instance=self.page,
                                    parent_page=self.parent)

        if self.form.is_valid() and not self.page_perms.page_locked():
            self.page = self.form.save(commit=False)

            is_publishing = bool(request.POST.get('action-publish')) and self.page_perms.can_publish()
            is_submitting = bool(request.POST.get('action-submit'))
            is_reverting = bool(request.POST.get('revision'))

            # If a revision ID was passed in the form, get that revision so its
            # date can be referenced in notification messages
            if is_reverting:
                previous_revision = get_object_or_404(self.page.revisions, id=request.POST.get('revision'))

            # Save revision
            revision = self.page.save_revision(
                user=request.user,
                submitted_for_moderation=is_submitting,
            )
            # store submitted go_live_at for messaging below
            go_live_at = self.page.go_live_at

            # Publish
            if is_publishing:
                for fn in hooks.get_hooks('before_publish_page'):
                    result = fn(request, self.page)
                    if hasattr(result, 'status_code'):
                        return result

                revision.publish()
                # Need to reload the page because the URL may have changed, and we
                # need the up-to-date URL for the "View Live" button.
                self.page = self.page.specific_class.objects.get(pk=self.page.pk)

                for fn in hooks.get_hooks('after_publish_page'):
                    result = fn(request, self.page)
                    if hasattr(result, 'status_code'):
                        return result

            # Notifications
            if is_publishing:
                if go_live_at and go_live_at > timezone.now():
                    # Page has been scheduled for publishing in the future

                    if is_reverting:
                        message = _(
                            "Revision from {0} of page '{1}' has been scheduled for publishing."
                        ).format(
                            previous_revision.created_at.strftime("%d %b %Y %H:%M"),
                            self.page.get_admin_display_title()
                        )
                    else:
                        if self.page.live:
                            message = _(
                                "Page '{0}' is live and this revision has been scheduled for publishing."
                            ).format(
                                self.page.get_admin_display_title()
                            )
                        else:
                            message = _(
                                "Page '{0}' has been scheduled for publishing."
                            ).format(
                                self.page.get_admin_display_title()
                            )

                    messages.success(request, message, buttons=[
                        messages.button(
                            reverse('wagtailadmin_pages:edit', args=(self.page.id,)),
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
                    buttons.append(
                        messages.button(reverse('wagtailadmin_pages:edit', args=(page_id,)), _('Edit'))
                    )
                    messages.success(request, message, buttons=buttons)

            elif is_submitting:

                message = _(
                    "Page '{0}' has been submitted for moderation."
                ).format(
                    self.page.get_admin_display_title()
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

                if not send_notification(self.page.get_latest_revision().id, 'submitted', request.user.pk):
                    messages.error(request, _("Failed to send notifications to moderators"))

            else:  # Saving

                if is_reverting:
                    message = _(
                        "Page '{0}' has been replaced with revision from {1}."
                    ).format(
                        self.page.get_admin_display_title(),
                        previous_revision.created_at.strftime("%d %b %Y %H:%M")
                    )
                else:
                    message = _(
                        "Page '{0}' has been updated."
                    ).format(
                        self.page.get_admin_display_title()
                    )

                messages.success(request, message)

            for fn in hooks.get_hooks('after_edit_page'):
                result = fn(request, self.page)
                if hasattr(result, 'status_code'):
                    return result

            if is_publishing or is_submitting:
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
                messages.error(request, _("The page could not be saved as it is locked"))
            else:
                messages.validation_error(
                    request, _("The page could not be saved due to validation errors"), self.form
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

            context = self.get_context_data()
            return self.render_to_response(context)

    def get(self, request, page_id):
        self.form = self.form_class(instance=self.page, parent_page=self.parent)
        self.has_unsaved_changes = False

        context = self.get_context_data()
        return self.render_to_response(context)

    def get_context_data(self):
        self.edit_handler = self.edit_handler.bind_to(form=self.form)

        # Check for revisions still undergoing moderation and warn
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
            page_for_status = self.real_page_record.specific
        else:
            page_for_status = self.page

        return {
            'page': self.page,
            'page_for_status': page_for_status,
            'content_type': self.content_type,
            'edit_handler': self.edit_handler,
            'errors_debug': self.errors_debug,
            'action_menu': PageActionMenu(self.request, view='edit', page=self.page),
            'preview_modes': self.page.preview_modes,
            'form': self.form,
            'next': self.next_url,
            'has_unsaved_changes': self.has_unsaved_changes,
            'page_locked': self.page_perms.page_locked(),
        }


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

    return TemplateResponse(request, 'wagtailadmin/pages/confirm_delete.html', {
        'page': page,
        'descendant_count': page.get_descendant_count(),
        'next': next_url,
    })


def view_draft(request, page_id):
    page = get_object_or_404(Page, id=page_id).get_latest_revision_as_page()
    perms = page.permissions_for_user(request.user)
    if not (perms.can_publish() or perms.can_edit()):
        raise PermissionDenied

    try:
        preview_mode = page.default_preview_mode
    except IndexError:
        raise PermissionDenied

    return page.make_preview_request(request, preview_mode)


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
        return TemplateResponse(
            self.request, 'wagtailadmin/pages/preview_error.html',
            {'page': page}
        )

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

        try:
            preview_mode = request.GET.get('mode', page.default_preview_mode)
        except IndexError:
            raise PermissionDenied

        return page.make_preview_request(request, preview_mode)


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

        for fn in hooks.get_hooks('before_unpublish_page'):
            result = fn(request, page)
            if hasattr(result, 'status_code'):
                return result

        page.unpublish()

        if include_descendants:
            live_descendant_pages = page.get_descendants().live().specific()
            for live_descendant_page in live_descendant_pages:
                if user_perms.for_page(live_descendant_page).can_unpublish():
                    live_descendant_page.unpublish()

        for fn in hooks.get_hooks('after_unpublish_page'):
            result = fn(request, page)
            if hasattr(result, 'status_code'):
                return result

        messages.success(request, _("Page '{0}' unpublished.").format(page.get_admin_display_title()), buttons=[
            messages.button(reverse('wagtailadmin_pages:edit', args=(page.id,)), _('Edit'))
        ])

        if next_url:
            return redirect(next_url)
        return redirect('wagtailadmin_explore', page.get_parent().id)

    return TemplateResponse(request, 'wagtailadmin/pages/confirm_unpublish.html', {
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

    return TemplateResponse(request, 'wagtailadmin/pages/move_choose_destination.html', {
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

    return TemplateResponse(request, 'wagtailadmin/pages/confirm_move.html', {
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

    return TemplateResponse(request, 'wagtailadmin/pages/copy.html', {
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
        return TemplateResponse(request, "wagtailadmin/pages/search_results.html", {
            'pages': pages,
            'all_pages': all_pages,
            'query_string': q,
            'content_types': content_types,
            'selected_content_type': selected_content_type,
            'ordering': ordering,
            'pagination_query_params': pagination_query_params.urlencode(),
        })
    else:
        return TemplateResponse(request, "wagtailadmin/pages/search.html", {
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

    try:
        preview_mode = page.default_preview_mode
    except IndexError:
        raise PermissionDenied

    return page.make_preview_request(request, preview_mode, extra_request_attrs={
        'revision_id': revision_id
    })


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
        page.locked_by = request.user
        page.locked_at = timezone.now()
        page.save()

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
    if not page.permissions_for_user(request.user).can_unlock():
        raise PermissionDenied

    # Unlock the page
    if page.locked:
        page.locked = False
        page.locked_by = None
        page.locked_at = None
        page.save()

        messages.success(request, _("Page '{0}' is now unlocked.").format(page.get_admin_display_title()), extra_tags='unlock')

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

    return TemplateResponse(request, 'wagtailadmin/pages/revisions/index.html', {
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

    return TemplateResponse(request, 'wagtailadmin/pages/edit.html', {
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

    perms = page.permissions_for_user(request.user)
    if not (perms.can_publish() or perms.can_edit()):
        raise PermissionDenied

    revision = get_object_or_404(page.revisions, id=revision_id)
    revision_page = revision.as_page_object()

    try:
        preview_mode = page.default_preview_mode
    except IndexError:
        raise PermissionDenied

    return revision_page.make_preview_request(request, preview_mode)


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

    return TemplateResponse(request, 'wagtailadmin/pages/revisions/compare.html', {
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

    return TemplateResponse(request, 'wagtailadmin/pages/revisions/confirm_unschedule.html', {
        'page': page,
        'revision': revision,
        'next': next_url,
        'subtitle': subtitle
    })
