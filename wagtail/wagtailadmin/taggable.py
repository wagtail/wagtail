from __future__ import absolute_import, unicode_literals

import warnings

from django.contrib.contenttypes.models import ContentType
from django.db.models import Count
from taggit.models import Tag

from wagtail.utils.deprecation import RemovedInWagtail18Warning
from wagtail.wagtailsearch import index


class TagSearchable(index.Indexed):
    """
    Mixin to provide a 'search' method, searching on the 'title' field and tags,
    for models that provide those things.
    """

    search_fields = [
        index.SearchField('title', partial_match=True, boost=10),
        index.RelatedFields('tags', [
            index.SearchField('name', partial_match=True, boost=10),
        ]),
    ]

    @classmethod
    def popular_tags(cls):
        content_type = ContentType.objects.get_for_model(cls)
        return Tag.objects.filter(
            taggit_taggeditem_items__content_type=content_type
        ).annotate(
            item_count=Count('taggit_taggeditem_items')
        ).order_by('-item_count')[:10]


warnings.warn(
    "The wagtail.wagtailadmin.taggable module is deprecated.",
    category=RemovedInWagtail18Warning, stacklevel=2
)
