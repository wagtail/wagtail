from django import template
from django.utils.safestring import mark_safe

from wagtail.wagtailembeds.embed.embeds import get_embed


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


@register.filter
def embedly(url, max_width=None):
    return embed(url, max_width)
