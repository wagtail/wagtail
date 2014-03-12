from django import template
from wagtail.wagtailadmin import edit_bird, hooks
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

    # Get items
    if items is None:
        if hasattr(request, 'wagtail_edit_bird_items'):
            items = request.wagtail_edit_bird_items
        else:
            items = [
                edit_bird.EditPageItem(current_page),
            ]
    for fn in hooks.get_hooks('construct_wagtail_edit_bird'):
        fn(request, items)

    # Render edit bird
    edit_bird_rendered = edit_bird.render_edit_bird(request, items)

    if edit_bird_rendered:
        # Disable cache
        request.disable_cache = True

        return edit_bird_rendered
    else:
        return ''
