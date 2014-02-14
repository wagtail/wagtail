import sys
from importlib import import_module
import requests
from django.conf import settings
from datetime import datetime
from django.utils import six
from wagtail.wagtailembeds.oembed_providers import get_oembed_provider
from wagtail.wagtailembeds.models import Embed


class EmbedNotFoundException(Exception): pass

class EmbedlyException(Exception): pass
class AccessDeniedEmbedlyException(EmbedlyException): pass


# Pinched from django 1.7 source code.
# TODO: Replace this with "from django.utils.module_loading import import_string" when django 1.7 is released
def import_string(dotted_path):
    """
    Import a dotted module path and return the attribute/class designated by the
    last name in the path. Raise ImportError if the import failed.
    """
    try:
        module_path, class_name = dotted_path.rsplit('.', 1)
    except ValueError:
        msg = "%s doesn't look like a module path" % dotted_path
        six.reraise(ImportError, ImportError(msg), sys.exc_info()[2])

    module = import_module(module_path)

    try:
        return getattr(module, class_name)
    except AttributeError:
        msg = 'Module "%s" does not define a "%s" attribute/class' % (
            dotted_path, class_name)
        six.reraise(ImportError, ImportError(msg), sys.exc_info()[2])


def embedly(url, max_width=None, key=None):
    from embedly import Embedly

    # Get embedly key
    if key is None:
        key = settings.EMBEDLY_KEY

    # Get embedly client
    client = Embedly(key=settings.EMBEDLY_KEY)

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
        'title': oembed['title'],
        'type': oembed['type'],
        'thumbnail_url': oembed.get('thumbnail_url'),
        'width': oembed.get('width'),
        'height': oembed.get('height'),
        'html': html,
    }


def oembed(url, max_width=None):
    # Find provider
    provider = get_oembed_provider(url)
    if provider is None:
        raise EmbedNotFoundException

    # Work out params
    params = {'url': url, 'format': 'json',  }
    if max_width:
        params['maxwidth'] = max_width

    # Perform request
    r = requests.get(provider, params=params)
    if r.status_code != 200:
        raise EmbedNotFoundException
    oembed = r.json()

    # Convert photos into HTML
    if oembed['type'] == 'photo':
        html = '<img src="%s" />' % (oembed['url'], )
    else:
        html = oembed.get('html')

    # Return embed as a dict
    return {
        'title': oembed['title'],
        'type': oembed['type'],
        'thumbnail_url': oembed.get('thumbnail_url'),
        'width': oembed.get('width'),
        'height': oembed.get('height'),
        'html': html,
    }


def get_default_finder():
    # Check if the user has set the embed finder manually
    if hasattr(settings, 'WAGTAILEMBEDS_EMBED_FINDER'):
        return import_string(settings.WAGTAILEMBEDS_EMBED_FINDER)

    # Use embedly if the embedly key is set
    if hasattr(settings, 'EMBEDLY_KEY'):
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
