from __future__ import absolute_import, unicode_literals

from django.conf import settings

from wagtail.wagtailembeds.exceptions import EmbedException, EmbedNotFoundException


class EmbedlyException(EmbedException):
    pass


class AccessDeniedEmbedlyException(EmbedlyException):
    pass


def embedly(url, max_width=None, key=None):
    from embedly import Embedly

    # Get embedly key
    if key is None:
        key = settings.WAGTAILEMBEDS_EMBEDLY_KEY

    # Get embedly client
    client = Embedly(key=key)

    # Call embedly
    if max_width is not None:
        oembed = client.oembed(url, maxwidth=max_width, better=False)
    else:
        oembed = client.oembed(url, better=False)

    # Check for error
    if oembed.get('error'):
        if oembed['error_code'] in [401, 403]:
            raise AccessDeniedEmbedlyException
        elif oembed['error_code'] == 404:
            raise EmbedNotFoundException
        else:
            raise EmbedlyException

    # Convert photos into HTML
    if oembed['type'] == 'photo':
        html = '<img src="%s" />' % (oembed['url'], )
    else:
        html = oembed.get('html')

    # Return embed as a dict
    return {
        'title': oembed['title'] if 'title' in oembed else '',
        'author_name': oembed['author_name'] if 'author_name' in oembed else '',
        'provider_name': oembed['provider_name'] if 'provider_name' in oembed else '',
        'type': oembed['type'],
        'thumbnail_url': oembed.get('thumbnail_url'),
        'width': oembed.get('width'),
        'height': oembed.get('height'),
        'html': html,
    }


find_embed = embedly
