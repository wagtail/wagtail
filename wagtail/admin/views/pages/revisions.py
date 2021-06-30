from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _

from wagtail.admin import messages
from wagtail.admin.action_menu import PageActionMenu
from wagtail.admin.auth import user_has_any_page_permission, user_passes_test
from wagtail.admin.views.pages.utils import get_valid_next_url_from_request
from wagtail.core.models import Page, UserPagePermissionsProxy


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
        _("You are viewing a previous version of this page from <b>%(created_at)s</b> by %(user)s") % {
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


@user_passes_test(user_has_any_page_permission)
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

    comparison = page.get_edit_handler().bind_to(instance=page, request=request).get_comparison()
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
        revision.save(user=request.user, update_fields=['approved_go_live_at'])

        messages.success(request, _('Version {0} of "{1}" unscheduled.').format(revision.id, page.get_admin_display_title()), buttons=[
            messages.button(reverse('wagtailadmin_pages:edit', args=(page.id,)), _('Edit'))
        ])

        if next_url:
            return redirect(next_url)
        return redirect('wagtailadmin_pages:history', page.id)

    return TemplateResponse(request, 'wagtailadmin/pages/revisions/confirm_unschedule.html', {
        'page': page,
        'revision': revision,
        'next': next_url,
        'subtitle': subtitle
    })
