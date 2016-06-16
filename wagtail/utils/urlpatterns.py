from __future__ import absolute_import, unicode_literals
from functools import update_wrapper
from django import VERSION as DJANGO_VERSION


def decorate_urlpatterns(urlpatterns, decorator):
    for pattern in urlpatterns:
        if hasattr(pattern, 'url_patterns'):
            decorate_urlpatterns(pattern.url_patterns, decorator)

        if DJANGO_VERSION <= (1, 9):
            if hasattr(pattern, '_callback'):
                pattern._callback = update_wrapper(decorator(pattern.callback), pattern.callback)
        else:
            if hasattr(pattern, 'callback') and callable(pattern.callback):
                pattern.callback = update_wrapper(decorator(pattern.callback), pattern.callback)

    return urlpatterns
