from __future__ import absolute_import, unicode_literals

from django import http
from django.utils.six.moves.urllib.parse import urlparse

from wagtail.wagtailredirects import models


def get_redirect(request, path):
    try:
        return models.Redirect.get_for_site(request.site).get(old_path=path)
    except models.Redirect.MultipleObjectsReturned:
        # We have a site-specific and a site-ambivalent redirect; prefer the specific one
        return models.Redirect.objects.get(site=request.site, old_path=path)
    except models.Redirect.DoesNotExist:
        return None


# Originally pinched from: https://github.com/django/django/blob/master/django/contrib/redirects/middleware.py
class RedirectMiddleware(object):
    def process_response(self, request, response):
        # No need to check for a redirect for non-404 responses.
        if response.status_code != 404:
            return response

        # If a middleware before `SiteMiddleware` returned a response the
        # `site` attribute was never set, ref #2120
        if not hasattr(request, 'site'):
            return response

        # Get the path
        path = models.Redirect.normalise_path(request.get_full_path())

        # Find redirect
        redirect = get_redirect(request, path)
        if redirect is None:
            # Get the path without the query string or params
            path_without_query = urlparse(path).path

            if path == path_without_query:
                # don't try again if we know we will get the same response
                return response

            redirect = get_redirect(request, path_without_query)
            if redirect is None:
                return response

        if redirect.is_permanent:
            return http.HttpResponsePermanentRedirect(redirect.link)
        else:
            return http.HttpResponseRedirect(redirect.link)
