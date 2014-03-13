from django import template
from wagtail.wagtailadmin.views import userbar
from wagtail.wagtailcore.models import Page

register = template.Library()

@register.simple_tag(takes_context=True)
def wagtail_edit_bird(context, current_page=None, items=None):
    # Find page object
    if not current_page:
        if 'self' in context and isinstance(context['self'], Page):
            current_page = context['self']
        else:
            return ''

    # Find request object
    request = context['request']

    print context

    # Render edit bird
    return userbar.render_edit_frame(request, context) or ''
