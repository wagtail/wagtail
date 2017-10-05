from __future__ import absolute_import, unicode_literals

import collections

from django.utils import six


def deep_update(source, overrides):
    """Update a nested dictionary or similar mapping.

    Modify ``source`` in place.
    """
    items = six.iteritems(overrides)

    for key, value in items:
        if isinstance(value, collections.Mapping) and value:
            returned = deep_update(source.get(key, {}), value)
            source[key] = returned
        else:
            source[key] = overrides[key]
    return source
