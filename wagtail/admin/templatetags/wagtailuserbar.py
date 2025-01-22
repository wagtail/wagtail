from django import template
from django.template.loader import render_to_string
from django.utils import translation

from wagtail.admin.userbar import (
    AccessibilityItem,
    AddPageItem,
    AdminItem,
    EditPageItem,
    ExplorePageItem,
    apply_userbar_hooks,
)
from wagtail.models import PAGE_TEMPLATE_VAR, Page, Revision
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

    # Render the userbar differently within the preview panel.
    in_preview_panel = getattr(request, "in_preview_panel", False)

    # Render the userbar using the user's preferred admin language
    userprofile = UserProfile.get_for_user(user)
    with translation.override(userprofile.get_preferred_language()):
        page = get_page_instance(context)

        try:
            revision_id = request.revision_id
        except AttributeError:
            revision_id = None

        if in_preview_panel:
            items = [
                AccessibilityItem(),
            ]
        elif page and page.id:
            if revision_id:
                revision = Revision.page_revisions.get(id=revision_id)
                items = [
                    AdminItem(),
                    ExplorePageItem(revision.content_object),
                    EditPageItem(revision.content_object),
                    AccessibilityItem(),
                ]
            else:
                # Not a revision
                items = [
                    AdminItem(),
                    ExplorePageItem(page),
                    EditPageItem(page),
                    AddPageItem(page),
                    AccessibilityItem(),
                ]
        else:
            # Not a page.
            items = [
                AdminItem(),
                AccessibilityItem(),
            ]

        apply_userbar_hooks(request, items, page)

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
