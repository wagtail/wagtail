from django.http import Http404, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import ValidationError, PermissionDenied
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.decorators import permission_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils.translation import ugettext as _
from django.views.decorators.vary import vary_on_headers

from wagtail.wagtailadmin.edit_handlers import TabbedInterface, ObjectList
from wagtail.wagtailadmin.forms import SearchForm
from wagtail.wagtailadmin import tasks, hooks

from wagtail.wagtailcore.models import Page, PageRevision


@permission_required('wagtailadmin.access_admin')
def index(request, parent_page_id=None):
    if parent_page_id:
        parent_page = get_object_or_404(Page, id=parent_page_id)
    else:
        parent_page = Page.get_first_root_node()

    pages = parent_page.get_children().prefetch_related('content_type')

    # Get page ordering
    if 'ordering' in request.GET:
        ordering = request.GET['ordering']

        if ordering in ['title', '-title', 'content_type', '-content_type', 'live', '-live']:
            pages = pages.order_by(ordering)
    else:
        ordering = 'title'

    # Pagination
    if ordering != 'ord':
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

    page_types = sorted(parent_page.clean_subpage_types(), key=lambda pagetype: pagetype.name.lower())

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

    # page must be in the list of allowed subpage types for this parent ID
    if content_type not in parent_page.clean_subpage_types():
        raise PermissionDenied

    page_class = content_type.model_class()

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

        if form.is_valid():
            page = form.save(commit=False)  # don't save yet, as we need treebeard to assign tree params

            is_publishing = bool(request.POST.get('action-publish')) and parent_page_perms.can_publish_subpage()
            is_submitting = bool(request.POST.get('action-submit'))

            if is_publishing:
                page.live = True
                page.has_unpublished_changes = False
            else:
                page.live = False
                page.has_unpublished_changes = True

            parent_page.add_child(instance=page)  # assign tree parameters - will cause page to be saved
            page.save_revision(user=request.user, submitted_for_moderation=is_submitting)

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

            return redirect('wagtailadmin_explore', page.get_parent().id)
        else:
            messages.error(request, _("The page could not be created due to errors."))
            edit_handler = edit_handler_class(instance=page, form=form)
    else:
        form = form_class(instance=page)
        edit_handler = edit_handler_class(instance=page, form=form)

    return render(request, 'wagtailadmin/pages/create.html', {
        'content_type': content_type,
        'page_class': page_class,
        'parent_page': parent_page,
        'edit_handler': edit_handler,
        'display_modes': page.get_page_modes(),
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

        if form.is_valid():
            is_publishing = bool(request.POST.get('action-publish')) and page_perms.can_publish()
            is_submitting = bool(request.POST.get('action-submit'))

            if is_publishing:
                page.live = True
                page.has_unpublished_changes = False
                form.save()
                page.revisions.update(submitted_for_moderation=False)
            else:
                # not publishing the page
                if page.live:
                    # To avoid overwriting the live version, we only save the page
                    # to the revisions table
                    form.save(commit=False)
                    Page.objects.filter(id=page.id).update(has_unpublished_changes=True)
                else:
                    page.has_unpublished_changes = True
                    form.save()

            page.save_revision(user=request.user, submitted_for_moderation=is_submitting)

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

            return redirect('wagtailadmin_explore', page.get_parent().id)
        else:
            messages.error(request, _("The page could not be saved due to validation errors"))
            edit_handler = edit_handler_class(instance=page, form=form)
            errors_debug = (
                repr(edit_handler.form.errors)
                + repr([(name, formset.errors) for (name, formset) in edit_handler.form.formsets.iteritems() if formset.errors])
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
        'display_modes': page.get_page_modes(),
    })


@permission_required('wagtailadmin.access_admin')
def delete(request, page_id):
    page = get_object_or_404(Page, id=page_id)
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
    return page.serve(request)


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

        # This view will generally be invoked as an AJAX request; as such, in the case of
        # an error Django will return a plaintext response. This isn't what we want, since
        # we will be writing the response back to an HTML page regardless of success or
        # failure - as such, we strip out the X-Requested-With header to get Django to return
        # an HTML error response
        request.META.pop('HTTP_X_REQUESTED_WITH', None)

        try:
            display_mode = request.GET['mode']
        except KeyError:
            display_mode = page.get_page_modes()[0][0]

        response = page.show_as_mode(display_mode)

        response['X-Wagtail-Preview'] = 'ok'
        return response

    else:
        edit_handler = edit_handler_class(instance=page, form=form)

        response = render(request, 'wagtailadmin/pages/edit.html', {
            'page': page,
            'edit_handler': edit_handler,
            'display_modes': page.get_page_modes(),
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

        # This view will generally be invoked as an AJAX request; as such, in the case of
        # an error Django will return a plaintext response. This isn't what we want, since
        # we will be writing the response back to an HTML page regardless of success or
        # failure - as such, we strip out the X-Requested-With header to get Django to return
        # an HTML error response
        request.META.pop('HTTP_X_REQUESTED_WITH', None)

        try:
            display_mode = request.GET['mode']
        except KeyError:
            display_mode = page.get_page_modes()[0][0]
        response = page.show_as_mode(display_mode)

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
            'display_modes': page.get_page_modes(),
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
    page = get_object_or_404(Page, id=page_id)
    if not page.permissions_for_user(request.user).can_unpublish():
        raise PermissionDenied

    if request.POST:
        parent_id = page.get_parent().id
        page.live = False
        page.save()
        messages.success(request, _("Page '{0}' unpublished.").format(page.title))
        return redirect('wagtailadmin_explore', parent_id)

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
    page_to_move = get_object_or_404(Page, id=page_to_move_id)
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
            # Move page into this position
            page_to_move.move(position_page, pos='left')
        else:
            # Move page to end
            page_to_move.move(parent_page, pos='last-child')

    return HttpResponse('')


PAGE_EDIT_HANDLERS = {}


def get_page_edit_handler(page_class):
    if page_class not in PAGE_EDIT_HANDLERS:
        PAGE_EDIT_HANDLERS[page_class] = TabbedInterface([
            ObjectList(page_class.content_panels, heading='Content'),
            ObjectList(page_class.promote_panels, heading='Promote')
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

    if request.POST:
        revision.publish()
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

    if request.POST:
        revision.submitted_for_moderation = False
        revision.save(update_fields=['submitted_for_moderation'])
        messages.success(request, _("Page '{0}' rejected for publication.").format(revision.page.title))
        tasks.send_notification.delay(revision.id, 'rejected', request.user.id)

    return redirect('wagtailadmin_home')


@permission_required('wagtailadmin.access_admin')
def preview_for_moderation(request, revision_id):
    revision = get_object_or_404(PageRevision, id=revision_id)
    if not revision.page.permissions_for_user(request.user).can_publish():
        raise PermissionDenied

    if not revision.submitted_for_moderation:
        messages.error(request, _("The page '{0}' is not currently awaiting moderation.").format(revision.page.title))
        return redirect('wagtailadmin_home')

    page = revision.as_page_object()

    request.revision_id = revision_id

    return page.serve(request)
