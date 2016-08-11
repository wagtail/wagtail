from __future__ import absolute_import, unicode_literals

from django import template
from django.utils.safestring import mark_safe

from wagtail.wagtailembeds import embeds
from wagtail.wagtailembeds.exceptions import EmbedException

register = template.Library()


@register.filter
def embed(url, max_width=None):
    try:
        embed = embeds.get_embed(url, max_width=max_width)
        return mark_safe(embed.html)
    except EmbedException:
        return ''
