from wagtail.wagtailcore.models import Page
from django.conf import settings


def used_by(self):
    """Returns the pages that an object was used in."""

    if not hasattr(settings, 'USAGE_COUNT') or not settings.USAGE_COUNT:
        return []

    related_objects = []
    result = []

    relations = self._meta.get_all_related_objects(
        include_hidden=True,
        include_proxy_eq=True
    )
    for relation in relations:
        related_objects.extend(list(relation.model._base_manager.filter(
            **{relation.field.name: self.id}
        )))
    for r in related_objects:
        if isinstance(r, Page):
            result.append(r)
        elif hasattr(r, 'page'):
            result.append(r.page)

    return result


def usage_count(self):
    """Returns the number of times that an obect has been used in a page"""

    if not hasattr(settings, 'USAGE_COUNT') or not settings.USAGE_COUNT:
        return None

    return len(used_by(self))
