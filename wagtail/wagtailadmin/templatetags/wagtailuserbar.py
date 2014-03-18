from django import template
from wagtail.wagtailadmin.views import userbar
from wagtail.wagtailcore.models import Page

register = template.Library()

@register.simple_tag(takes_context=True)
def wagtailuserbar(context, current_page=None, items=None):

    # Find request object
    request = context['request']
    
    # Don't render if user doesn't have permission to access the admin area
    if not request.user.has_perm('wagtailadmin.access_admin'):
        return ''

    # Find page object
    if not current_page:
        if 'self' in context and isinstance(context['self'], Page):
            current_page = context['self']
        else:
            return ''

    # Render edit bird
    return userbar.render_edit_frame(request, context) or ''