from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from django.urls import path

from wagtail.admin.views.pages.choose_parent import ChooseParentView
from wagtail.admin.views.pages.listing import ExplorableIndexView, IndexView
from wagtail.models import Page
from wagtail.utils.registry import ObjectTypeRegistry

from .base import ViewSet


class PageListingViewSet(ViewSet):
    """
    A viewset to present a flat listing of all pages of a specific type.
    All attributes and methods from :class:`~wagtail.admin.viewsets.base.ViewSet`
    are available.
    For more information on how to use this class, see :ref:`custom_page_listings`.
    """

    #: The view class to use for the index view; must be a subclass of ``wagtail.admin.views.pages.listing.IndexView``.
    index_view_class = IndexView
    #: The view class to use for choosing the parent page when creating a new page of this page type.
    choose_parent_view_class = ChooseParentView
    #: Required; the page model class that this viewset will work with.
    model = Page
    #: A list of ``wagtail.admin.ui.tables.Column`` instances for the columns in the listing.
    columns = IndexView.columns
    #: A subclass of ``wagtail.admin.filters.WagtailFilterSet``, which is a
    #: subclass of `django_filters.FilterSet <https://django-filter.readthedocs.io/en/stable/ref/filterset.html>`_.
    #: This will be passed to the ``filterset_class`` attribute of the index view.
    filterset_class = IndexView.filterset_class

    def get_common_view_kwargs(self, **kwargs):
        return super().get_common_view_kwargs(
            **{
                "header_icon": self.icon,
                "model": self.model,
                "index_url_name": self.get_url_name("index"),
                "add_url_name": self.get_url_name("choose_parent"),
                **kwargs,
            }
        )

    def get_index_view_kwargs(self, **kwargs):
        return {
            "index_results_url_name": self.get_url_name("index_results"),
            "columns": self.columns,
            "filterset_class": self.filterset_class,
            **kwargs,
        }

    def get_choose_parent_view_kwargs(self, **kwargs):
        return kwargs

    @property
    def index_view(self):
        return self.construct_view(
            self.index_view_class, **self.get_index_view_kwargs()
        )

    @property
    def index_results_view(self):
        return self.construct_view(
            self.index_view_class, **self.get_index_view_kwargs(), results_only=True
        )

    @property
    def choose_parent_view(self):
        return self.construct_view(
            self.choose_parent_view_class, **self.get_choose_parent_view_kwargs()
        )

    def get_urlpatterns(self):
        return [
            path("", self.index_view, name="index"),
            path("results/", self.index_results_view, name="index_results"),
            path("choose_parent/", self.choose_parent_view, name="choose_parent"),
        ]


class PageViewSet(PageListingViewSet):
    index_view_class = ExplorableIndexView
    columns = PageListingViewSet.UNDEFINED
    filterset_class = PageListingViewSet.UNDEFINED
    menu_url = None
    """Unused. There is no specific URL to link to for the menu item."""

    @property
    def views(self):
        return {
            "index": self.index_view,
            "index_results": self.index_results_view,
        }

    def get_view_by_name(self, name):
        return self.views[name]

    def get_url_name(self, view_name):
        """
        Unused. URL names are shared across all page types and are defined
        in the view classes directly.
        """
        return self.UNDEFINED

    def get_urlpatterns(self):
        """
        Unused. URL patterns are shared across all page types and defined in
        the main URL configuration. A thin view wrapper is used to route to the
        appropriate viewset based on the model of the page being accessed.
        """
        return []


class PageViewSetRegistry(ObjectTypeRegistry):
    def get_content_type_id_by_page_id(self, page_id):
        return (
            Page.objects.filter(pk=page_id)
            .values_list("content_type_id", flat=True)
            .get()
        )

    def get_page_model_by_content_type_id(self, content_type_id):
        # A stale content type's model_class() returns None, fall back to base Page.
        return ContentType.objects.get_for_id(content_type_id).model_class() or Page

    def get_by_page_id(self, page_id):
        """Get a viewset by the page ID whose model is registered."""
        # Only fetch the content type ID to optimise the query, as the full page
        # instance will be fetched later by the view itself.
        content_type_id = self.get_content_type_id_by_page_id(page_id)
        model = self.get_page_model_by_content_type_id(content_type_id)
        return self.get_by_type(model)

    def as_view(self, view_name, page_id_kwarg):
        """
        Create a view function that routes to the appropriate view based on the
        model of the page being accessed.

        This allows the use of custom views for specific page types, while still
        using the same URL pattern for all page types.
        """

        def view_router(request, *args, **kwargs):
            try:
                viewset = self.get_by_page_id(kwargs.get(page_id_kwarg))
            except ObjectDoesNotExist as e:
                # Page or ContentType not found
                raise Http404 from e
            view = viewset.get_view_by_name(view_name)
            return view(request, *args, **kwargs)

        return view_router


page_viewset_registry = PageViewSetRegistry()

# Provide a fallback default viewset for any page types that don't have a custom
# viewset registered
base_page_viewset = PageViewSet()
page_viewset_registry.register(Page, base_page_viewset)
