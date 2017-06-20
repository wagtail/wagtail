from __future__ import absolute_import, unicode_literals

from django.template.loader import render_to_string

from wagtail.wagtailembeds import embeds
from wagtail.wagtailembeds.exceptions import EmbedException


def embed_to_frontend_html(url):
    try:
        embed = embeds.get_embed(url)

        # Render template
        return render_to_string('wagtailembeds/embed_frontend.html', {
            'embed': embed,
        })
    except EmbedException:
        # silently ignore failed embeds, rather than letting them crash the page
        return ''


def embed_to_editor_html(url):
    embed = embeds.get_embed(url)
    # catching EmbedException is the responsibility of the caller

    # Render template
    return render_to_string('wagtailembeds/embed_editor.html', {
        'embed': embed,
    })
