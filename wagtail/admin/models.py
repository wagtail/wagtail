from django.contrib.contenttypes.models import ContentType
from django.db.models import Count, Model
from modelcluster.fields import ParentalKey
from taggit.models import Tag

# The panels module extends Page with some additional attributes required by
# wagtail admin (namely, base_form_class and get_edit_handler). Importing this within
# wagtail.admin.models ensures that this happens in advance of running wagtail.admin's
# system checks.
from wagtail.admin import panels  # NOQA
from wagtail.models import Page


# A dummy model that exists purely to attach the access_admin permission type to, so that it
# doesn't get identified as a stale content type and removed by the remove_stale_contenttypes
# management command.
class Admin(Model):
    class Meta:
        default_permissions = (
            []
        )  # don't create the default add / change / delete / view perms
        permissions = [
            ("access_admin", "Can access Wagtail admin"),
        ]


def get_object_usage(obj):
    """Returns a queryset of pages that link to a particular object"""

    pages = Page.objects.none()

    # get all the relation objects for obj
    relations = [
        f
        for f in type(obj)._meta.get_fields(include_hidden=True)
        if (f.one_to_many or f.one_to_one) and f.auto_created
    ]
    for relation in relations:
        related_model = relation.related_model

        # if the relation is between obj and a page, get the page
        if issubclass(related_model, Page):
            pages |= Page.objects.filter(
                id__in=related_model._base_manager.filter(
                    **{relation.field.name: obj.id}
                ).values_list("id", flat=True)
            )
        else:
            # if the relation is between obj and an object that has a page as a
            # property, return the page
            for f in related_model._meta.fields:
                if isinstance(f, ParentalKey) and issubclass(
                    f.remote_field.model, Page
                ):
                    pages |= Page.objects.filter(
                        id__in=related_model._base_manager.filter(
                            **{relation.field.name: obj.id}
                        ).values_list(f.attname, flat=True)
                    )

    return pages


def popular_tags_for_model(model, count=10):
    """Return a queryset of the most frequently used tags used on this model class"""
    content_type = ContentType.objects.get_for_model(model)
    return (
        Tag.objects.filter(taggit_taggeditem_items__content_type=content_type)
        .annotate(item_count=Count("taggit_taggeditem_items"))
        .order_by("-item_count")[:count]
    )
