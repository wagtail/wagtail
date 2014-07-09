from wagtail.wagtailcore.models import Page


def usage_count(self):
    """The number of times that an obect has been used"""
    count = 0
    relations = self._meta.get_all_related_objects(
        include_hidden=True,
        include_proxy_eq=True
    )
    for relation in relations:
        count += relation.model._base_manager.filter(
            **{relation.field.name: self.id}
        ).count()
    return count


def used_by(self):
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
