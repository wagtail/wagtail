from __future__ import unicode_literals

from six import string_types
import warnings

from django.http import Http404
from django.core.urlresolvers import RegexURLResolver
from django.conf.urls import url

from wagtail.wagtailcore.models import Page
from wagtail.wagtailcore.url_routing import RouteResult
from wagtail.utils.deprecation import RemovedInWagtail12Warning


_creation_counter = 0


def route(pattern, name=None):
    def decorator(view_func):
        global _creation_counter
        _creation_counter += 1

        # Make sure page has _routablepage_routes attribute
        if not hasattr(view_func, '_routablepage_routes'):
            view_func._routablepage_routes = []

        # Add new route to view
        view_func._routablepage_routes.append((
            url(pattern, view_func, name=(name or view_func.__name__)),
            _creation_counter,
        ))

        return view_func

    return decorator


class RoutablePageMixin(object):
    """
    This class can be mixed in to a Page subclass to allow urlconfs to be
    embedded inside pages.
    """
    #: Set this to a tuple of ``django.conf.urls.url`` objects.
    subpage_urls = None

    @classmethod
    def check(cls, **kwargs):
        if cls.subpage_urls and not hasattr(cls, '_disable_subpage_urls_deprecation_warning'):
            warnings.warn(
                "{app_label}.{classname}: subpage_urls is deprecated. Use the "
                "@route decorator to define page routes instead.".format(
                    app_label=cls._meta.app_label,
                    classname=cls.__name__,
                ), RemovedInWagtail12Warning)

        return super(RoutablePageMixin, cls).check(**kwargs)

    @classmethod
    def get_subpage_urls(cls):
        # Old style
        if cls.subpage_urls:
            return cls.subpage_urls

        # New style
        routes = []
        for attr in dir(cls):
            val = getattr(cls, attr)
            if hasattr(val, '_routablepage_routes'):
                routes.extend(val._routablepage_routes)

        return tuple([
            route[0]
            for route in sorted(routes, key=lambda route: route[1])
        ])

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

        if self.subpage_urls:  # Old style
            # If view is a string, find it as an attribute of self
            if isinstance(view, string_types):
                view = getattr(self, view)

        else:  # New style
            # Bind the method
            view = view.__get__(self, type(self))

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
