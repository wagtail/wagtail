from django.db import connection, models
from django.test import TestCase

from wagtail.search import index
from wagtail.search.backends import get_search_backend


class Dummy(models.Model, index.Indexed):
    title = models.CharField(max_length=255)

    search_fields = [
        index.SearchField("title"),
    ]

    class Meta:
        app_label = "wagtailsearch"  # ensures unique table name
        managed = False  # prevent migrations


class HyphenSearchTest(TestCase):
    def setUp(self):
        self.backend = get_search_backend("default")
        # manually create table for Dummy
        with connection.schema_editor() as schema_editor:
            schema_editor.create_model(Dummy)

    def tearDown(self):
        # drop table after test
        with connection.schema_editor() as schema_editor:
            schema_editor.delete_model(Dummy)

    def test_hyphenated_numbers_index_and_search(self):
        obj = Dummy.objects.create(title="Model-123")
        results = list(self.backend.search("Model-123", Dummy))
        self.assertIn(obj, results)
