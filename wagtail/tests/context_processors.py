
def do_not_use_static_url(request):
    def exception():
        raise Exception("Do not use STATIC_URL in templates. Use the {% static %} templatetag (or {% versioned_static %} within admin templates) instead.")

    return {
        'STATIC_URL': lambda: exception(),
    }
