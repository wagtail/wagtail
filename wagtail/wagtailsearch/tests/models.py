from django.db import models
from wagtail.wagtailsearch import Indexed


class SearchTest(models.Model, Indexed):
    title = models.CharField(max_length=255)
    content = models.TextField()
    live = models.BooleanField(default=False)
    published_date = models.DateField(null=True)

    search_fields = ['title', 'content', 'callable_indexed_field']
    search_filter_fields = ['live', 'published_date']

    def callable_indexed_field(self):
        return "Callable"


class SearchTestChild(SearchTest):
    extra_content = models.TextField()

    search_fields = ['extra_content']
