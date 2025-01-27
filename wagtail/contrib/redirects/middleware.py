from urllib.parse import urlparse

from django import http
from django.db.models import Case, IntegerField, Q, When
from django.utils.deprecation import MiddlewareMixin
from django.utils.encoding import iri_to_uri

from wagtail.contrib.redirects import models
from wagtail.models import Site


def get_redirect(request, path):
    if "\0" in path:
        # reject paths with null characters, which crash on Postgres (#4496)
        return None

    site = Site.find_for_request(request)

    encoded_path = iri_to_uri(path)
    match_paths = [path, encoded_path]
    path_without_query = urlparse(path).path
    if path_without_query != path:
        encoded_path_without_query = iri_to_uri(path_without_query)
        match_paths.extend([path_without_query, encoded_path_without_query])
    else:
        encoded_path_without_query = encoded_path

    queryset = models.Redirect.objects.filter(old_path__in=match_paths)
    if site:
        queryset = queryset.filter(Q(site=site) | Q(site__isnull=True)).annotate(
            priority=Case(
                # A full-url match for the current site is most favourable
                # encoded matches less so, as they are likely to be less recent
                When(site_id=site.id, old_path=path, then=1),
                When(site_id=site.id, old_path=encoded_path, then=2),
                # A site-ambivalent full-url is next best
                # Again, encoded matches are slightly less favourable
                When(site_id=None, old_path=path, then=3),
                When(site_id=None, old_path=encoded_path, then=4),
                # A path-only match for the current site is next best
                # Again, encoded matches are slightly less favourable
                When(site_id=site.id, old_path=path_without_query, then=5),
                When(site_id=site.id, old_path=encoded_path_without_query, then=6),
                # A decodeed site-ambivalent path-only match is next best
                When(site_id=None, old_path=path_without_query, then=7),
                # Anything else must be an encoded site-ambivalent path-only match
                default=8,
                output_field=IntegerField(),
            )
        )
    else:
        queryset = queryset.filter(site__isnull=True).annotate(
            priority=Case(
                When(old_path=path, then=1),
                When(old_path=encoded_path, then=2),
                When(old_path=path_without_query, then=3),
                default=4,
                output_field=IntegerField(),
            )
        )
    return queryset.order_by("priority").first()


# Originally pinched from: https://github.com/django/django/blob/main/django/contrib/redirects/middleware.py
class RedirectMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        # No need to check for a redirect for non-404 responses.
        if response.status_code != 404:
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

        if redirect.link is None:
            return response

        if redirect.is_permanent:
            return http.HttpResponsePermanentRedirect(redirect.link)
        else:
            return http.HttpResponseRedirect(redirect.link)
