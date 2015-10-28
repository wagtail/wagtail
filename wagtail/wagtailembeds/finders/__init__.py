from django.utils.module_loading import import_string
from django.conf import settings

from wagtail.wagtailembeds.finders.oembed import oembed
from wagtail.wagtailembeds.finders.embedly import embedly


MOVED_FINDERS = {
    'wagtail.wagtailembeds.embeds.embedly': 'wagtail.wagtailembeds.finders.embedly.embedly',
    'wagtail.wagtailembeds.embeds.oembed': 'wagtail.wagtailembeds.finders.oembed.oembed',
}


def get_default_finder():
    # Check if the user has set the embed finder manually
    if hasattr(settings, 'WAGTAILEMBEDS_EMBED_FINDER'):
        finder_name = settings.WAGTAILEMBEDS_EMBED_FINDER

        if finder_name in MOVED_FINDERS:
            finder_name = MOVED_FINDERS[finder_name]

        return import_string(finder_name)

    # Use embedly if the embedly key is set
    if hasattr(settings, 'WAGTAILEMBEDS_EMBEDLY_KEY'):
        return embedly

    # Fall back to oembed
    return oembed
