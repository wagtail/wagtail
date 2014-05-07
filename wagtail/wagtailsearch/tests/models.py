from django.db import models
from wagtail.wagtailsearch import Indexed


class SearchTest(models.Model, Indexed):
    title = models.CharField(max_length=255)
    content = models.TextField()
    live = models.BooleanField(default=False)
    published_date = models.DateField(null=True)

    search_fields = ['title', 'content', 'callable_indexed_field']
    search_filter_fields = ['title', 'live', 'published_date']

    def callable_indexed_field(self):
        return "Callable"


class SearchTestChild(SearchTest):
    extra_content = models.TextField()

    search_fields = ['extra_content']


class SearchTestOldConfig(models.Model, Indexed):
    """
    This tests that the Indexed class can correctly handle models that
    use the old "indexed_fields" configuration format.
    """
    indexed_fields = {
        # A search field with predictive search and boosting
        'title': {
            'type': 'string',
            'analyzer': 'edgengram_analyzer',
            'boost': 100,
        },

        # A filter field
        'live': {
            'type': 'boolean',
            'index': 'not_analyzed',
        },
    }

class SearchTestOldConfigList(models.Model, Indexed):
    """
    This tests that the Indexed class can correctly handle models that
    use the old "indexed_fields" configuration format using a list.
    """
    indexed_fields = ['title', 'content']
