from django import template
from django.template.loader import render_to_string

from wagtail.wagtailcore.models import Page, PAGE_TEMPLATE_VAR


register = template.Library()


def get_page_instance(context):
    """
    Given a template context, try and find a Page variable in the common
    places. Returns None if a page can not be found.
    """
    possible_names = [PAGE_TEMPLATE_VAR, 'self']
    for name in possible_names:
        if name in context:
            page = context[name]
            if isinstance(page, Page):
                return page


@register.simple_tag(takes_context=True)
def wagtailuserbar(context):
    # Find request object
    request = context['request']

    # Don't render if user doesn't have permission to access the admin area
    if not request.user.has_perm('wagtailadmin.access_admin'):
        return ''

    # Only render if the context contains a variable referencing a saved page
    page = get_page_instance(context)
    if page is None:
        return ''

    # Dont render anything if the page has not been saved - i.e. a preview
    if page.pk is None:
        return ''

    try:
        revision_id = request.revision_id
    except AttributeError:
        revision_id = None

    # Render the frame to contain the userbar items
    return render_to_string('wagtailadmin/userbar/frame.html', {
        'request': request,
        'page': page,
        'revision_id': revision_id
    })
