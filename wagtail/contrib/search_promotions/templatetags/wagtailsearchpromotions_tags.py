from django import template

from wagtail.contrib.search_promotions.models import SearchPromotion
from wagtail.search.models import Query

register = template.Library()


@register.simple_tag
def get_search_promotions(search_query):
    if search_query:
        return Query.get(search_query).editors_picks.all()
    else:
        return SearchPromotion.objects.none()
