from functools import update_wrapper


def decorate_urlpatterns(urlpatterns, decorator):
    """Decorate all the views in the passed urlpatterns list with the given decorator"""
    for pattern in urlpatterns:
        if hasattr(pattern, 'url_patterns'):
            # this is an included RegexURLResolver; recursively decorate the views
            # contained in it
            decorate_urlpatterns(pattern.url_patterns, decorator)

        if getattr(pattern, 'callback', None):
            pattern.callback = update_wrapper(decorator(pattern.callback), pattern.callback)

    return urlpatterns
