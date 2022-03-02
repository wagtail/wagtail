import json
import re
from datetime import timedelta
from urllib import request as urllib_request
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request

from django.utils import timezone

from wagtail.embeds.exceptions import EmbedNotFoundException
from wagtail.embeds.oembed_providers import all_providers

from .base import EmbedFinder


class OEmbedFinder(EmbedFinder):
    options = {}
    _endpoints = None

    def __init__(self, providers=None, options=None):
        self._endpoints = {}

        for provider in providers or all_providers:
            patterns = []

            endpoint = provider["endpoint"].replace("{format}", "json")

            for url in provider["urls"]:
                patterns.append(re.compile(url))

            self._endpoints[endpoint] = patterns

        if options:
            self.options = self.options.copy()
            self.options.update(options)

    def _get_endpoint(self, url):
        for endpoint, patterns in self._endpoints.items():
            for pattern in patterns:
                if re.match(pattern, url):
                    return endpoint

    def accept(self, url):
        return self._get_endpoint(url) is not None

    def find_embed(self, url, max_width=None, max_height=None):
        # Find provider
        endpoint = self._get_endpoint(url)
        if endpoint is None:
            raise EmbedNotFoundException

        # Work out params
        params = self.options.copy()
        params["url"] = url
        params["format"] = "json"
        if max_width:
            params["maxwidth"] = max_width
        if max_height:
            params["maxheight"] = max_height

        # Perform request
        request = Request(endpoint + "?" + urlencode(params))
        request.add_header("User-agent", "Mozilla/5.0")
        try:
            r = urllib_request.urlopen(request)
            oembed = json.loads(r.read().decode("utf-8"))
        except (URLError, json.decoder.JSONDecodeError):
            raise EmbedNotFoundException

        # Convert photos into HTML
        if oembed["type"] == "photo":
            html = '<img src="%s" alt="">' % (oembed["url"],)
        else:
            html = oembed.get("html")

        # Return embed as a dict
        result = {
            "title": oembed.get("title", ""),
            "author_name": oembed.get("author_name", ""),
            "provider_name": oembed.get("provider_name", ""),
            "type": oembed["type"],
            "thumbnail_url": oembed.get("thumbnail_url"),
            "width": oembed.get("width"),
            "height": oembed.get("height"),
            "html": html,
        }

        try:
            cache_age = int(oembed["cache_age"])
        except (KeyError, TypeError, ValueError):
            pass
        else:
            result["cache_until"] = timezone.now() + timedelta(seconds=cache_age)

        return result


embed_finder_class = OEmbedFinder
