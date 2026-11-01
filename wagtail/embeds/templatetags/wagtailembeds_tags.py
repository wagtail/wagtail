from django import template
from django.utils.safestring import mark_safe

from wagtail.embeds import embeds
from wagtail.embeds.exceptions import EmbedException

register = template.Library()


@register.simple_tag(name="embed")
def embed_tag(url, max_width=None):
    try:
        embed = embeds.get_embed(url, max_width=max_width)
        return mark_safe(embed.html)  # noqa: S308 - we need to render the html we get back from the embed provider
    except EmbedException:
        return ""
