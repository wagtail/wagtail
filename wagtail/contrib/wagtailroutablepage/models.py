from six import string_types

from django.http import Http404
from django.core.urlresolvers import RegexURLResolver

from wagtail.wagtailcore.models import Page
from wagtail.wagtailcore.url_routing import RouteResult


class RoutablePageMixin(object):
    """
    This class can be mixed in to a Page subclass to allow urlconfs to be
    embedded inside pages.
    """
    #: Set this to a tuple of ``django.conf.urls.url`` objects.
    subpage_urls = None

    @classmethod
    def get_subpage_urls(cls):
        if cls.subpage_urls:
            return cls.subpage_urls

        return ()

    @classmethod
    def get_resolver(cls):
        if '_routablepage_urlresolver' not in cls.__dict__:
            subpage_urls = cls.get_subpage_urls()
            cls._routablepage_urlresolver = RegexURLResolver(r'^/', subpage_urls)

        return cls._routablepage_urlresolver

    def reverse_subpage(self, name, args=None, kwargs=None):
        """
        This method does the same job as Djangos' built in
        "urlresolvers.reverse()" function for subpage urlconfs.
        """
        args = args or []
        kwargs = kwargs or {}

        return self.get_resolver().reverse(name, *args, **kwargs)

    def resolve_subpage(self, path):
        """
        This finds a view method/function from a URL path.
        """
        view, args, kwargs = self.get_resolver().resolve(path)

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
                return RouteResult(self, args=(view, args, kwargs))
            except Http404:
                pass

        return super(RoutablePageMixin, self).route(request, path_components)

    def serve(self, request, view, args, kwargs):
        return view(request, *args, **kwargs)

    def serve_preview(self, request, mode_name):
        view, args, kwargs = self.resolve_subpage('/')
        return view(request, *args, **kwargs)


class RoutablePage(RoutablePageMixin, Page):
    """
    This class extends Page by adding methods to allow urlconfs
    to be embedded inside pages
    """

    is_abstract = True

    class Meta:
        abstract = True
