from __future__ import absolute_import, unicode_literals

import warnings

from django import template
from django.utils.safestring import mark_safe

from wagtail.utils.deprecation import RemovedInWagtail19Warning
from wagtail.wagtailembeds import embeds
from wagtail.wagtailembeds.exceptions import EmbedException

register = template.Library()


@register.filter
def embed(url, max_width=None):
    warnings.warn(
        "The embed filter has been converted to a template tag. "
        "Use {% embed my_embed_url %} instead.",
        category=RemovedInWagtail19Warning, stacklevel=2
    )

    return embed_tag(url, max_width)


@register.simple_tag(name='embed')
def embed_tag(url, max_width=None):
    try:
        embed = embeds.get_embed(url, max_width=max_width)
        return mark_safe(embed.html)
    except EmbedException:
        return ''
