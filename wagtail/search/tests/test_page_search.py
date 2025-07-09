from django.conf import settings
from django.db.models import F
from django.test import TestCase

from wagtail.models import Page
from wagtail.search.backends import get_search_backend
from wagtail.search.backends.base import (
    BaseSearchQueryCompiler,
    BaseSearchResults,
    OrderByFieldError,
)


class PageSearchTests:
    # A TestCase with this class mixed in will be dynamically created
    # for each search backend defined in WAGTAILSEARCH_BACKENDS, with the backend name available
    # as self.backend_name

    fixtures = ["test.json"]

    def setUp(self):
        self.backend = get_search_backend(self.backend_name)
        self.reset_index()
        for page in Page.objects.all():
            self.backend.add(page)
        self.refresh_index()

    def reset_index(self):
        if self.backend.rebuilder_class:
            index = self.backend.get_index_for_model(Page)
            rebuilder = self.backend.rebuilder_class(index)
            index = rebuilder.start()
            index.add_model(Page)
            rebuilder.finish()

    def refresh_index(self):
        index = self.backend.get_index_for_model(Page)
        if index:
            index.refresh()

    def test_order_by_title(self):
        list(
            Page.objects.order_by("title").search(
                "blah", order_by_relevance=False, backend=self.backend_name
            )
        )

    def test_order_by_last_published_at_with_drafts_first(self):
        qs = Page.objects.order_by(F("last_published_at").asc(nulls_first=True))
        if self.backend.query_compiler_class.HANDLES_ORDER_BY_EXPRESSIONS:
            qs.autocomplete("blah", order_by_relevance=False, backend=self.backend_name)
        else:
            with self.assertRaises(OrderByFieldError) as ctx:
                qs.autocomplete(
                    "blah", order_by_relevance=False, backend=self.backend_name
                )
            self.assertIn(
                'Cannot sort search results with "OrderBy(F(last_published_at), descending=False)".',
                str(ctx.exception),
            )

    def test_search_specific_queryset(self):
        list(Page.objects.specific().search("bread", backend=self.backend_name))

    def test_search_specific_queryset_with_fields(self):
        list(
            Page.objects.specific().search(
                "bread", fields=["title"], backend=self.backend_name
            )
        )


for backend_name in settings.WAGTAILSEARCH_BACKENDS.keys():
    test_name = str("Test%sBackend" % backend_name.title())
    globals()[test_name] = type(
        test_name,
        (
            PageSearchTests,
            TestCase,
        ),
        {"backend_name": backend_name},
    )


class TestBaseSearchResults(TestCase):
    def test_get_item_no_results(self):
        # Ensure that, if there are no results, we do not attempt to get the entire search index.
        base_search_results = BaseSearchResults(
            "BackendIrrelevant",
            BaseSearchQueryCompiler(Page.objects.none(), "query"),
        )
        obj = base_search_results[0:0]
        self.assertEqual(obj.start, 0)
        self.assertEqual(obj.stop, 0)
