from django import template

from wagtail.core import hooks


register = template.Library()


@register.inclusion_tag("wagtailsnippets/snippets/listing_buttons.html",
                        takes_context=True)
def snippet_listing_buttons(context, snippet):
    next_url = context.request.path
    button_hooks = hooks.get_hooks('register_snippet_listing_buttons')

    buttons = []
    for hook in button_hooks:
        buttons.extend(hook(snippet, context.request.user, next_url))

    buttons.sort()

    for hook in hooks.get_hooks('construct_snippet_listing_buttons'):
        hook(buttons, snippet, context.request.user, context)

    return {'snippet': snippet, 'buttons': buttons}
