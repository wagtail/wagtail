from modelcluster.fields import ParentalKey

from wagtail.wagtailcore.models import Page


def get_object_usage(obj):
    "Returns a queryset of pages that link to a particular object"

    pages = Page.objects.none()

    # get all the relation objects for obj
    relations = type(obj)._meta.get_all_related_objects(
        include_hidden=True,
        include_proxy_eq=True
    )
    for relation in relations:
        # if the relation is between obj and a page, get the page
        if issubclass(relation.model, Page):
            pages |= Page.objects.filter(
                id__in=relation.model._base_manager.filter(**{
                    relation.field.name: obj.id
                }).values_list('id', flat=True)
            )
        else:
        # if the relation is between obj and an object that has a page as a
        # property, return the page
            for f in relation.model._meta.fields:
                if isinstance(f, ParentalKey) and issubclass(f.rel.to, Page):
                    pages |= Page.objects.filter(
                        id__in=relation.model._base_manager.filter(
                            **{
                                relation.field.name: obj.id
                            }).values_list(f.attname, flat=True)
                    )

    return pages
