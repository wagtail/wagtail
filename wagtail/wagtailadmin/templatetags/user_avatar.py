from __future__ import absolute_import, unicode_literals
from django.contrib.staticfiles.templatetags.staticfiles import static

from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def user_avatar_url(context, *args, **kwargs):
    """
    A template tag that receives a user an size and return
    the appropiate avatar for that user.
    Usage: {% avatar_url user=request.user size=50 %}
    """

    user = kwargs.get('user')
    size = kwargs.get('size')
    if hasattr(user, 'wagtail_userprofile'):
        return user.wagtail_userprofile.get_avatar_url(size=size)
    return static('wagtailadmin/images/default-user-avatar.svg')
