from taggit.models import Tag

from django.contrib.contenttypes.models import ContentType
from django.db.models import Count
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from wagtail.wagtailsearch import Indexed, Search


class TagSearchable(Indexed):
    """
    Mixin to provide a 'search' method, searching on the 'title' field and tags,
    for models that provide those things.
    """

    indexed_fields = {
        'title': {
            'type': 'string',
            'analyzer': 'edgengram_analyzer',
            'boost': 10,
        },
        'get_tags': {
            'type': 'string',
            'analyzer': 'edgengram_analyzer',
            'boost': 10,
        },
    }

    @property
    def get_tags(self):
        return ' '.join([tag.name for tag in self.tags.all()])

    @classmethod
    def search(cls, q, results_per_page=None, page=1, prefetch_tags=False, filters={}):
        # Run search query
        if prefetch_tags:
            results = Search().search(q, cls, prefetch_related=['tagged_items__tag'], filters=filters)
        else:
            results = Search().search(q, cls, filters=filters)

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
