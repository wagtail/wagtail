from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from wagtail.admin.forms.pages import PageViewRestrictionForm
from wagtail.admin.modal_workflow import render_modal_workflow
from wagtail.core.models import Page, PageViewRestriction


def set_privacy(request, page_id):
    page = get_object_or_404(Page, id=page_id)
    page_perms = page.permissions_for_user(request.user)
    if not page_perms.can_set_view_restrictions():
        raise PermissionDenied

    # fetch restriction records in depth order so that ancestors appear first
    restrictions = page.get_view_restrictions().order_by('page__depth')
    if restrictions:
        restriction = restrictions[0]
        restriction_exists_on_ancestor = (restriction.page != page)
    else:
        restriction = None
        restriction_exists_on_ancestor = False

    if request.method == 'POST':
        form = PageViewRestrictionForm(request.POST, instance=restriction)
        if form.is_valid() and not restriction_exists_on_ancestor:
            if form.cleaned_data['restriction_type'] == PageViewRestriction.NONE:
                # remove any existing restriction
                if restriction:
                    restriction.delete(user=request.user)
            else:
                restriction = form.save(commit=False)
                restriction.page = page
                restriction.save(user=request.user)
                # Save the groups many-to-many field
                form.save_m2m()

            return render_modal_workflow(
                request, None, None,
                None, json_data={
                    'step': 'set_privacy_done',
                    'is_public': (form.cleaned_data['restriction_type'] == 'none')
                }
            )

    else:  # request is a GET
        if not restriction_exists_on_ancestor:
            if restriction:
                form = PageViewRestrictionForm(instance=restriction)
            else:
                # no current view restrictions on this page
                form = PageViewRestrictionForm(initial={
                    'restriction_type': 'none'
                })

    if restriction_exists_on_ancestor:
        # display a message indicating that there is a restriction at ancestor level -
        # do not provide the form for setting up new restrictions
        return render_modal_workflow(
            request, 'wagtailadmin/page_privacy/ancestor_privacy.html', None,
            {
                'page_with_restriction': restriction.page,
            }
        )
    else:
        # no restriction set at ancestor level - can set restrictions here
        return render_modal_workflow(
            request, 'wagtailadmin/page_privacy/set_privacy.html', None, {
                'page': page,
                'form': form,
            }, json_data={'step': 'set_privacy'}
        )
