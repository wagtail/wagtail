import six

from .translation import L18NMap, L18NListMap

try:
    from . import __maps
    tz_cities = L18NMap(__maps.tz_cities)
    territories = L18NMap(__maps.territories)

    # tz_fullnames requires a main dictionary and an auxiliary translations
    # dictionary (for components)

    _main_dict = dict(__maps.tz_cities)
    _aux_dict = {}
    for k, v in six.iteritems(__maps.tz_locations):
        if k in _main_dict:
            _main_dict[k] = v
        else:
            _aux_dict[k] = v

    tz_fullnames = L18NListMap('/', _aux_dict, _main_dict)

except ImportError:
    tz_cities = {}
    tz_fullnames = {}
    territories = {}
