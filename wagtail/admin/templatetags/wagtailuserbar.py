from django import template

from wagtail.admin.userbar import Userbar
from wagtail.models import PAGE_TEMPLATE_VAR, Page

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

    page = get_page_instance(context)

    return Userbar(object=page, position=position).render_html(context)
