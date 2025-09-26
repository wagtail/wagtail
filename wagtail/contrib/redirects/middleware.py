from urllib.parse import urlparse

from django import http
from django.utils.deprecation import MiddlewareMixin
from django.utils.encoding import uri_to_iri

from wagtail.contrib.redirects import models
from wagtail.models import Site


def _get_redirect(request, path):
    if (
        "\0" in path
    ):  # reject URLs with null characters, which crash on Postgres (#4496)
        return None

    site = Site.find_for_request(request)
    redirects = models.Redirect.get_for_site(site).filter(old_path=path)
    if len(redirects) == 1:
        return redirects[0]
    elif len(redirects) > 1:
        # We have a site-specific and a site-ambivalent redirect; prefer the specific one
        for redirect in redirects:
            if redirect.site == site:
                return redirect
    else:
        return None


def get_redirect(request, path, *, exact_match=True):
    path = models.Redirect.normalise_path(path)
    redirect = _get_redirect(request, path)
    if redirect is None:
        # try unencoding the path
        redirect = _get_redirect(request, uri_to_iri(path))
    if redirect is None and not exact_match:
        # Get the path without the query string or params
        path_without_query = urlparse(path).path
        if path != path_without_query:
            redirect = get_redirect(request, path_without_query)
    return redirect


# Originally pinched from: https://github.com/django/django/blob/main/django/contrib/redirects/middleware.py
class RedirectMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        # No need to check for a redirect for non-404 responses.
        if response.status_code != 404:
            return response

        # Get the path
        path = request.get_full_path()

        # Find redirect
        redirect = get_redirect(request, path, exact_match=False)
        if redirect is None:
            return response

        if redirect.link is None:
            return response

        if redirect.is_permanent:
            return http.HttpResponsePermanentRedirect(redirect.link)
        else:
            return http.HttpResponseRedirect(redirect.link)
