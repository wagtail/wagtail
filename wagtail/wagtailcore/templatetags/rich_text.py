from django import template
from django.utils.safestring import mark_safe

from wagtail.wagtailcore.rich_text import expand_db_html

register = template.Library()

@register.filter
def richtext(value):
    return mark_safe(expand_db_html(value))
