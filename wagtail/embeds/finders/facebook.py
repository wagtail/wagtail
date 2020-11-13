import json
import re

from urllib import request as urllib_request
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request

from wagtail.embeds.exceptions import EmbedException, EmbedNotFoundException

from .base import EmbedFinder


class AccessDeniedFacebookOEmbedException(EmbedException):
    pass


class FacebookOEmbedFinder(EmbedFinder):
    '''
    An embed finder that supports the authenticated Facebook oEmbed Endpoint.
    https://developers.facebook.com/docs/plugins/oembed
    '''
    facebook_video = {
        "endpoint": "https://graph.facebook.com/v9.0/oembed_video",
        "urls": [
            r'^https://(?:www\.)?facebook\.com/.+?/videos/.+$',
            r'^https://(?:www\.)?facebook\.com/video\.php\?(?:v|id)=.+$',
            r'^https://fb.watch/.+$',
        ],
    }

    facebook_post = {
        "endpoint": "https://graph.facebook.com/v9.0/oembed_post",
        "urls": [
            r'^https://(?:www\.)?facebook\.com/.+?/(?:posts|activity)/.+$',
            r'^https://(?:www\.)?facebook\.com/photo\.php\?fbid=.+$',
            r'^https://(?:www\.)?facebook\.com/(?:photos|questions)/.+$',
            r'^https://(?:www\.)?facebook\.com/permalink\.php\?story_fbid=.+$',
            r'^https://(?:www\.)?facebook\.com/media/set/?\?set=.+$',
            r'^https://(?:www\.)?facebook\.com/notes/.+?/.+?/.+$',

            # At the moment, not documented on https://developers.facebook.com/docs/plugins/oembed-endpoints
            # Works for posts with a single photo
            r'^https://(?:www\.)?facebook\.com/.+?/photos/.+$',
        ],
    }

    def __init__(self, omitscript=False, app_id=None, app_secret=None):
        # {settings.facebook_APP_ID}|{settings.facebook_APP_SECRET}
        self.app_id = app_id
        self.app_secret = app_secret
        self.omitscript = omitscript

        self._endpoints = {}

        for provider in [self.facebook_video, self.facebook_post]:
            patterns = []

            endpoint = provider['endpoint'].replace('{format}', 'json')

            for url in provider['urls']:
                patterns.append(re.compile(url))

            self._endpoints[endpoint] = patterns

    def _get_endpoint(self, url):
        for endpoint, patterns in self._endpoints.items():
            for pattern in patterns:
                if re.match(pattern, url):
                    return endpoint

    def accept(self, url):
        return self._get_endpoint(url) is not None

    def find_embed(self, url, max_width=None):
        # Find provider
        endpoint = self._get_endpoint(url)
        if endpoint is None:
            raise EmbedNotFoundException

        params = {'url': url, 'format': 'json'}
        if max_width:
            params['maxwidth'] = max_width
        if self.omitscript:
            params['omitscript'] = 'true'

        # Configure request
        request = Request(endpoint + '?' + urlencode(params))
        request.add_header('Authorization', f'Bearer {self.app_id}|{self.app_secret}')

        # Perform request
        try:
            r = urllib_request.urlopen(request)
        except (HTTPError, URLError) as e:
            if isinstance(e, HTTPError) and e.code == 404:
                raise EmbedNotFoundException
            elif isinstance(e, HTTPError) and e.code in [400, 401, 403]:
                raise AccessDeniedFacebookOEmbedException
            else:
                raise EmbedNotFoundException
        oembed = json.loads(r.read().decode('utf-8'))

        # Return embed as a dict
        return {
            'title': oembed['title'] if 'title' in oembed else '',
            'author_name': oembed['author_name'] if 'author_name' in oembed else '',
            'provider_name': oembed['provider_name'] if 'provider_name' in oembed else 'Facebook',
            'type': oembed['type'],
            'thumbnail_url': oembed.get('thumbnail_url'),
            'width': oembed.get('width'),
            'height': oembed.get('height'),
            'html': oembed.get('html'),
        }


embed_finder_class = FacebookOEmbedFinder
