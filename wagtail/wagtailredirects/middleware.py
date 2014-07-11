from django import http

from wagtail.wagtailredirects import models


# Originally pinched from: https://github.com/django/django/blob/master/django/contrib/redirects/middleware.py
class RedirectMiddleware(object):
    def process_response(self, request, response):
        # No need to check for a redirect for non-404 responses.
        if response.status_code != 404:
            return response

        # Get the path
        path = models.Redirect.normalise_path(request.get_full_path())

        # Find redirect
        try:
            redirect = models.Redirect.get_for_site(request.site).get(old_path=path)

            if redirect.is_permanent:
                return http.HttpResponsePermanentRedirect(redirect.link)
            else:
                return http.HttpResponseRedirect(redirect.link)
        except:
            pass

        return response
