from modelcluster.fields import ParentalKey

from wagtail.wagtailcore.models import Page


def used_by(self):
    """Returns the pages that an object was used in."""

    pages = Page.objects.none()

    # get all the relation objects for self
    relations = type(self)._meta.get_all_related_objects(
        include_hidden=True,
        include_proxy_eq=True
    )
    for relation in relations:
        # if the relation is between self and a page, get the page
        if issubclass(relation.model, Page):
            pages |= Page.objects.filter(
                id__in=relation.model._base_manager.filter(**{
                    relation.field.name: self.id
                }).values_list('id', flat=True)
            )
        else:
        # if the relation is between self and an object that has a page as a
        # property, return the page
            for f in relation.model._meta.fields:
                if isinstance(f, ParentalKey) and issubclass(f.rel.to, Page):
                    pages |= Page.objects.filter(
                        id__in=relation.model._base_manager.filter(
                            **{
                                relation.field.name: self.id
                            }).values_list(f.attname, flat=True)
                    )

    return pages
