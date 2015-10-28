from __future__ import absolute_import

import json

# Needs to be imported like this to allow @patch to work in tests
from django.utils.six.moves.urllib import request as urllib_request
from django.utils.six.moves.urllib.request import Request
from django.utils.six.moves.urllib.error import URLError
from django.utils.six.moves.urllib.parse import urlencode

from wagtail.wagtailembeds.oembed_providers import get_oembed_provider
from wagtail.wagtailembeds.exceptions import EmbedNotFoundException


def oembed(url, max_width=None):
    # Find provider
    provider = get_oembed_provider(url)
    if provider is None:
        raise EmbedNotFoundException

    # Work out params
    params = {'url': url, 'format': 'json'}
    if max_width:
        params['maxwidth'] = max_width

    # Perform request
    request = Request(provider + '?' + urlencode(params))
    request.add_header('User-agent', 'Mozilla/5.0')
    try:
        r = urllib_request.urlopen(request)
    except URLError:
        raise EmbedNotFoundException
    oembed = json.loads(r.read().decode('utf-8'))

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


find_embed = oembed
