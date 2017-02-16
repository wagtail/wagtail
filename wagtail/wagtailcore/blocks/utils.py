from __future__ import absolute_import, unicode_literals

import inspect
import re
import sys

# helpers for Javascript expression formatting


def indent(string, depth=1):
    """indent all non-empty lines of string by 'depth' 4-character tabs"""
    return re.sub(r'(^|\n)([^\n]+)', '\g<1>' + ('    ' * depth) + '\g<2>', string)


def js_dict(d):
    """
    Return a Javascript expression string for the dict 'd'.
    Keys are assumed to be strings consisting only of JS-safe characters, and will be quoted but not escaped;
    values are assumed to be valid Javascript expressions and will be neither escaped nor quoted (but will be
    wrapped in parentheses, in case some awkward git decides to use the comma operator...)
    """
    dict_items = [
        indent("'%s': (%s)" % (k, v))
        for (k, v) in d.items()
    ]
    return "{\n%s\n}" % ',\n'.join(dict_items)


def accepts_kwarg(func, kwarg):
    """
    Determine whether the callable `func` has a signature that accepts the keyword argument `kwarg`
    """
    if sys.version_info >= (3, 3):
        signature = inspect.signature(func)
        try:
            signature.bind_partial(**{kwarg: None})
            return True
        except TypeError:
            return False
    else:
        # Fall back on inspect.getargspec, available on Python 2.7 but deprecated since 3.5
        argspec = inspect.getargspec(func)
        return (kwarg in argspec.args) or (argspec.keywords is not None)
