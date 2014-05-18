from taggit.models import Tag

from django.contrib.contenttypes.models import ContentType
from django.db.models import Count
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from wagtail.wagtailsearch import Indexed, get_search_backend


class TagSearchable(Indexed):
    """
    Mixin to provide a 'search' method, searching on the 'title' field and tags,
    for models that provide those things.
    """

    search_fields = {
        'title': dict(partial_match=True, boost=10),
        'get_tags': dict(partial_match=True, boost=10),
    }

    @property
    def get_tags(self):
        return ' '.join([tag.name for tag in self.tags.all()])

    @classmethod
    def search(cls, query_string, results_per_page=None, page=1, prefetch_tags=False, filters={}):
        # Create query set
        query_set = cls.objects.all()

        # Apply filters
        query_set = query_set.filter(**filters)

        # Prefetch tags
        if prefetch_tags:
            query_set = query_set.prefetch_related('tagged_items__tag')

        # Get results
        search_backend = get_search_backend()
        results = search_backend.search(query_set, query_string)

        # If results_per_page is set, return a paginator
        if results_per_page is not None:
            paginator = Paginator(results, results_per_page)
            try:
                return paginator.page(page)
            except PageNotAnInteger:
                return paginator.page(1)
            except EmptyPage:
                return paginator.page(paginator.num_pages)
        else:
            return results

    def prefetched_tags(self):
        # a hack to do the equivalent of self.tags.all() but take advantage of the
        # prefetch_related('tagged_items__tag') in the above search method, so that we can
        # output the list of tags on each result without doing a further query
        return [tagged_item.tag for tagged_item in self.tagged_items.all()]

    @classmethod
    def popular_tags(cls):
        content_type = ContentType.objects.get_for_model(cls)
        return Tag.objects.filter(
            taggit_taggeditem_items__content_type=content_type
        ).annotate(
            item_count=Count('taggit_taggeditem_items')
        ).order_by('-item_count')[:10]
