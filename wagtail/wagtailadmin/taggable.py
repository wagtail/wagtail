from taggit.models import Tag

from django.contrib.contenttypes.models import ContentType
from django.db.models import Count

from wagtail.wagtailsearch import index


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
    def popular_tags(cls):
        content_type = ContentType.objects.get_for_model(cls)
        return Tag.objects.filter(
            taggit_taggeditem_items__content_type=content_type
        ).annotate(
            item_count=Count('taggit_taggeditem_items')
        ).order_by('-item_count')[:10]
