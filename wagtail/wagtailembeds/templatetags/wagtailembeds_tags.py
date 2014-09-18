import warnings

from django import template
from django.utils.safestring import mark_safe

from wagtail.wagtailembeds.embeds import get_embed


register = template.Library()


@register.filter
def embed(url, max_width=None):
    embed = get_embed(url, max_width=max_width)
    try:
        if embed is not None:
            return mark_safe(embed.html)
        else:
            return ''
    except:
        return ''
