import warnings

from django.http import HttpResponse, Http404


def serve(request, path):
    # we need a valid Site object corresponding to this request (set in wagtail.wagtailcore.middleware.SiteMiddleware)
    # in order to proceed
    if not request.site:
        raise Http404

    path_components = [component for component in path.split('/') if component]
    page = request.site.root_page.specific.route(request, path_components)
    if isinstance(page, HttpResponse):
        warnings.warn(
            "Page.route should return a Page, not an HttpResponse",
            DeprecationWarning
        )
        return page

    return page.serve(request)
