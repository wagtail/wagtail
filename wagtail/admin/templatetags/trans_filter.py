from django import template
from django.utils.translation import gettext as _

register = template.Library()


@register.simple_tag
def trans(msg_var):
    result_var = msg_var
    return _(result_var)
