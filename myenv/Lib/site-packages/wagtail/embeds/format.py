from django.template.loader import render_to_string

from wagtail.embeds import embeds
from wagtail.embeds.exceptions import EmbedException


def embed_to_frontend_html(url, max_width=None, max_height=None):
    try:
        embed = embeds.get_embed(url, max_width, max_height)

        # Render template
        return render_to_string(
            "wagtailembeds/embed_frontend.html",
            {
                "embed": embed,
            },
        )
    except EmbedException:
        # silently ignore failed embeds, rather than letting them crash the page
        return ""


def embed_to_editor_html(url):
    embed = embeds.get_embed(url)
    # catching EmbedException is the responsibility of the caller

    # Render template
    return render_to_string(
        "wagtailembeds/embed_editor.html",
        {
            "embed": embed,
        },
    )
