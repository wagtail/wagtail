from __future__ import absolute_import, unicode_literals

from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from wagtail.wagtailadmin.forms import CollectionViewRestrictionForm
from wagtail.wagtailadmin.modal_workflow import render_modal_workflow
from wagtail.wagtailcore.models import Collection, CollectionViewRestriction
from wagtail.wagtailcore.permissions import collection_permission_policy


def set_privacy(request, collection_id):
    collection = get_object_or_404(Collection, id=collection_id)
    if not collection_permission_policy.user_has_permission(request.user, 'change'):
        raise PermissionDenied

    # fetch restriction records in depth order so that ancestors appear first
    restrictions = collection.get_view_restrictions().order_by('collection__depth')
    if restrictions:
        restriction = restrictions[0]
        restriction_exists_on_ancestor = (restriction.collection != collection)
    else:
        restriction = None
        restriction_exists_on_ancestor = False

    if request.method == 'POST':
        form = CollectionViewRestrictionForm(request.POST, instance=restriction)
        if form.is_valid() and not restriction_exists_on_ancestor:
            if form.cleaned_data['restriction_type'] == CollectionViewRestriction.NONE:
                # remove any existing restriction
                if restriction:
                    restriction.delete()
            else:
                restriction = form.save(commit=False)
                restriction.collection = collection
                form.save()

            return render_modal_workflow(
                request, None, 'wagtailadmin/collection_privacy/set_privacy_done.js', {
                    'is_public': (form.cleaned_data['restriction_type'] == 'none')
                }
            )

    else:  # request is a GET
        if not restriction_exists_on_ancestor:
            if restriction:
                form = CollectionViewRestrictionForm(instance=restriction)
            else:
                # no current view restrictions on this collection
                form = CollectionViewRestrictionForm(initial={
                    'restriction_type': 'none'
                })

    if restriction_exists_on_ancestor:
        # display a message indicating that there is a restriction at ancestor level -
        # do not provide the form for setting up new restrictions
        return render_modal_workflow(
            request, 'wagtailadmin/collection_privacy/ancestor_privacy.html', None,
            {
                'collection_with_restriction': restriction.collection,
            }
        )
    else:
        # no restriction set at ancestor level - can set restrictions here
        return render_modal_workflow(
            request,
            'wagtailadmin/collection_privacy/set_privacy.html',
            'wagtailadmin/collection_privacy/set_privacy.js', {
                'collection': collection,
                'form': form,
            }
        )
