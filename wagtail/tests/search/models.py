from django.db import models

from taggit.managers import TaggableManager

from wagtail.wagtailsearch import index


class SearchTest(models.Model, index.Indexed):
    title = models.CharField(max_length=255)
    content = models.TextField()
    live = models.BooleanField(default=False)
    published_date = models.DateField(null=True)
    tags = TaggableManager()

    search_fields = [
        index.SearchField('title', partial_match=True),
        index.RelatedFields('tags', [
            index.SearchField('name', partial_match=True),
            index.FilterField('slug'),
        ]),
        index.SearchField('content'),
        index.SearchField('callable_indexed_field'),
        index.FilterField('title'),
        index.FilterField('live'),
        index.FilterField('published_date'),
    ]

    def callable_indexed_field(self):
        return "Callable"

    @classmethod
    def get_indexed_objects(cls):
        indexed_objects = super(SearchTest, cls).get_indexed_objects()

        # Exclude SearchTests that have a SearchTestChild to stop update_index creating duplicates
        if cls is SearchTest:
            indexed_objects = indexed_objects.exclude(
                id__in=SearchTestChild.objects.all().values_list('searchtest_ptr_id', flat=True)
            )

        # Exclude SearchTests that have the title "Don't index me!"
        indexed_objects = indexed_objects.exclude(title="Don't index me!")

        return indexed_objects

    def get_indexed_instance(self):
        # Check if there is a SearchTestChild that descends from this
        child = SearchTestChild.objects.filter(searchtest_ptr_id=self.id).first()

        # Return the child if there is one, otherwise return self
        return child or self

    def __str__(self):
        return self.title


class SearchTestChild(SearchTest):
    subtitle = models.CharField(max_length=255, null=True, blank=True)
    extra_content = models.TextField()
    page = models.ForeignKey('wagtailcore.Page', null=True, blank=True)

    search_fields = SearchTest.search_fields + [
        index.SearchField('subtitle', partial_match=True),
        index.SearchField('extra_content'),
        index.RelatedFields('page', [
            index.SearchField('title', partial_match=True),
            index.SearchField('search_description'),
            index.FilterField('live'),
        ]),
    ]
