from django import template

from wagtail.wagtailsearch.models import Query


register = template.Library()


@register.assignment_tag()
def get_search_picks(search_query):
    return Query.get(search_query).editors_picks.all()
