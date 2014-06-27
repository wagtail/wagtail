from __future__ import division  # Use true division

from django.template.loader import render_to_string

from wagtail.wagtailembeds import get_embed


def embed_to_frontend_html(url):
    try:
        embed = get_embed(url)
        if embed is not None:
            # Work out ratio
            if embed.width and embed.height:
                ratio = str(embed.height / embed.width * 100) + "%"
            else:
                ratio = "0"

            # Render template
            return render_to_string('wagtailembeds/embed_frontend.html', {
                'embed': embed,
                'ratio': ratio,
            })
        else:
            return ''
    except:
        return ''


def embed_to_editor_html(url):
    embed = get_embed(url)
    if embed is None:
        return

    # Render template
    return render_to_string('wagtailembeds/embed_editor.html', {
        'embed': embed,
    })
