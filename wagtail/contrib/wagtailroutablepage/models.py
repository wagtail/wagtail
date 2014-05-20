from six import string_types

from django.http import Http404
from django.core.urlresolvers import get_resolver
from django.core.exceptions import ImproperlyConfigured

from wagtail.wagtailcore.models import Page
from wagtail.wagtailcore.url_routing import RouteResult


class RoutablePage(Page):
    """
    This class extends Page by adding methods to allow urlconfs to be embedded inside pages
    """
    subpage_urls = None

    def reverse_subpage(self, name, args=None, kwargs=None):
        """
        This method does the same job as Djangos' built in "urlresolvers.reverse()" function for subpage urlconfs.
        """
        args = args or []
        kwargs = kwargs or {}

        if self.subpage_urls is None:
            raise ImproperlyConfigured("You must set 'subpage_urls' on " + type(self).__name__)

        resolver = get_resolver(self.subpage_urls)
        return resolver.reverse(name, *args, **kwargs)

    def resolve_subpage(self, path):
        """
        This finds a view method/function from a URL path.
        """
        if self.subpage_urls is None:
            raise ImproperlyConfigured("You must set 'subpage_urls' on " + type(self).__name__)

        resolver = get_resolver(self.subpage_urls)
        view, args, kwargs = resolver.resolve(path)

        # If view is a string, find it as an attribute of self
        if isinstance(view, string_types):
            view = getattr(self, view)

        return view, args, kwargs

    def route(self, request, path_components):
        """
        This hooks the subpage urls into Wagtails routing.
        """
        if self.live:
            try:
                path = '/'
                if path_components:
                    path += '/'.join(path_components) + '/'

                view, args, kwargs = self.resolve_subpage(path)
                return RouteResult(self, view=view, args=args, kwargs=kwargs)
            except Http404:
                pass

        return super(RoutablePage, self).route(request, path_components)

    is_abstract = True

    class Meta:
        abstract = True
