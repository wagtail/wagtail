from django.utils.module_loading import import_string
from django.conf import settings

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
