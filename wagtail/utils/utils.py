from __future__ import absolute_import, unicode_literals

import collections
import sys


def deep_update(source, overrides):
    """Update a nested dictionary or similar mapping.

    Modify ``source`` in place.
    """
    if sys.version_info >= (3, 0):
        items = overrides.items()
    else:
        items = overrides.iteritems()

    for key, value in items:
        if isinstance(value, collections.Mapping) and value:
            returned = deep_update(source.get(key, {}), value)
            source[key] = returned
        else:
            source[key] = overrides[key]
    return source
