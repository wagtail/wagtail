from django.utils.module_loading import import_string
from django.conf import settings


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

    elif hasattr(settings, 'WAGTAILEMBEDS_EMBEDLY_KEY'):
        # Default to Embedly as an embedly key is set
        finder_name = 'wagtail.wagtailembeds.finders.embedly.embedly'

    else:
        # Default to oembed
        finder_name = 'wagtail.wagtailembeds.finders.oembed.oembed'

    return import_string(finder_name)
