from __future__ import absolute_import, unicode_literals

from datetime import datetime

from .exceptions import EmbedUnsupportedProviderException
from .finders import get_finders
from .models import Embed


def get_embed(url, max_width=None, finder=None):
    # Check database
    try:
        return Embed.objects.get(url=url, max_width=max_width)
    except Embed.DoesNotExist:
        pass

    # Get/Call finder
    if not finder:
        def finder(url, max_width=None):
            for finder in get_finders():
                if finder.accept(url):
                    return finder.find_embed(url, max_width=max_width)

            raise EmbedUnsupportedProviderException

    embed_dict = finder(url, max_width)

    # Make sure width and height are valid integers before inserting into database
    try:
        embed_dict['width'] = int(embed_dict['width'])
    except (TypeError, ValueError):
        embed_dict['width'] = None

    try:
        embed_dict['height'] = int(embed_dict['height'])
    except (TypeError, ValueError):
        embed_dict['height'] = None

    # Make sure html field is valid
    if 'html' not in embed_dict or not embed_dict['html']:
        embed_dict['html'] = ''

    # Create database record
    embed, created = Embed.objects.get_or_create(
        url=url,
        max_width=max_width,
        defaults=embed_dict,
    )

    # Save
    embed.last_updated = datetime.now()
    embed.save()

    return embed
