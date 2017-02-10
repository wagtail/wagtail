from __future__ import absolute_import, unicode_literals


def do_not_use_static_url(request):
    def exception():
        raise Exception("Do not use STATIC_URL in templates. Use the {% static %} templatetag instead.")

    return {
        'STATIC_URL': lambda: exception(),
    }
