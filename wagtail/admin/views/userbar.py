from django.contrib.auth.decorators import permission_required
from django.template.response import TemplateResponse

from wagtail import hooks
from wagtail.admin.userbar import (
    AddPageItem,
    ApproveModerationEditPageItem,
    EditPageItem,
    RejectModerationEditPageItem,
)
from wagtail.models import Page, Revision


@permission_required("wagtailadmin.access_admin", raise_exception=True)
def for_frontend(request, page_id):
    items = [
        EditPageItem(Page.objects.get(id=page_id)),
        AddPageItem(Page.objects.get(id=page_id)),
    ]

    for fn in hooks.get_hooks("construct_wagtail_userbar"):
        fn(request, items)

    # Render the items
    rendered_items = [item.render(request) for item in items]

    # Remove any unrendered items
    rendered_items = [item for item in rendered_items if item]

    # Render the edit bird
    return TemplateResponse(
        request,
        "wagtailadmin/userbar/base.html",
        {
            "items": rendered_items,
        },
    )


@permission_required("wagtailadmin.access_admin", raise_exception=True)
def for_moderation(request, revision_id):
    items = [
        EditPageItem(Revision.page_revisions.get(id=revision_id).content_object),
        AddPageItem(Revision.page_revisions.get(id=revision_id).content_object),
        ApproveModerationEditPageItem(Revision.page_revisions.get(id=revision_id)),
        RejectModerationEditPageItem(Revision.page_revisions.get(id=revision_id)),
    ]

    for fn in hooks.get_hooks("construct_wagtail_userbar"):
        fn(request, items)

    # Render the items
    rendered_items = [item.render(request) for item in items]

    # Remove any unrendered items
    rendered_items = [item for item in rendered_items if item]

    # Render the edit bird
    return TemplateResponse(
        request,
        "wagtailadmin/userbar/base.html",
        {
            "items": rendered_items,
        },
    )
