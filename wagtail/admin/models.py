from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Count
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from modelcluster.fields import ParentalKey
from taggit.models import Tag

# The panels module extends Page with some additional attributes required by
# wagtail admin (namely, base_form_class and get_edit_handler). Importing this within
# wagtail.admin.models ensures that this happens in advance of running wagtail.admin's
# system checks.
from wagtail.admin import panels  # NOQA: F401
from wagtail.models import Page


# A dummy model that exists purely to attach the access_admin permission type to, so that it
# doesn't get identified as a stale content type and removed by the remove_stale_contenttypes
# management command.
class Admin(models.Model):
    class Meta:
        default_permissions = []  # don't create the default add / change / delete / view perms
        permissions = [
            ("access_admin", _("Can access Wagtail admin")),
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


class EditingSession(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="editing_sessions",
    )
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, related_name="+"
    )
    object_id = models.CharField(max_length=255)
    content_object = GenericForeignKey(
        "content_type", "object_id", for_concrete_model=False
    )
    last_seen_at = models.DateTimeField()
    is_editing = models.BooleanField(default=False)

    @staticmethod
    def cleanup():
        EditingSession.objects.filter(
            last_seen_at__lt=timezone.now() - timezone.timedelta(hours=1)
        ).delete()

    class Meta:
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]


class FormStateQuerySet(models.QuerySet):
    def for_instance(self, instance):
        return self.filter(
            content_type=ContentType.objects.get_for_model(
                instance, for_concrete_model=False
            ),
            object_id=str(instance.pk or ""),
        )

    def for_preview(self, user, instance, parent_object_id=""):
        return self.filter(user=user, parent_object_id=parent_object_id).for_instance(
            instance
        )


class FormStateManager(models.Manager.from_queryset(FormStateQuerySet)):
    def update_or_create_by_instance(
        self,
        instance,
        parent_object_id="",
        **kwargs,
    ):
        return super().update_or_create(
            content_type=ContentType.objects.get_for_model(
                instance, for_concrete_model=False
            ),
            object_id=str(instance.pk or ""),
            parent_object_id=parent_object_id,
            **kwargs,
        )


class FormState(models.Model):
    """The form state of a create or edit form for a given user and object."""

    data = models.JSONField(default=dict)
    """The form data as a dictionary that maps form field names to arrays of values."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="wagtail_form_states",
    )
    """The user that the form state belongs to."""
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name="+",
    )
    """The content type of the object being created or edited."""
    object_id = models.CharField(max_length=255)
    """The ID of the object being edited, empty if the object is being created."""
    content_object = GenericForeignKey(
        "content_type",
        "object_id",
        for_concrete_model=False,
    )
    """The object being edited or created."""
    parent_object_id = models.CharField(max_length=255)
    """
    The ID of the parent object, if the object is being created under a parent
    (e.g. for pages). Empty otherwise.
    """
    last_updated_at = models.DateTimeField()
    """The last time the form state was updated."""

    objects = FormStateManager()

    class Meta:
        indexes = [
            models.Index(
                fields=["user", "content_type", "object_id", "parent_object_id"],
                name="formstate_user_object",
            ),
        ]
        ordering = ["-last_updated_at"]
