import warnings

from django import template
from django.utils.safestring import mark_safe

from wagtail.wagtailembeds import embeds


register = template.Library()


@register.filter
def embed(url, max_width=None):
    embed = embeds.get_embed(url, max_width=max_width)
    return mark_safe(embed.html)
