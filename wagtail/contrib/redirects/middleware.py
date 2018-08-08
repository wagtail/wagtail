from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from django import http
from django.utils.deprecation import MiddlewareMixin
from django.utils.encoding import uri_to_iri

from wagtail.contrib.redirects import models


def _get_redirect(request, path):
    try:
        return models.Redirect.get_for_site(request.site).get(old_path=path)
    except models.Redirect.MultipleObjectsReturned:
        # We have a site-specific and a site-ambivalent redirect; prefer the specific one
        return models.Redirect.objects.get(site=request.site, old_path=path)
    except models.Redirect.DoesNotExist:
        return None


def get_redirect(request, path):
    redirect = _get_redirect(request, path)
    if not redirect:
        # try unencoding the path
        redirect = _get_redirect(request, uri_to_iri(path))
    return redirect


def append_querystring(redirect, request_qs):
    """
    Returns the redirected URL with a querystring, with any params specified in the old_path
    filtered out, and any other params passed through.
    """
    old_path_qs_params = parse_qs(urlparse(redirect.old_path).query, keep_blank_values=True)
    redirect_qs_params = parse_qs(urlparse(redirect.link).query, keep_blank_values=True)
    request_qs_params = parse_qs(request_qs, keep_blank_values=True)

    # Filter out any key-value pairs from the request qs that are specified in the old path.
    pass_through_params = {
        key: val for key, val in request_qs_params.items()
        if old_path_qs_params.get(key) != val
    }

    # Construct a new querystring, combining those in the redirect target and the pass-through params.
    new_qs_params = {**redirect_qs_params}
    for key, val in pass_through_params.items():
        try:
            new_qs_params[key] += val
        except KeyError:
            new_qs_params[key] = val

    new_qs = urlencode(new_qs_params, doseq=True)
    if new_qs:
        # Replace the original requested querystring with the new one
        url_parts = list(urlparse(redirect.link))
        url_parts[4] = new_qs
        return urlunparse(url_parts)
    else:
        # No querystring to return
        return redirect.link


# Originally pinched from: https://github.com/django/django/blob/master/django/contrib/redirects/middleware.py
class RedirectMiddleware(MiddlewareMixin):
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

        request_qs = request.META.get('QUERY_STRING', '')
        redirect_url = append_querystring(redirect, request_qs)

        if redirect.is_permanent:
            return http.HttpResponsePermanentRedirect(redirect_url)
        else:
            return http.HttpResponseRedirect(redirect_url)
