from django import template
from django.contrib.staticfiles.storage import staticfiles_storage
from django.utils.html import format_html, format_html_join

register = template.Library()


@register.simple_tag(takes_context=True)
def wagtailuserbar(context, cssfile=None):
    try:
        items = format_html_join('', '<li>{0}</li>', [(item,) for item in context['request'].userbar])
        context.hasuserbar = True
        if not cssfile:
            cssfile = staticfiles_storage.url('wagtailadmin/css/wagtail-userbar.css')
        return format_html('<link rel="stylesheet" href="//fonts.googleapis.com/css?family=Open+Sans:400" /><link rel="stylesheet" href="{0}" /><ul id="wagtail-userbar">{1}</ul>', cssfile, items)
    except AttributeError:
        return ''
