from django.conf.urls import patterns, url

urlpatterns = patterns(
    'wagtail.wagtailcore.views',
    # All front-end views are handled through Wagtail's core.views.serve mechanism.
    # Here we match a (possibly empty) list of path segments, each followed by
    # a '/'. If a trailing slash is not present, we leave CommonMiddleware to
    # handle it as usual (i.e. redirect it to the trailing slash version if
    # settings.APPEND_SLASH is True)
    url(r'^((?:[\w\-]+/)*)$', 'serve')
)
