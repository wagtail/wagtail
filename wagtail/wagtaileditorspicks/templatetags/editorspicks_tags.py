from django import template
from wagtail.wagtaileditorspicks.models import Query

register = template.Library()


@register.assignment_tag
def get_editors_picks(query_string):
    return Query.get(query_string).editors_picks.all()
