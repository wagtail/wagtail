from functools import lru_cache
from importlib import import_module

from django.conf import settings
from django.utils.module_loading import import_string


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
            raise ImportError from e


def _get_config_from_settings():
    if hasattr(settings, "WAGTAILEMBEDS_FINDERS"):
        return settings.WAGTAILEMBEDS_FINDERS
    else:
        # Default to the oembed backend
        return [
            {
                "class": "wagtail.embeds.finders.oembed",
            }
        ]


@lru_cache(maxsize=None)
def get_finders():
    finders = []

    for finder_config in _get_config_from_settings():
        finder_config = finder_config.copy()
        cls = import_finder_class(finder_config.pop("class"))

        finders.append(cls(**finder_config))

    return finders
