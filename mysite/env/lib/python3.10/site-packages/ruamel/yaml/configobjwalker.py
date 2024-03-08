# coding: utf-8

import warnings

from ruamel.yaml.util import configobj_walker as new_configobj_walker

from typing import Any


def configobj_walker(cfg: Any) -> Any:
    warnings.warn(
        'configobj_walker has moved to ruamel.yaml.util, please update your code',
        stacklevel=2,
    )
    return new_configobj_walker(cfg)
