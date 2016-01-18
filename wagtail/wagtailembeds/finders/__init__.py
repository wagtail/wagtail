import pprint
import sys
import warnings
from importlib import import_module

from django.utils.module_loading import import_string
from django.utils import six
from django.conf import settings

from wagtail.utils.deprecation import RemovedInWagtail114Warning


MOVED_FINDERS = {
    'wagtail.wagtailembeds.embeds.embedly': 'wagtail.wagtailembeds.finders.embedly',
    'wagtail.wagtailembeds.embeds.oembed': 'wagtail.wagtailembeds.finders.oembed',
    'wagtail.wagtailembeds.finders.embedly.embedly': 'wagtail.wagtailembeds.finders.embedly',
    'wagtail.wagtailembeds.finders.oembed.oembed': 'wagtail.wagtailembeds.finders.oembed',
}


def import_finder_class(dotted_path):
    """
    Imports a finder class from a dotted path. If the dotted path points to a
    module, that module is imported and its "embed_finder_class" class returned.

    If not, this will assume the dotted path points to directly a class and
    will attempt to import that instead.
    """
    try:
        finder_module = import_module(dotted_path)
        return finder_module.embed_finder_class
    except ImportError as e:
        try:
            return import_string(dotted_path)
        except ImportError:
            six.reraise(ImportError, e, sys.exc_info()[2])


def _settings_deprecation_warning(key, suggestion):
    hint = 'WAGTAILEMBEDS_FINDERS = ' + pprint.pformat(suggestion)
    warnings.warn(
        "The `{}` setting is now deprecrated. Please replace this with `{}`".format(key, hint),
        category=RemovedInWagtail114Warning
    )


def _get_config_from_settings():
    if hasattr(settings, 'WAGTAILEMBEDS_FINDERS'):
        return settings.WAGTAILEMBEDS_FINDERS

    elif hasattr(settings, 'WAGTAILEMBEDS_EMBED_FINDER'):
        finder_name = settings.WAGTAILEMBEDS_EMBED_FINDER

        if finder_name in MOVED_FINDERS:
            finder_name = MOVED_FINDERS[finder_name]

        finders = [
            {
                'class': finder_name,
            }
        ]

        _settings_deprecation_warning('WAGTAILEMBEDS_EMBED_FINDER', finders)

        return finders

    elif hasattr(settings, 'WAGTAILEMBEDS_EMBEDLY_KEY'):
        finders = [
            {
                'class': 'wagtail.wagtailembeds.finders.embedly',
                'key': settings.WAGTAILEMBEDS_EMBEDLY_KEY,
            }
        ]

        _settings_deprecation_warning('WAGTAILEMBEDS_EMBEDLY_KEY', finders)

        return finders

    else:
        # Default to the oembed backend
        return [
            {
                'class': 'wagtail.wagtailembeds.finders.oembed',
            }
        ]


def get_finders():
    finders = []

    for finder_config in _get_config_from_settings():
        finder_config = finder_config.copy()
        cls = import_finder_class(finder_config.pop('class'))

        finders.append(cls(**finder_config))

    return finders
