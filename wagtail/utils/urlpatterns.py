from __future__ import absolute_import, unicode_literals
from functools import update_wrapper
from django import VERSION as DJANGO_VERSION


def decorate_urlpatterns(urlpatterns, decorator):
    """Decorate all the views in the passed urlpatterns list with the given decorator"""
    for pattern in urlpatterns:
        if hasattr(pattern, 'url_patterns'):
            # this is an included RegexURLResolver; recursively decorate the views
            # contained in it
            decorate_urlpatterns(pattern.url_patterns, decorator)

        if DJANGO_VERSION < (1, 10):
            # Prior to Django 1.10, RegexURLPattern accepted both strings and callables as
            # the callback parameter; `callback` is a property that consistently returns it as
            # a callable.
            #
            # * if RegexURLPattern was given a string, _callback will be None, and will be
            #   populated on the first call to the `callback` property
            # * if RegexURLPattern was given a callable, _callback will be set to that callable,
            #   and the `callback` property will return it
            #
            # In either case, we wrap the result of `callback` and write it back to `_callback`,
            # so that future calls to `callback` will return our wrapped version.

            if hasattr(pattern, '_callback'):
                pattern._callback = update_wrapper(decorator(pattern.callback), pattern.callback)
        else:
            # In Django 1.10 and above, RegexURLPattern only accepts a callable as the callback
            # parameter; this is directly accessible as the `callback` attribute.
            if getattr(pattern, 'callback', None):
                pattern.callback = update_wrapper(decorator(pattern.callback), pattern.callback)

    return urlpatterns
