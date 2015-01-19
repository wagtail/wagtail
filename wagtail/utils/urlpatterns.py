def decorate_urlpatterns(urlpatterns, decorator):
    for pattern in urlpatterns:
        if hasattr(pattern, 'url_patterns'):
            decorate_urlpatterns(pattern.url_patterns, decorator)

        if hasattr(pattern, '_callback'):
            pattern._callback = decorator(pattern.callback)

    return urlpatterns
