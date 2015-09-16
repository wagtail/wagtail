from django import http
from django.utils.six.moves.urllib.parse import urlparse

from wagtail.wagtailredirects import models


# Originally pinched from: https://github.com/django/django/blob/master/django/contrib/redirects/middleware.py
class RedirectMiddleware(object):
    def process_response(self, request, response):
        # No need to check for a redirect for non-404 responses.
        if response.status_code != 404:
            return response

        # Get the path
        path = models.Redirect.normalise_path(request.get_full_path())

        # Get the path without the query string or params
        path_without_query = urlparse(path)[2]

        # Find redirect
        try:
            redirect = models.Redirect.get_for_site(request.site).get(old_path=path)
        except models.Redirect.DoesNotExist:
            if path == path_without_query:
                # don't try again if we know we will get the same response
                return response

            try:
                redirect = models.Redirect.get_for_site(request.site).get(old_path=path_without_query)
            except models.Redirect.DoesNotExist:
                return response

        if redirect.is_permanent:
            return http.HttpResponsePermanentRedirect(redirect.link)
        else:
            return http.HttpResponseRedirect(redirect.link)
