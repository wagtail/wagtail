import warnings

from taggit.models import Tag

from django.contrib.contenttypes.models import ContentType
from django.db.models import Count
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from wagtail.wagtailsearch import index
from wagtail.utils.deprecation import RemovedInWagtail14Warning


class TagSearchable(index.Indexed):
    """
    Mixin to provide a 'search' method, searching on the 'title' field and tags,
    for models that provide those things.
    """

    search_fields = (
        index.SearchField('title', partial_match=True, boost=10),
        index.RelatedFields('tags', [
            index.SearchField('name', partial_match=True, boost=10),
        ]),
    )

    @classmethod
    def get_indexed_objects(cls):
        return super(TagSearchable, cls).get_indexed_objects().prefetch_related('tagged_items__tag')

    @classmethod
    def search(cls, q, results_per_page=None, page=1, prefetch_tags=False, filters={}):
        warnings.warn(
            "The {class_name}.search() method is deprecated. "
            "Please use the {class_name}.objects.search() method instead.".format(class_name=cls.__name__),
            RemovedInWagtail14Warning, stacklevel=2)

        results = cls.objects.all()

        if prefetch_tags:
            results = results.prefetch_related('tagged_items__tag')

        if filters:
            results = results.filter(**filters)

        results = results.search(q)

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

    @classmethod
    def popular_tags(cls):
        content_type = ContentType.objects.get_for_model(cls)
        return Tag.objects.filter(
            taggit_taggeditem_items__content_type=content_type
        ).annotate(
            item_count=Count('taggit_taggeditem_items')
        ).order_by('-item_count')[:10]
