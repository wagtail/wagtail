import warnings

from django.http import Http404, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import ValidationError, PermissionDenied
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.decorators import permission_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import timezone
from django.utils.translation import ugettext as _
from django.utils.http import is_safe_url
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.vary import vary_on_headers
from django.db.models import Count

from wagtail.wagtailadmin.edit_handlers import TabbedInterface, ObjectList
from wagtail.wagtailadmin.forms import SearchForm, CopyForm
from wagtail.wagtailadmin import tasks, signals

from wagtail.wagtailcore import hooks
from wagtail.wagtailcore.models import Page, PageRevision, get_navigation_menu_items


@permission_required('wagtailadmin.access_admin')
def explorer_nav(request):
    return render(request, 'wagtailadmin/shared/explorer_nav.html', {
        'nodes': get_navigation_menu_items(),
    })


@permission_required('wagtailadmin.access_admin')
def index(request, parent_page_id=None):
    if parent_page_id:
        parent_page = get_object_or_404(Page, id=parent_page_id)
    else:
        parent_page = Page.get_first_root_node()

    pages = parent_page.get_children().prefetch_related('content_type')

    # Get page ordering
    ordering = request.GET.get('ordering', '-latest_revision_created_at')
    if ordering not in ['title', '-title', 'content_type', '-content_type', 'live', '-live', 'latest_revision_created_at', '-latest_revision_created_at', 'ord']:
        ordering = '-latest_revision_created_at'

    # Pagination
    if ordering != 'ord':
        ordering_no_minus = ordering
        if ordering_no_minus.startswith('-'):
            ordering_no_minus = ordering[1:]
        pages = pages.order_by(ordering).annotate(null_position=Count(ordering_no_minus)).order_by('-null_position', ordering)

        p = request.GET.get('p', 1)
        paginator = Paginator(pages, 50)
        try:
            pages = paginator.page(p)
        except PageNotAnInteger:
            pages = paginator.page(1)
        except EmptyPage:
            pages = paginator.page(paginator.num_pages)

    return render(request, 'wagtailadmin/pages/index.html', {
        'parent_page': parent_page,
        'ordering': ordering,
        'pages': pages,
    })


@permission_required('wagtailadmin.access_admin')
def add_subpage(request, parent_page_id):
    parent_page = get_object_or_404(Page, id=parent_page_id).specific
    if not parent_page.permissions_for_user(request.user).can_add_subpage():
        raise PermissionDenied

    page_types = sorted(parent_page.allowed_subpage_types(),
        key=lambda pagetype: pagetype.model_class().get_verbose_name().lower()
    )

    if len(page_types) == 1:
        # Only one page type is available - redirect straight to the create form rather than
        # making the user choose
        content_type = page_types[0]
        return redirect('wagtailadmin_pages_create', content_type.app_label, content_type.model, parent_page.id)

    return render(request, 'wagtailadmin/pages/add_subpage.html', {
        'parent_page': parent_page,
        'page_types': page_types,
    })


@permission_required('wagtailadmin.access_admin')
def content_type_use(request, content_type_app_name, content_type_model_name):
    try:
        content_type = ContentType.objects.get_by_natural_key(content_type_app_name, content_type_model_name)
    except ContentType.DoesNotExist:
        raise Http404

    p = request.GET.get("p", 1)

    page_class = content_type.model_class()

    # page_class must be a Page type and not some other random model
    if not issubclass(page_class, Page):
        raise Http404

    pages = page_class.objects.all()

    paginator = Paginator(pages, 10)

    try:
        pages = paginator.page(p)
    except PageNotAnInteger:
        pages = paginator.page(1)
    except EmptyPage:
        pages = paginator.page(paginator.num_pages)

    return render(request, 'wagtailadmin/pages/content_type_use.html', {
        'pages': pages,
        'app_name': content_type_app_name,
        'content_type': content_type,
        'page_class': page_class,
    })


@permission_required('wagtailadmin.access_admin')
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
    if content_type not in parent_page.allowed_subpage_types():
        raise PermissionDenied

    page = page_class(owner=request.user)
    edit_handler_class = get_page_edit_handler(page_class)
    form_class = edit_handler_class.get_form_class(page_class)

    if request.POST:
        form = form_class(request.POST, request.FILES, instance=page)

        # Stick an extra validator into the form to make sure that the slug is not already in use
        def clean_slug(slug):
            # Make sure the slug isn't already in use
            if parent_page.get_children().filter(slug=slug).count() > 0:
                raise ValidationError(_("This slug is already in use"))
            return slug
        form.fields['slug'].clean = clean_slug

        # Stick another validator into the form to check that the scheduled publishing settings are set correctly
        def clean():
            cleaned_data = form_class.clean(form)

            # Go live must be before expire
            go_live_at = cleaned_data.get('go_live_at')
            expire_at = cleaned_data.get('expire_at')

            if go_live_at and expire_at:
                if go_live_at > expire_at:
                    msg = _('Go live date/time must be before expiry date/time')
                    form._errors['go_live_at'] = form.error_class([msg])
                    form._errors['expire_at'] = form.error_class([msg])
                    del cleaned_data['go_live_at']
                    del cleaned_data['expire_at']

            # Expire must be in the future
            expire_at = cleaned_data.get('expire_at')

            if expire_at and expire_at < timezone.now():
                form._errors['expire_at'] = form.error_class([_('Expiry date/time must be in the future')])
                del cleaned_data['expire_at']

            return cleaned_data
        form.clean = clean

        if form.is_valid():
            page = form.save(commit=False)

            is_publishing = bool(request.POST.get('action-publish')) and parent_page_perms.can_publish_subpage()
            is_submitting = bool(request.POST.get('action-submit'))

            # Set live to False and has_unpublished_changes to True if we are not publishing
            if not is_publishing:
                page.live = False
                page.has_unpublished_changes = True

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
                messages.success(request, _("Page '{0}' published.").format(page.title))
            elif is_submitting:
                messages.success(request, _("Page '{0}' submitted for moderation.").format(page.title))
                tasks.send_notification.delay(page.get_latest_revision().id, 'submitted', request.user.id)
            else:
                messages.success(request, _("Page '{0}' created.").format(page.title))

            for fn in hooks.get_hooks('after_create_page'):
                result = fn(request, page)
                if hasattr(result, 'status_code'):
                    return result

            if is_publishing or is_submitting:
                # we're done here - redirect back to the explorer
                return redirect('wagtailadmin_explore', page.get_parent().id)
            else:
                # Just saving - remain on edit page for further edits
                return redirect('wagtailadmin_pages_edit', page.id)
        else:
            messages.error(request, _("The page could not be created due to validation errors"))
            edit_handler = edit_handler_class(instance=page, form=form)
    else:
        signals.init_new_page.send(sender=create, page=page, parent=parent_page)
        form = form_class(instance=page)
        edit_handler = edit_handler_class(instance=page, form=form)

    return render(request, 'wagtailadmin/pages/create.html', {
        'content_type': content_type,
        'page_class': page_class,
        'parent_page': parent_page,
        'edit_handler': edit_handler,
        'preview_modes': page.preview_modes,
        'form': form, # Used in unit tests
    })


@permission_required('wagtailadmin.access_admin')
def edit(request, page_id):
    latest_revision = get_object_or_404(Page, id=page_id).get_latest_revision()
    page = get_object_or_404(Page, id=page_id).get_latest_revision_as_page()
    parent = page.get_parent()

    page_perms = page.permissions_for_user(request.user)
    if not page_perms.can_edit():
        raise PermissionDenied

    edit_handler_class = get_page_edit_handler(page.__class__)
    form_class = edit_handler_class.get_form_class(page.__class__)

    errors_debug = None

    if request.POST:
        form = form_class(request.POST, request.FILES, instance=page)

        # Stick an extra validator into the form to make sure that the slug is not already in use
        def clean_slug(slug):
            # Make sure the slug isn't already in use
            if parent.get_children().filter(slug=slug).exclude(id=page_id).count() > 0:
                raise ValidationError(_("This slug is already in use"))
            return slug
        form.fields['slug'].clean = clean_slug

        # Stick another validator into the form to check that the scheduled publishing settings are set correctly
        def clean():
            cleaned_data = form_class.clean(form)

            # Go live must be before expire
            go_live_at = cleaned_data.get('go_live_at')
            expire_at = cleaned_data.get('expire_at')

            if go_live_at and expire_at:
                if go_live_at > expire_at:
                    msg = _('Go live date/time must be before expiry date/time')
                    form._errors['go_live_at'] = form.error_class([msg])
                    form._errors['expire_at'] = form.error_class([msg])
                    del cleaned_data['go_live_at']
                    del cleaned_data['expire_at']

            # Expire must be in the future
            expire_at = cleaned_data.get('expire_at')

            if expire_at and expire_at < timezone.now():
                form._errors['expire_at'] = form.error_class([_('Expiry date/time must be in the future')])
                del cleaned_data['expire_at']

            return cleaned_data
        form.clean = clean

        if form.is_valid() and not page.locked:
            page = form.save(commit=False)

            is_publishing = bool(request.POST.get('action-publish')) and page_perms.can_publish()
            is_submitting = bool(request.POST.get('action-submit'))

            # Save revision
            revision = page.save_revision(
                user=request.user,
                submitted_for_moderation=is_submitting,
            )

            # Publish
            if is_publishing:
                revision.publish()
            else:
                # Set has_unpublished_changes flag
                if page.live:
                    # To avoid overwriting the live version, we only save the page
                    # to the revisions table
                    Page.objects.filter(id=page.id).update(has_unpublished_changes=True)
                else:
                    page.has_unpublished_changes = True
                    page.save()

            # Notifications
            if is_publishing:
                messages.success(request, _("Page '{0}' published.").format(page.title))
            elif is_submitting:
                messages.success(request, _("Page '{0}' submitted for moderation.").format(page.title))
                tasks.send_notification.delay(page.get_latest_revision().id, 'submitted', request.user.id)
            else:
                messages.success(request, _("Page '{0}' updated.").format(page.title))

            for fn in hooks.get_hooks('after_edit_page'):
                result = fn(request, page)
                if hasattr(result, 'status_code'):
                    return result

            if is_publishing or is_submitting:
                # we're done here - redirect back to the explorer
                return redirect('wagtailadmin_explore', page.get_parent().id)
            else:
                # Just saving - remain on edit page for further edits
                return redirect('wagtailadmin_pages_edit', page.id)
        else:
            if page.locked:
                messages.error(request, _("The page could not be saved as it is locked"))
            else:
                messages.error(request, _("The page could not be saved due to validation errors"))

            edit_handler = edit_handler_class(instance=page, form=form)
            errors_debug = (
                repr(edit_handler.form.errors)
                + repr([(name, formset.errors) for (name, formset) in edit_handler.form.formsets.items() if formset.errors])
            )
    else:
        form = form_class(instance=page)
        edit_handler = edit_handler_class(instance=page, form=form)

    # Check for revisions still undergoing moderation and warn
    if latest_revision and latest_revision.submitted_for_moderation:
        messages.warning(request, _("This page is currently awaiting moderation"))

    return render(request, 'wagtailadmin/pages/edit.html', {
        'page': page,
        'edit_handler': edit_handler,
        'errors_debug': errors_debug,
        'preview_modes': page.preview_modes,
        'form': form, # Used in unit tests
    })


@permission_required('wagtailadmin.access_admin')
def delete(request, page_id):
    page = get_object_or_404(Page, id=page_id).specific
    if not page.permissions_for_user(request.user).can_delete():
        raise PermissionDenied

    if request.POST:
        parent_id = page.get_parent().id
        page.delete()

        messages.success(request, _("Page '{0}' deleted.").format(page.title))

        for fn in hooks.get_hooks('after_delete_page'):
            result = fn(request, page)
            if hasattr(result, 'status_code'):
                return result

        return redirect('wagtailadmin_explore', parent_id)

    return render(request, 'wagtailadmin/pages/confirm_delete.html', {
        'page': page,
        'descendant_count': page.get_descendant_count()
    })


@permission_required('wagtailadmin.access_admin')
def view_draft(request, page_id):
    page = get_object_or_404(Page, id=page_id).get_latest_revision_as_page()
    return page.serve_preview(page.dummy_request(), page.default_preview_mode)


@permission_required('wagtailadmin.access_admin')
def preview_on_edit(request, page_id):
    # Receive the form submission that would typically be posted to the 'edit' view. If submission is valid,
    # return the rendered page; if not, re-render the edit form
    page = get_object_or_404(Page, id=page_id).get_latest_revision_as_page()
    edit_handler_class = get_page_edit_handler(page.__class__)
    form_class = edit_handler_class.get_form_class(page.__class__)

    form = form_class(request.POST, request.FILES, instance=page)

    if form.is_valid():
        form.save(commit=False)

        preview_mode = request.GET.get('mode', page.default_preview_mode)
        response = page.serve_preview(page.dummy_request(), preview_mode)
        response['X-Wagtail-Preview'] = 'ok'
        return response

    else:
        edit_handler = edit_handler_class(instance=page, form=form)

        response = render(request, 'wagtailadmin/pages/edit.html', {
            'page': page,
            'edit_handler': edit_handler,
            'preview_modes': page.preview_modes,
        })
        response['X-Wagtail-Preview'] = 'error'
        return response


@permission_required('wagtailadmin.access_admin')
def preview_on_create(request, content_type_app_name, content_type_model_name, parent_page_id):
    # Receive the form submission that would typically be posted to the 'create' view. If submission is valid,
    # return the rendered page; if not, re-render the edit form
    try:
        content_type = ContentType.objects.get_by_natural_key(content_type_app_name, content_type_model_name)
    except ContentType.DoesNotExist:
        raise Http404

    page_class = content_type.model_class()
    page = page_class()
    edit_handler_class = get_page_edit_handler(page_class)
    form_class = edit_handler_class.get_form_class(page_class)

    form = form_class(request.POST, request.FILES, instance=page)

    if form.is_valid():
        form.save(commit=False)

        # ensure that our unsaved page instance has a suitable url set
        parent_page = get_object_or_404(Page, id=parent_page_id).specific
        page.set_url_path(parent_page)

        # Set treebeard attributes
        page.depth = parent_page.depth + 1
        page.path = Page._get_children_path_interval(parent_page.path)[1]

        preview_mode = request.GET.get('mode', page.default_preview_mode)
        response = page.serve_preview(page.dummy_request(), preview_mode)
        response['X-Wagtail-Preview'] = 'ok'
        return response

    else:
        edit_handler = edit_handler_class(instance=page, form=form)
        parent_page = get_object_or_404(Page, id=parent_page_id).specific

        response = render(request, 'wagtailadmin/pages/create.html', {
            'content_type': content_type,
            'page_class': page_class,
            'parent_page': parent_page,
            'edit_handler': edit_handler,
            'preview_modes': page.preview_modes,
        })
        response['X-Wagtail-Preview'] = 'error'
        return response


def preview(request):
    """
    The HTML of a previewed page is written to the destination browser window using document.write.
    This overwrites any previous content in the window, while keeping its URL intact. This in turn
    means that any content we insert that happens to trigger an HTTP request, such as an image or
    stylesheet tag, will report that original URL as its referrer.

    In Webkit browsers, a new window opened with window.open('', 'window_name') will have a location
    of 'about:blank', causing it to omit the Referer header on those HTTP requests. This means that
    any third-party font services that use the Referer header for access control will refuse to
    serve us.

    So, instead, we need to open the window on some arbitrary URL on our domain. (Provided that's
    also the same domain as our editor JS code, the browser security model will happily allow us to
    document.write over the page in question.)

    This, my friends, is that arbitrary URL.

    Since we're going to this trouble, we'll also take the opportunity to display a spinner on the
    placeholder page, providing some much-needed visual feedback.
    """
    return render(request, 'wagtailadmin/pages/preview.html')

def preview_loading(request):
    """
    This page is blank, but must be real HTML so its DOM can be written to once the preview of the page has rendered
    """
    return HttpResponse("<html><head><title></title></head><body></body></html>")

@permission_required('wagtailadmin.access_admin')
def unpublish(request, page_id):
    page = get_object_or_404(Page, id=page_id).specific
    if not page.permissions_for_user(request.user).can_unpublish():
        raise PermissionDenied

    if request.method == 'POST':
        page.unpublish()

        messages.success(request, _("Page '{0}' unpublished.").format(page.title))

        return redirect('wagtailadmin_explore', page.get_parent().id)

    return render(request, 'wagtailadmin/pages/confirm_unpublish.html', {
        'page': page,
    })


@permission_required('wagtailadmin.access_admin')
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

        target.can_descend = not(target == page_to_move or target.is_child_of(page_to_move)) and target.get_children_count()

        child_pages.append(target)

    return render(request, 'wagtailadmin/pages/move_choose_destination.html', {
        'page_to_move': page_to_move,
        'viewed_page': viewed_page,
        'child_pages': child_pages,
    })


@permission_required('wagtailadmin.access_admin')
def move_confirm(request, page_to_move_id, destination_id):
    page_to_move = get_object_or_404(Page, id=page_to_move_id).specific
    destination = get_object_or_404(Page, id=destination_id)
    if not page_to_move.permissions_for_user(request.user).can_move_to(destination):
        raise PermissionDenied

    if request.POST:
        # any invalid moves *should* be caught by the permission check above,
        # so don't bother to catch InvalidMoveToDescendant

        page_to_move.move(destination, pos='last-child')

        messages.success(request, _("Page '{0}' moved.").format(page_to_move.title))
        return redirect('wagtailadmin_explore', destination.id)

    return render(request, 'wagtailadmin/pages/confirm_move.html', {
        'page_to_move': page_to_move,
        'destination': destination,
    })


@permission_required('wagtailadmin.access_admin')
def set_page_position(request, page_to_move_id):
    page_to_move = get_object_or_404(Page, id=page_to_move_id)
    parent_page = page_to_move.get_parent()

    if not parent_page.permissions_for_user(request.user).can_reorder_children():
        raise PermissionDenied

    if request.POST:
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


@permission_required('wagtailadmin.access_admin')
def copy(request, page_id):
    page = Page.objects.get(id=page_id)
    parent_page = page.get_parent()

    # Make sure this user has permission to add subpages on the parent
    if not parent_page.permissions_for_user(request.user).can_add_subpage():
        raise PermissionDenied

    # Check if the user has permission to publish subpages on the parent
    can_publish = parent_page.permissions_for_user(request.user).can_publish_subpage()

    # Create the form
    form = CopyForm(request.POST or None, page=page, can_publish=can_publish)

    # Check if user is submitting
    if request.method == 'POST' and form.is_valid():
        # Copy the page
        new_page = page.copy(
            recursive=form.cleaned_data.get('copy_subpages'),
            update_attrs={
                'title': form.cleaned_data['new_title'],
                'slug': form.cleaned_data['new_slug'],
            },
            keep_live=(can_publish and form.cleaned_data.get('publish_copies')),
            user=request.user,
        )

        # Give a success message back to the user
        if form.cleaned_data.get('copy_subpages'):
            messages.success(request, _("Page '{0}' and {1} subpages copied.").format(page.title, new_page.get_descendants().count()))
        else:
            messages.success(request, _("Page '{0}' copied.").format(page.title))

        # Redirect to explore of parent page
        return redirect('wagtailadmin_explore', parent_page.id)

    return render(request, 'wagtailadmin/pages/copy.html', {
        'page': page,
        'form': form,
    })


PAGE_EDIT_HANDLERS = {}


def get_page_edit_handler(page_class):
    if page_class not in PAGE_EDIT_HANDLERS:
        PAGE_EDIT_HANDLERS[page_class] = TabbedInterface([
            ObjectList(page_class.content_panels, heading='Content'),
            ObjectList(page_class.promote_panels, heading='Promote'),
            ObjectList(page_class.settings_panels, heading='Settings', classname="settings")
        ])

    return PAGE_EDIT_HANDLERS[page_class]


@permission_required('wagtailadmin.access_admin')
@vary_on_headers('X-Requested-With')
def search(request):
    pages = []
    q = None
    is_searching = False
    if 'q' in request.GET:
        form = SearchForm(request.GET)
        if form.is_valid():
            q = form.cleaned_data['q']

            # page number
            p = request.GET.get("p", 1)
            is_searching = True
            pages = Page.search(q, show_unpublished=True, search_title_only=True, prefetch_related=['content_type'])

            # Pagination
            paginator = Paginator(pages, 20)
            try:
                pages = paginator.page(p)
            except PageNotAnInteger:
                pages = paginator.page(1)
            except EmptyPage:
                pages = paginator.page(paginator.num_pages)
    else:
        form = SearchForm()

    if request.is_ajax():
        return render(request, "wagtailadmin/pages/search_results.html", {
            'pages': pages,
            'is_searching': is_searching,
            'query_string': q,
        })
    else:
        return render(request, "wagtailadmin/pages/search.html", {
            'search_form': form,
            'pages': pages,
            'is_searching': is_searching,
            'query_string': q,
        })


@permission_required('wagtailadmin.access_admin')
def approve_moderation(request, revision_id):
    revision = get_object_or_404(PageRevision, id=revision_id)
    if not revision.page.permissions_for_user(request.user).can_publish():
        raise PermissionDenied

    if not revision.submitted_for_moderation:
        messages.error(request, _("The page '{0}' is not currently awaiting moderation.").format(revision.page.title))
        return redirect('wagtailadmin_home')

    if request.method == 'POST':
        revision.approve_moderation()
        messages.success(request, _("Page '{0}' published.").format(revision.page.title))
        tasks.send_notification.delay(revision.id, 'approved', request.user.id)

    return redirect('wagtailadmin_home')


@permission_required('wagtailadmin.access_admin')
def reject_moderation(request, revision_id):
    revision = get_object_or_404(PageRevision, id=revision_id)
    if not revision.page.permissions_for_user(request.user).can_publish():
        raise PermissionDenied

    if not revision.submitted_for_moderation:
        messages.error(request, _("The page '{0}' is not currently awaiting moderation.").format( revision.page.title))
        return redirect('wagtailadmin_home')

    if request.method == 'POST':
        revision.reject_moderation()
        messages.success(request, _("Page '{0}' rejected for publication.").format(revision.page.title))
        tasks.send_notification.delay(revision.id, 'rejected', request.user.id)

    return redirect('wagtailadmin_home')


@permission_required('wagtailadmin.access_admin')
@require_GET
def preview_for_moderation(request, revision_id):
    revision = get_object_or_404(PageRevision, id=revision_id)
    if not revision.page.permissions_for_user(request.user).can_publish():
        raise PermissionDenied

    if not revision.submitted_for_moderation:
        messages.error(request, _("The page '{0}' is not currently awaiting moderation.").format(revision.page.title))
        return redirect('wagtailadmin_home')

    page = revision.as_page_object()

    request.revision_id = revision_id

    # pass in the real user request rather than page.dummy_request(), so that request.user
    # and request.revision_id will be picked up by the wagtail user bar
    return page.serve_preview(request, page.default_preview_mode)


@permission_required('wagtailadmin.access_admin')
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

        messages.success(request, _("Page '{0}' is now locked.").format(page.title))

    # Redirect
    redirect_to = request.POST.get('next', None)
    if redirect_to and is_safe_url(url=redirect_to, host=request.get_host()):
        return redirect(redirect_to)
    else:
        return redirect('wagtailadmin_explore', page.get_parent().id)


@permission_required('wagtailadmin.access_admin')
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

        messages.success(request, _("Page '{0}' is now unlocked.").format(page.title))

    # Redirect
    redirect_to = request.POST.get('next', None)
    if redirect_to and is_safe_url(url=redirect_to, host=request.get_host()):
        return redirect(redirect_to)
    else:
        return redirect('wagtailadmin_explore', page.get_parent().id)
