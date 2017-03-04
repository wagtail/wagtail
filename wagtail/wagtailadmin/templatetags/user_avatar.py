from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def user_avatar_url(context, *args, **kwargs):
    """
    A template tag that receives a user an size and return
    the appropiate avatar for that user.
    If user is not passed, the user in the request is used.
    Usage: {% avatar_url user=request.user size=50 %}
    """
    user = getattr(kwargs, 'user', context['user'])
    size = kwargs['size']

    return user.wagtail_userprofile.get_avatar_url(size=size)

