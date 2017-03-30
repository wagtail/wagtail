from __future__ import absolute_import, unicode_literals


# Adapted from https://djangosnippets.org/snippets/10563/
# original author bernd-wechner
def to_datetimepicker_format(python_format_string):
    """
    Given a python datetime format string, attempts to convert it to
    the nearest PHP datetime format string possible.
    """
    python2PHP = {
        "%a": "D",
        "%A": "l",
        "%b": "M",
        "%B": "F",
        "%c": "",
        "%d": "d",
        "%H": "H",
        "%I": "h",
        "%j": "z",
        "%m": "m",
        "%M": "i",
        "%p": "A",
        "%S": "s",
        "%U": "",
        "%w": "w",
        "%W": "W",
        "%x": "",
        "%X": "",
        "%y": "y",
        "%Y": "Y",
        "%Z": "e",
    }

    php_format_string = python_format_string
    for py, php in python2PHP.items():
        php_format_string = php_format_string.replace(py, php)

    return php_format_string
