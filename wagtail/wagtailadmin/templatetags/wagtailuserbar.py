import warnings

from django import template
from django.template.loader import render_to_string

from wagtail.wagtailcore.models import Page


register = template.Library()


@register.simple_tag(takes_context=True)
def wagtailuserbar(context):
    # Find request object
    request = context['request']
    
    # Don't render if user doesn't have permission to access the admin area
    if not request.user.has_perm('wagtailadmin.access_admin'):
        return ''

    # Only render if the context contains a 'self' variable referencing a saved page
    if 'self' in context and isinstance(context['self'], Page) and context['self'].id is not None:
        pass
    else:
        return ''

    try:
        revision_id = request.revision_id
    except AttributeError:
        revision_id = None

    # Render the frame to contain the userbar items
    return render_to_string('wagtailadmin/userbar/frame.html', {
        'request': request,
        'page': context,
        'revision_id': revision_id
    })
