from django.urls import path

from wagtail.admin.views.pages.listing import IndexView
from wagtail.models import Page

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
    #: Required; the page model class that this viewset will work with.
    model = Page
    #: A list of ``wagtail.admin.ui.tables.Column`` instances for the columns in the listing.
    columns = IndexView.columns
    #: A subclass of ``wagtail.admin.filters.WagtailFilterSet``, which is a
    #: subclass of `django_filters.FilterSet <https://django-filter.readthedocs.io/en/stable/ref/filterset.html>`_.
    #: This will be passed to the ``filterset_class`` attribute of the index view.
    filterset_class = IndexView.filterset_class

    def get_index_view_kwargs(self, **kwargs):
        return {
            "index_url_name": self.get_url_name("index"),
            "index_results_url_name": self.get_url_name("index_results"),
            "model": self.model,
            "columns": self.columns,
            "filterset_class": self.filterset_class,
            **kwargs,
        }

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

    def get_urlpatterns(self):
        return [
            path("", self.index_view, name="index"),
            path("results/", self.index_results_view, name="index_results"),
        ]
