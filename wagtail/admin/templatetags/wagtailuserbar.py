from django import template
from django.template.loader import render_to_string
from django.utils import translation

from wagtail import hooks
from wagtail.admin.userbar import (
    AddPageItem,
    AdminItem,
    ApproveModerationEditPageItem,
    EditPageItem,
    ExplorePageItem,
    RejectModerationEditPageItem,
)
from wagtail.models import PAGE_TEMPLATE_VAR, Page, PageRevision
from wagtail.users.models import UserProfile

register = template.Library()


def get_page_instance(context):
    """
    Given a template context, try and find a Page variable in the common
    places. Returns None if a page can not be found.
    """
    possible_names = [PAGE_TEMPLATE_VAR, "self"]
    for name in possible_names:
        if name in context:
            page = context[name]
            if isinstance(page, Page):
                return page


@register.simple_tag(takes_context=True)
def wagtailuserbar(context, position="bottom-right"):
    # Find request object
    try:
        request = context["request"]
    except KeyError:
        return ""

    # Don't render without a user because we can't check their permissions
    try:
        user = request.user
    except AttributeError:
        return ""

    # Don't render if user doesn't have permission to access the admin area
    if not user.has_perm("wagtailadmin.access_admin"):
        return ""

    # Render the userbar using the user's preferred admin language
    userprofile = UserProfile.get_for_user(user)
    with translation.override(userprofile.get_preferred_language()):
        page = get_page_instance(context)

        try:
            revision_id = request.revision_id
        except AttributeError:
            revision_id = None

        if page and page.id:
            if revision_id:
                items = [
                    AdminItem(),
                    ExplorePageItem(PageRevision.objects.get(id=revision_id).page),
                    EditPageItem(PageRevision.objects.get(id=revision_id).page),
                    ApproveModerationEditPageItem(
                        PageRevision.objects.get(id=revision_id)
                    ),
                    RejectModerationEditPageItem(
                        PageRevision.objects.get(id=revision_id)
                    ),
                ]
            else:
                # Not a revision
                items = [
                    AdminItem(),
                    ExplorePageItem(Page.objects.get(id=page.id)),
                    EditPageItem(Page.objects.get(id=page.id)),
                    AddPageItem(Page.objects.get(id=page.id)),
                ]
        else:
            # Not a page.
            items = [AdminItem()]

        for fn in hooks.get_hooks("construct_wagtail_userbar"):
            fn(request, items)

        # Render the items
        rendered_items = [item.render(request) for item in items]

        # Remove any unrendered items
        rendered_items = [item for item in rendered_items if item]

        # Render the userbar items
        return render_to_string(
            "wagtailadmin/userbar/base.html",
            {
                "request": request,
                "items": rendered_items,
                "position": position,
                "page": page,
                "revision_id": revision_id,
            },
        )
