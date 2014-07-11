from django.conf import settings

from modelcluster.fields import ParentalKey

from wagtail.wagtailcore.models import Page


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
        else:
            parental_keys = get_parental_keys(r)
            for parental_key in parental_keys:
                result.append(getattr(r, parental_key.name))

    return result


def usage_count(self):
    """Returns the number of times that an obect has been used in a page"""

    if not hasattr(settings, 'USAGE_COUNT') or not settings.USAGE_COUNT:
        return None

    return len(used_by(self))


def get_parental_keys(obj):
    return [field for field in obj._meta.fields if type(field) == ParentalKey]
