from __future__ import absolute_import, unicode_literals

from django import template
from django.contrib.staticfiles.templatetags.staticfiles import static
register = template.Library()


@register.simple_tag(takes_context=True)
def user_avatar_url(context, user, size):
    """
    A template tag that receives a user and size and return
    the appropiate avatar url for that user.
    Example usage: {% avatar_url request.user 50 %}
    """

    if hasattr(user, 'wagtail_userprofile'):  # A user could not have profile yet, so this is necessay
        return user.wagtail_userprofile.get_avatar_url(size=size)
    return static('wagtailadmin/images/default-user-avatar.svg')
