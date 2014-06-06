from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import permission_required
from django.shortcuts import get_object_or_404

from wagtail.wagtailcore.models import Page
from wagtail.wagtailadmin.modal_workflow import render_modal_workflow

@permission_required('wagtailadmin.access_admin')
def set_view_restrictions(request, page_id):
    page = get_object_or_404(Page, id=page_id)
    page_perms = page.permissions_for_user(request.user)
    if not page_perms.can_set_view_restrictions():
        raise PermissionDenied

    restrictions = page.get_view_restrictions().order_by('page__depth')
    if restrictions:
        if restrictions[0].page == page:
            # a restriction is set on this specific page, and no restrictions
            # further up the tree exist
            return render_modal_workflow(
                request, 'wagtailadmin/page_view_restrictions/set_view_restrictions.html', None, {}
            )
        else:
            # a restriction further up the tree exists
            return render_modal_workflow(
                request, 'wagtailadmin/page_view_restrictions/ancestor_restriction.html', None,
                {
                    'page_with_restriction': restrictions[0].page,
                }
            )
    else:
        # no current view restrictions on this page
        return render_modal_workflow(
            request, 'wagtailadmin/page_view_restrictions/set_view_restrictions.html', None, {}
        )
