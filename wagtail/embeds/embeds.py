from datetime import datetime

from django.utils.timezone import now

from wagtail.coreutils import accepts_kwarg, safe_md5

from .exceptions import EmbedUnsupportedProviderException
from .finders import get_finders
from .models import Embed


def get_finder_for_embed(url, max_width=None, max_height=None):
    for finder in get_finders():
        if finder.accept(url):
            kwargs = {}
            if accepts_kwarg(finder.find_embed, "max_height"):
                kwargs["max_height"] = max_height
            return finder.find_embed(url, max_width=max_width, **kwargs)

    raise EmbedUnsupportedProviderException


def get_embed(url, max_width=None, max_height=None, finder=get_finder_for_embed):
    embed_hash = get_embed_hash(url, max_width, max_height)

    # Check database
    try:
        return Embed.objects.exclude(cache_until__lte=now()).get(hash=embed_hash)
    except Embed.DoesNotExist:
        pass

    embed_dict = finder(url, max_width, max_height)

    # Make sure width and height are valid integers before inserting into database
    try:
        embed_dict["width"] = int(embed_dict["width"])
    except (TypeError, ValueError):
        embed_dict["width"] = None

    try:
        embed_dict["height"] = int(embed_dict["height"])
    except (TypeError, ValueError):
        embed_dict["height"] = None

    # Make sure html field is valid
    if "html" not in embed_dict or not embed_dict["html"]:
        embed_dict["html"] = ""

    # If the finder does not return an thumbnail_url, convert null to '' before inserting into the db
    if "thumbnail_url" not in embed_dict or not embed_dict["thumbnail_url"]:
        embed_dict["thumbnail_url"] = ""

    # Create database record
    embed, created = Embed.objects.update_or_create(
        hash=embed_hash, defaults=dict(url=url, max_width=max_width, **embed_dict)
    )

    # Save
    embed.last_updated = datetime.now()
    embed.save()

    return embed


def get_embed_hash(url, max_width=None, max_height=None):
    h = safe_md5(url.encode("utf-8"), usedforsecurity=False)
    if max_width is not None:
        h.update(b"\n")
        h.update(str(max_width).encode("utf-8"))
    if max_height is not None:
        h.update(b"\n")
        h.update(str(max_height).encode("utf-8"))
    return h.hexdigest()
