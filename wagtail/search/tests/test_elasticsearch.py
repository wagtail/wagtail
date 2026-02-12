import unittest

from django.conf import settings
from django.test import TestCase

from wagtail.search.backends import get_search_backend
from wagtail.utils.deprecation import RemovedInWagtail80Warning


@unittest.skipIf(
    "elasticsearch_with_index_option" not in settings.WAGTAILSEARCH_BACKENDS,
    "No elasticsearch backend active",
)
class TestIndexOptionDeprecation(TestCase):
    def test_index_option_deprecation_warning(self):
        with self.assertWarnsMessage(
            RemovedInWagtail80Warning,
            "The INDEX option on Elasticsearch / OpenSearch backends is deprecated",
        ):
            backend = get_search_backend("elasticsearch_with_index_option")

        self.assertEqual(backend.index_prefix, "wagtailtest_")
