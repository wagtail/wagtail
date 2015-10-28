from datetime import datetime

from django.utils.module_loading import import_string
from django.conf import settings

from wagtail.wagtailembeds.models import Embed
from wagtail.wagtailembeds.exceptions import EmbedException, EmbedNotFoundException  # noqa
from wagtail.wagtailembeds.finders.oembed import oembed
from wagtail.wagtailembeds.finders.embedly import embedly


def get_default_finder():
    # Check if the user has set the embed finder manually
    if hasattr(settings, 'WAGTAILEMBEDS_EMBED_FINDER'):
        return import_string(settings.WAGTAILEMBEDS_EMBED_FINDER)

    # Use embedly if the embedly key is set
    if hasattr(settings, 'WAGTAILEMBEDS_EMBEDLY_KEY'):
        return embedly

    # Fall back to oembed
    return oembed


def get_embed(url, max_width=None, finder=None):
    # Check database
    try:
        return Embed.objects.get(url=url, max_width=max_width)
    except Embed.DoesNotExist:
        pass

    # Get/Call finder
    if not finder:
        finder = get_default_finder()
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
