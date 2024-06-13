from collections.abc import Mapping


def deep_update(source, overrides):
    """Update a nested dictionary or similar mapping.

    Modify ``source`` in place.
    """
    for key, value in overrides.items():
        if isinstance(value, Mapping) and value:
            returned = deep_update(source.get(key, {}), value)
            source[key] = returned
        else:
            source[key] = overrides[key]
    return source


def flatten_choices(choices):
    """
    Convert potentially grouped choices into a flat dict of choices.

    flatten_choices([(1, '1st'), (2, '2nd')]) -> {1: '1st', 2: '2nd'}
    flatten_choices([('Group', [(1, '1st'), (2, '2nd')])]) -> {1: '1st', 2: '2nd'}
    flatten_choices({'Group': {'1': '1st', '2': '2nd'}}) -> {'1': '1st', '2': '2nd'}
    """
    ret = {}

    to_unpack = choices.items() if isinstance(choices, dict) else choices

    for key, value in to_unpack:
        if isinstance(value, (list, tuple)):
            # grouped choices (category, sub choices)
            for sub_key, sub_value in value:
                ret[str(sub_key)] = sub_value
        elif isinstance(value, (dict)):
            # grouped choices using dict (category, sub choices)
            for sub_key, sub_value in value.items():
                ret[str(sub_key)] = sub_value
        else:
            # choice (key, display value)
            ret[str(key)] = value
    return ret
