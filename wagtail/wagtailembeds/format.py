from __future__ import division  # Use true division

from django.utils.html import escape

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

            # Build html
            return '<div style="padding-bottom: %s;" class="responsive-object">%s</div>' % (ratio, embed.html)
        else:
            return ''
    except:
        return ''


def embed_to_editor_html(url):
    embed = get_embed(url)
    if embed is None:
        return

    return '<div class="embed-placeholder" contenteditable="false" data-embedtype="media" data-url="%s"><h3>%s</h3><p>%s<br/>%s<br/>%s</p><img src="%s"></div>' % (url, escape(embed.title), url, escape(embed.provider_name), escape(embed.author_name), embed.thumbnail_url)
