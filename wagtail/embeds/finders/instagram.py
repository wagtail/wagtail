import json
from urllib import request as urllib_request
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request

from wagtail.embeds.exceptions import EmbedException, EmbedNotFoundException

from .oembed import OEmbedFinder


class AccessDeniedInstagramOEmbedException(EmbedException):
    pass


INSTAGRAM_PROVIDER = {
    "endpoint": "https://graph.facebook.com/v11.0/instagram_oembed",
    "urls": [
        r"^https?://(?:www\.)?instagram\.com/p/.+$",
        r"^https?://(?:www\.)?instagram\.com/tv/.+$",
        r"^https?://(?:www\.)?instagram\.com/reel/.+$",
    ],
}


class InstagramOEmbedFinder(OEmbedFinder):
    """
    An embed finder that supports the authenticated Instagram oEmbed Endpoint.
    https://developers.facebook.com/docs/instagram/oembed
    """

    def __init__(self, omitscript=False, app_id=None, app_secret=None):
        # {settings.INSTAGRAM_APP_ID}|{settings.INSTAGRAM_APP_SECRET}
        self.app_id = app_id
        self.app_secret = app_secret
        self.omitscript = omitscript

        super().__init__(providers=[INSTAGRAM_PROVIDER])

    def find_embed(self, url, max_width=None, max_height=None):
        # Find provider
        endpoint = self._get_endpoint(url)
        if endpoint is None:
            raise EmbedNotFoundException

        params = {"url": url, "format": "json"}
        if max_width:
            params["maxwidth"] = max_width
        if max_height:
            params["maxheight"] = max_height
        if self.omitscript:
            params["omitscript"] = "true"

        # Configure request
        request = Request(endpoint + "?" + urlencode(params))
        request.add_header("Authorization", f"Bearer {self.app_id}|{self.app_secret}")

        # Perform request
        try:
            r = urllib_request.urlopen(request)
        except (HTTPError, URLError) as e:
            if isinstance(e, HTTPError) and e.code == 404:
                raise EmbedNotFoundException
            elif isinstance(e, HTTPError) and e.code in [400, 401, 403]:
                raise AccessDeniedInstagramOEmbedException
            else:
                raise EmbedNotFoundException
        oembed = json.loads(r.read().decode("utf-8"))

        # Convert photos into HTML
        if oembed["type"] == "photo":
            html = '<img src="{}" alt="">'.format(oembed["url"])
        else:
            html = oembed.get("html")

        # Return embed as a dict
        return {
            "title": oembed["title"] if "title" in oembed else "",
            "author_name": oembed["author_name"] if "author_name" in oembed else "",
            "provider_name": oembed["provider_name"]
            if "provider_name" in oembed
            else "Instagram",
            "type": oembed["type"],
            "thumbnail_url": oembed.get("thumbnail_url"),
            "width": oembed.get("width"),
            "height": oembed.get("height"),
            "html": html,
        }


embed_finder_class = InstagramOEmbedFinder
