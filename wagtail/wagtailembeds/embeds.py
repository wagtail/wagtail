import sys

try:
    from importlib import import_module
except ImportError:
    # for Python 2.6, fall back on django.utils.importlib (deprecated as of Django 1.7)
    from django.utils.importlib import import_module

from django.conf import settings
from datetime import datetime
from django.utils import six
from wagtail.wagtailembeds.oembed_providers import get_oembed_provider
from wagtail.wagtailembeds.models import Embed
import urllib2, urllib
import json


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
    request = urllib2.Request(provider + '?' + urllib.urlencode(params))
    request.add_header('User-agent', 'Mozilla/5.0')
    try:
        r = urllib2.urlopen(request)
    except urllib2.URLError:
        raise EmbedNotFoundException
    oembed = json.loads(r.read())

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
