import warnings

from django.shortcuts import render
from django.contrib.auth.decorators import permission_required

from wagtail.wagtailadmin.userbar import EditPageItem, AddPageItem, ApproveModerationEditPageItem, RejectModerationEditPageItem
from wagtail.wagtailcore import hooks
from wagtail.wagtailcore.models import Page, PageRevision

from wagtail.utils.deprecation import RemovedInWagtail11Warning


@permission_required('wagtailadmin.access_admin', raise_exception=True)
def for_frontend(request, page_id):
    items = [
        EditPageItem(Page.objects.get(id=page_id)),
        AddPageItem(Page.objects.get(id=page_id)),
    ]

    # TODO: Remove in 1.1 release
    run_deprecated_edit_bird_hook(request, items)

    for fn in hooks.get_hooks('construct_wagtail_userbar'):
        fn(request, items)

    # Render the items
    rendered_items = [item.render(request) for item in items]

    # Remove any unrendered items
    rendered_items = [item for item in rendered_items if item]

    # Render the edit bird
    return render(request, 'wagtailadmin/userbar/base.html', {
        'items': rendered_items,
    })


@permission_required('wagtailadmin.access_admin', raise_exception=True)
def for_moderation(request, revision_id):
    items = [
        EditPageItem(PageRevision.objects.get(id=revision_id).page),
        AddPageItem(PageRevision.objects.get(id=revision_id).page),
        ApproveModerationEditPageItem(PageRevision.objects.get(id=revision_id)),
        RejectModerationEditPageItem(PageRevision.objects.get(id=revision_id)),
    ]

    # TODO: Remove in 1.1 release
    run_deprecated_edit_bird_hook(request, items)

    for fn in hooks.get_hooks('construct_wagtail_userbar'):
        fn(request, items)

    # Render the items
    rendered_items = [item.render(request) for item in items]

    # Remove any unrendered items
    rendered_items = [item for item in rendered_items if item]

    # Render the edit bird
    return render(request, 'wagtailadmin/userbar/base.html', {
        'items': rendered_items,
    })


def run_deprecated_edit_bird_hook(request, items):
    for fn in hooks.get_hooks('construct_wagtail_edit_bird'):
        fn(request, items)

        warnings.warn(
            "The 'construct_wagtail_edit_bird' hook has been renamed to 'construct_wagtail_userbar'."
            "Please update function '%s' in '%s'." % (fn.__name__, fn.__module__), RemovedInWagtail11Warning
        )
